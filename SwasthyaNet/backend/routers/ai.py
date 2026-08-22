import os, json
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import numpy as np
import pandas as pd
import joblib

from database import get_db
import models
from dependencies import get_current_user, verify_centre_access

router = APIRouter(prefix="/ai", tags=["AI Predictions & Forecasting"])

MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "ml_models")

# -----------------------------------------------------------------------------
# MODEL ARTIFACT CACHE (Lazy loaded on first call or module load)
# -----------------------------------------------------------------------------
_MODELS_CACHE = {}

def get_ml_models():
    """Load and cache champion models and feature configurations."""
    if not _MODELS_CACHE:
        # Stock-out artifacts
        stock_cols = joblib.load(os.path.join(MODEL_DIR, "stockout_feature_columns.joblib"))
        clf_stage1 = joblib.load(os.path.join(MODEL_DIR, "stockout_stage1_classifier.joblib"))
        reg_stage2 = joblib.load(os.path.join(MODEL_DIR, "stockout_stage2_regressor.joblib"))
        
        # Bed occupancy artifacts
        bed_cols = joblib.load(os.path.join(MODEL_DIR, "bed_occ_feature_columns.joblib"))
        bed_t1 = joblib.load(os.path.join(MODEL_DIR, "bed_occ_t+1_champion_lgb.joblib"))
        bed_t7 = joblib.load(os.path.join(MODEL_DIR, "bed_occ_t+7_champion_lgb.joblib"))
        bed_t14 = joblib.load(os.path.join(MODEL_DIR, "bed_occ_t+14_champion_lgb.joblib"))
        
        _MODELS_CACHE['stock_cols'] = stock_cols
        _MODELS_CACHE['clf_stage1'] = clf_stage1
        _MODELS_CACHE['reg_stage2'] = reg_stage2
        _MODELS_CACHE['bed_cols'] = bed_cols
        _MODELS_CACHE['bed_t1'] = bed_t1
        _MODELS_CACHE['bed_t7'] = bed_t7
        _MODELS_CACHE['bed_t14'] = bed_t14
        
    return _MODELS_CACHE


# -----------------------------------------------------------------------------
# 1. GET /api/ai/stockout/{centre_id}/{medicine_id}
# -----------------------------------------------------------------------------
@router.get("/stockout/{centre_id}/{medicine_id}")
def get_medicine_stockout_prediction(
    centre_id: int,
    medicine_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """
    Predict days until medicine stock reaches zero using the Two-Stage Champion Model.
    Enforces RBAC: PHC/CHC staff own centre only, District Admin district only, Super Admin global.
    """
    # 1. RBAC Verification
    verify_centre_access(centre_id, user, db)
    
    # 2. Query Entity Data
    centre = db.query(models.HealthCentre).filter(models.HealthCentre.centre_id == centre_id).first()
    if not centre:
        raise HTTPException(status_code=404, detail="Health centre not found")
        
    medicine = db.query(models.Medicine).filter(models.Medicine.medicine_id == medicine_id).first()
    if not medicine:
        raise HTTPException(status_code=404, detail="Medicine not found")
        
    inv = db.query(models.MedicineInventory).filter(
        models.MedicineInventory.centre_id == centre_id,
        models.MedicineInventory.medicine_id == medicine_id
    ).first()
    
    current_stock = inv.current_stock if inv else 0
    minimum_stock = inv.minimum_stock if inv and inv.minimum_stock else 10
    maximum_stock = inv.maximum_stock if inv and inv.maximum_stock else minimum_stock * 6
    
    # 3. Query Recent Historical Outflow / Inflow for Feature Computation
    history_records = db.query(models.MedicineStockHistory).filter(
        models.MedicineStockHistory.centre_id == centre_id,
        models.MedicineStockHistory.medicine_id == medicine_id
    ).order_by(models.MedicineStockHistory.recorded_at.desc()).limit(60).all()
    
    # Dispensed history
    dispensed_quantities = [
        h.quantity for h in history_records if h.transaction_type in ['DISPENSED', 'OUT']
    ]
    
    # Default consumption baseline if no transactions logged yet
    default_base = 35.0 if centre.centre_type == 'CHC' else 12.0
    
    avg_7d = float(np.mean(dispensed_quantities[:7])) if len(dispensed_quantities) >= 1 else default_base
    avg_14d = float(np.mean(dispensed_quantities[:14])) if len(dispensed_quantities) >= 1 else default_base
    avg_30d = float(np.mean(dispensed_quantities[:30])) if len(dispensed_quantities) >= 1 else default_base
    std_7d = float(np.std(dispensed_quantities[:7])) if len(dispensed_quantities) > 1 else 1.5
    
    # Days since last restock
    restock_records = [
        h for h in history_records if h.transaction_type in ['RECEIVED', 'IN', 'TRANSFER_IN']
    ]
    now = datetime.now(timezone.utc)
    if restock_records and restock_records[0].recorded_at:
        # Normalize timezone
        rec_time = restock_records[0].recorded_at
        if rec_time.tzinfo is None:
            rec_time = rec_time.replace(tzinfo=timezone.utc)
        days_since_last_restock = max(0, (now - rec_time).days)
        last_restock_qty = restock_records[0].quantity
    else:
        days_since_last_restock = 5
        last_restock_qty = minimum_stock * 3
        
    burn_rate_7d = float(np.clip(current_stock / max(0.1, avg_7d), 0.0, 60.0))
    burn_rate_14d = float(np.clip(current_stock / max(0.1, avg_14d), 0.0, 60.0))
    burn_rate_30d = float(np.clip(current_stock / max(0.1, avg_30d), 0.0, 60.0))
    
    stock_to_min_ratio = float(current_stock / max(1.0, minimum_stock))
    is_critical_buffer = 1 if stock_to_min_ratio <= 1.5 else 0
    trend_7_30 = float(avg_7d / (avg_30d + 1e-4))
    
    dow = now.weekday()
    month = now.month
    is_weekend = 1 if dow in [5, 6] else 0
    is_monsoon = 1 if month in [6, 7, 8, 9, 10, 11] else 0
    
    # 4. Assemble One-Hot Feature Vector
    models_dict = get_ml_models()
    feature_cols = models_dict['stock_cols']
    
    raw_dict = {
        'centre_type': centre.centre_type,
        'district_id': centre.district_id,
        'medicine_category': medicine.category,
        'day_of_week': dow,
        'month': month,
        'current_stock': current_stock,
        'minimum_stock': minimum_stock,
        'maximum_stock': maximum_stock,
        'stock_to_min_ratio': stock_to_min_ratio,
        'burn_rate_7d': burn_rate_7d,
        'burn_rate_14d': burn_rate_14d,
        'burn_rate_30d': burn_rate_30d,
        'is_critical_buffer': is_critical_buffer,
        'days_since_last_restock': days_since_last_restock,
        'last_restock_quantity': last_restock_qty,
        'dispensed_qty_7d_avg': avg_7d,
        'dispensed_qty_14d_avg': avg_14d,
        'dispensed_qty_30d_avg': avg_30d,
        'dispensed_qty_7d_std': std_7d,
        'consumption_trend_7_30': trend_7_30,
        'is_weekend': is_weekend,
        'is_monsoon': is_monsoon
    }
    
    df_raw = pd.DataFrame([raw_dict])
    cat_cols = ['centre_type', 'district_id', 'medicine_category', 'day_of_week', 'month']
    df_encoded = pd.get_dummies(df_raw, columns=cat_cols)
    
    vec = pd.DataFrame(0, index=[0], columns=feature_cols)
    for c in df_encoded.columns:
        if c in vec.columns:
            vec[c] = df_encoded[c].values[0]
            
    # 5. Execute Two-Stage Model Inference
    clf_stage1 = models_dict['clf_stage1']
    reg_stage2 = models_dict['reg_stage2']
    
    risk_prob = float(clf_stage1.predict_proba(vec.values)[0, 1])
    reg_days = float(np.clip(reg_stage2.predict(vec.values)[0], 0.0, 59.0))
    
    if current_stock == 0:
        predicted_days = 0.0
        risk_level = "STOCK_OUT"
    elif risk_prob >= 0.50:
        predicted_days = float(np.round(min(reg_days, burn_rate_7d), 1))
        if predicted_days <= 7.0:
            risk_level = "CRITICAL"
        elif predicted_days <= 14.0:
            risk_level = "HIGH"
        else:
            risk_level = "MEDIUM"
    else:
        predicted_days = 60.0
        risk_level = "LOW"
        
    return {
        "centre_id": centre.centre_id,
        "centre_name": centre.centre_name,
        "centre_type": centre.centre_type,
        "district_id": centre.district_id,
        "medicine_id": medicine.medicine_id,
        "medicine_name": medicine.medicine_name,
        "medicine_category": medicine.category,
        "current_stock": current_stock,
        "minimum_stock": minimum_stock,
        "maximum_stock": maximum_stock,
        "stock_to_min_ratio": round(stock_to_min_ratio, 2),
        "predicted_days_until_stockout": predicted_days,
        "risk_level": risk_level,
        "risk_probability": round(risk_prob, 3),
        "estimated_daily_consumption": round(avg_7d, 1),
        "forecast_timestamp": now.isoformat()
    }


# -----------------------------------------------------------------------------
# 2. GET /api/ai/bed-forecast/{centre_id}/{ward_id}
# -----------------------------------------------------------------------------
@router.get("/bed-forecast/{centre_id}/{ward_id}")
def get_bed_occupancy_forecast(
    centre_id: int,
    ward_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """
    Predict ward bed occupancy for t+1, t+7, and t+14 horizons using Multi-Horizon LightGBM models.
    Enforces RBAC: PHC/CHC staff own centre only, District Admin district only, Super Admin global.
    """
    # 1. RBAC Verification
    verify_centre_access(centre_id, user, db)
    
    # 2. Query Entity Data
    centre = db.query(models.HealthCentre).filter(models.HealthCentre.centre_id == centre_id).first()
    if not centre:
        raise HTTPException(status_code=404, detail="Health centre not found")
        
    ward = db.query(models.Ward).filter(models.Ward.ward_id == ward_id).first()
    if not ward or ward.centre_id != centre_id:
        raise HTTPException(status_code=404, detail="Ward not found in this health centre")
        
    total_beds = ward.total_beds
    
    # 3. Query Recent Bed Occupancy History
    recent_occ = db.query(models.BedOccupancy).filter(
        models.BedOccupancy.ward_id == ward_id
    ).order_by(models.BedOccupancy.recorded_at.desc(), models.BedOccupancy.occupancy_id.desc()).limit(30).all()
    
    is_emergency = ward.ward_name.strip().lower() == "emergency"
    if recent_occ:
        current_occupied = recent_occ[0].occupied_beds
        if not is_emergency:
            current_occupied = min(current_occupied, total_beds)
        occ_history = [min(o.occupied_beds, total_beds) if not is_emergency else o.occupied_beds for o in recent_occ]
    else:
        # Fallback default occupancy rate if no history exists yet
        rate_def = 0.70 if centre.centre_type == 'CHC' else 0.45
        current_occupied = int(total_beds * rate_def)
        occ_history = [current_occupied]
        
    current_available = max(0, total_beds - current_occupied)
    current_rate = round((current_occupied / total_beds) * 100.0, 1) if total_beds > 0 else 0.0
    
    # Compute Lags & Rolling Means
    lag_1d = occ_history[1] if len(occ_history) > 1 else current_occupied
    lag_2d = occ_history[2] if len(occ_history) > 2 else current_occupied
    lag_7d = occ_history[7] if len(occ_history) > 7 else current_occupied
    lag_14d = occ_history[14] if len(occ_history) > 14 else current_occupied
    
    past_7 = occ_history[:7]
    past_14 = occ_history[:14]
    mean_7d = float(np.mean(past_7)) if past_7 else float(current_occupied)
    mean_14d = float(np.mean(past_14)) if past_14 else float(current_occupied)
    std_7d = float(np.std(past_7)) if len(past_7) > 1 else 0.5
    
    now = datetime.now(timezone.utc)
    dow = now.weekday()
    day_of_month = now.day
    month = now.month
    is_weekend = 1 if dow in [5, 6] else 0
    is_monsoon = 1 if month in [6, 7, 8, 9, 10, 11] else 0
    
    # 4. Assemble Vector
    models_dict = get_ml_models()
    bed_feature_cols = models_dict['bed_cols']
    
    raw_dict = {
        'ward_name': ward.ward_name,
        'centre_type': centre.centre_type,
        'district_id': centre.district_id,
        'day_of_week': dow,
        'day_of_month': day_of_month,
        'month': month,
        'total_beds': total_beds,
        'current_occupied_beds': current_occupied,
        'current_available_beds': current_available,
        'current_occupancy_rate': current_rate / 100.0,
        'occupied_lag_1d': lag_1d,
        'occupied_lag_2d': lag_2d,
        'occupied_lag_7d': lag_7d,
        'occupied_lag_14d': lag_14d,
        'occupied_7d_mean': mean_7d,
        'occupied_14d_mean': mean_14d,
        'occupied_7d_std': std_7d,
        'is_weekend': is_weekend,
        'is_monsoon': is_monsoon
    }
    
    df_raw = pd.DataFrame([raw_dict])
    cat_cols_bed = ['ward_name', 'centre_type', 'district_id', 'day_of_week', 'day_of_month', 'month']
    df_encoded = pd.get_dummies(df_raw, columns=cat_cols_bed)
    
    vec = pd.DataFrame(0, index=[0], columns=bed_feature_cols)
    for c in df_encoded.columns:
        if c in vec.columns:
            vec[c] = df_encoded[c].values[0]
            
    # 5. Run Inference across t+1, t+7, t+14
    max_cap = total_beds + (2 if ward.ward_name == 'Emergency' else 0)
    
    pred_t1 = int(np.round(np.clip(models_dict['bed_t1'].predict(vec.values)[0], 0, max_cap)))
    pred_t7 = int(np.round(np.clip(models_dict['bed_t7'].predict(vec.values)[0], 0, max_cap)))
    pred_t14 = int(np.round(np.clip(models_dict['bed_t14'].predict(vec.values)[0], 0, max_cap)))
    
    return {
        "centre_id": centre.centre_id,
        "centre_name": centre.centre_name,
        "centre_type": centre.centre_type,
        "district_id": centre.district_id,
        "ward_id": ward.ward_id,
        "ward_name": ward.ward_name,
        "total_beds": total_beds,
        "current_occupied_beds": current_occupied,
        "current_available_beds": current_available,
        "current_occupancy_rate_pct": current_rate,
        "forecasts": {
            "t_plus_1": {
                "horizon_days": 1,
                "target_date": (now + timedelta(days=1)).strftime("%Y-%m-%d"),
                "predicted_occupied_beds": pred_t1,
                "predicted_available_beds": max(0, total_beds - pred_t1),
                "predicted_occupancy_rate_pct": round((pred_t1 / total_beds) * 100.0, 1),
                "status": "SURGE_RISK" if pred_t1 >= total_beds * 0.9 else "NORMAL"
            },
            "t_plus_7": {
                "horizon_days": 7,
                "target_date": (now + timedelta(days=7)).strftime("%Y-%m-%d"),
                "predicted_occupied_beds": pred_t7,
                "predicted_available_beds": max(0, total_beds - pred_t7),
                "predicted_occupancy_rate_pct": round((pred_t7 / total_beds) * 100.0, 1),
                "status": "SURGE_RISK" if pred_t7 >= total_beds * 0.9 else "NORMAL"
            },
            "t_plus_14": {
                "horizon_days": 14,
                "target_date": (now + timedelta(days=14)).strftime("%Y-%m-%d"),
                "predicted_occupied_beds": pred_t14,
                "predicted_available_beds": max(0, total_beds - pred_t14),
                "predicted_occupancy_rate_pct": round((pred_t14 / total_beds) * 100.0, 1),
                "status": "SURGE_RISK" if pred_t14 >= total_beds * 0.9 else "NORMAL"
            }
        },
        "forecast_timestamp": now.isoformat()
    }
