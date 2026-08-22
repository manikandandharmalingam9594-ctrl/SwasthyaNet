import os, sys, io, json
import numpy as np
import pandas as pd
import joblib

# Ensure UTF-8 output on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "ml_data")
MODEL_DIR = os.path.join(BASE_DIR, "ml_models")

print("=" * 85)
print("PHASE 5E: AI MODEL ARTIFACT & INFERENCE VERIFICATION")
print("=" * 85)

# ==============================================================================
# 1. VERIFY MEDICINE STOCK-OUT CHAMPION MODEL
# ==============================================================================
print("\n" + "-" * 85)
print("1. VERIFYING MEDICINE STOCK-OUT CHAMPION MODEL ARTIFACTS...")
print("-" * 85)

stock_config_path = os.path.join(MODEL_DIR, "stockout_champion_config.json")
stock_cols_path = os.path.join(MODEL_DIR, "stockout_feature_columns.joblib")
stage1_model_path = os.path.join(MODEL_DIR, "stockout_stage1_classifier.joblib")
stage2_model_path = os.path.join(MODEL_DIR, "stockout_stage2_regressor.joblib")

# Step 1: Check artifact existence
assert os.path.exists(stock_config_path), f"Missing config: {stock_config_path}"
assert os.path.exists(stock_cols_path), f"Missing cols: {stock_cols_path}"
assert os.path.exists(stage1_model_path), f"Missing Stage 1 model: {stage1_model_path}"
assert os.path.exists(stage2_model_path), f"Missing Stage 2 model: {stage2_model_path}"

with open(stock_config_path, "r", encoding="utf-8") as f:
    stock_config = json.load(f)

stock_feature_cols = joblib.load(stock_cols_path)
clf_stage1 = joblib.load(stage1_model_path)
reg_stage2 = joblib.load(stage2_model_path)

print(f"Loaded Champion Architecture: {stock_config['champion_model']}")
print(f"Stage 1 Classifier: {type(clf_stage1).__name__} (Classes: {clf_stage1.classes_})")
print(f"Stage 2 Regressor:  {type(reg_stage2).__name__}")
print(f"Feature Space:      {len(stock_feature_cols)} encoded features")

# Step 2: Load one sample from dataset
stock_csv_path = os.path.join(DATA_DIR, "medicine_stockout_dataset.csv")
df_stock = pd.read_csv(stock_csv_path)

# Pick an acute low-stock sample from test period
test_samples = df_stock[df_stock['days_until_stockout'] <= 7.0]
sample_stock = test_samples.iloc[0] if len(test_samples) > 0 else df_stock.iloc[-1]

print(f"\n[Sample Input Details]:")
print(f"  Date:                 {sample_stock['date']}")
print(f"  Facility:             {sample_stock['centre_name']} ({sample_stock['centre_type']})")
print(f"  Medicine:             {sample_stock['medicine_name']} (Category: {sample_stock['medicine_category']})")
print(f"  Current Stock:        {sample_stock['current_stock']} units (Min buffer: {sample_stock['minimum_stock']})")
print(f"  Stock-to-Min Ratio:   {sample_stock['stock_to_min_ratio']}")
print(f"  7-Day Avg Dispense:   {sample_stock['dispensed_qty_7d_avg']} units/day")
print(f"  True Ground Truth:    {sample_stock['days_until_stockout']} days until stockout")

# Step 3: Compute engineered features & one-hot vector for inference
sample_df = pd.DataFrame([sample_stock])
sample_df['burn_rate_7d'] = np.clip(sample_df['current_stock'] / np.maximum(0.1, sample_df['dispensed_qty_7d_avg']), 0.0, 60.0)
sample_df['burn_rate_14d'] = np.clip(sample_df['current_stock'] / np.maximum(0.1, sample_df['dispensed_qty_14d_avg']), 0.0, 60.0)
sample_df['burn_rate_30d'] = np.clip(sample_df['current_stock'] / np.maximum(0.1, sample_df['dispensed_qty_30d_avg']), 0.0, 60.0)
sample_df['is_critical_buffer'] = (sample_df['stock_to_min_ratio'] <= 1.5).astype(int)

cat_cols = ['centre_type', 'district_id', 'medicine_category', 'day_of_week', 'month']
num_cols = [
    'current_stock', 'minimum_stock', 'maximum_stock', 'stock_to_min_ratio',
    'burn_rate_7d', 'burn_rate_14d', 'burn_rate_30d', 'is_critical_buffer',
    'days_since_last_restock', 'last_restock_quantity',
    'dispensed_qty_7d_avg', 'dispensed_qty_14d_avg', 'dispensed_qty_30d_avg',
    'dispensed_qty_7d_std', 'consumption_trend_7_30',
    'is_weekend', 'is_monsoon'
]

# Vectorize according to exact training columns
X_raw_encoded = pd.get_dummies(sample_df[cat_cols + num_cols], columns=cat_cols)
X_vector = pd.DataFrame(0, index=[0], columns=stock_feature_cols)
for c in X_raw_encoded.columns:
    if c in X_vector.columns:
        X_vector[c] = X_raw_encoded[c].values[0]

# Step 4: Run Two-Stage Inference
risk_prob = clf_stage1.predict_proba(X_vector.values)[0, 1]
reg_val = np.clip(reg_stage2.predict(X_vector.values)[0], 0.0, 59.0)
burn_rate_val = sample_df['burn_rate_7d'].values[0]

if risk_prob >= 0.50:
    pred_days = min(reg_val, burn_rate_val)
    risk_level = "CRITICAL / HIGH RISK"
else:
    pred_days = 60.0
    risk_level = "SAFE / BUFFERED"

print(f"\n[Champion Model Inference Output]:")
print(f"  Stage 1 Risk Probability:  {risk_prob * 100:.1f}% -> Classification: {risk_level}")
print(f"  Stage 2 Raw Regression:    {reg_val:.2f} days")
print(f"  Physical Burn Constraint:  {burn_rate_val:.2f} days")
print(f"  Final Predicted Value:     {pred_days:.2f} days (Error: {abs(pred_days - sample_stock['days_until_stockout']):.2f} days)")
print("  => Stock-Out Champion Model Inference: PASS")


# ==============================================================================
# 2. VERIFY BED OCCUPANCY MULTI-HORIZON FORECASTING MODELS (t+1, t+7, t+14)
# ==============================================================================
print("\n" + "-" * 85)
print("2. VERIFYING BED OCCUPANCY FORECASTING MODEL ARTIFACTS...")
print("-" * 85)

bed_config_path = os.path.join(MODEL_DIR, "bed_occ_champion_config.json")
bed_cols_path = os.path.join(MODEL_DIR, "bed_occ_feature_columns.joblib")

assert os.path.exists(bed_config_path), f"Missing config: {bed_config_path}"
assert os.path.exists(bed_cols_path), f"Missing cols: {bed_cols_path}"

with open(bed_config_path, "r", encoding="utf-8") as f:
    bed_config = json.load(f)

bed_feature_cols = joblib.load(bed_cols_path)

# Load Models for t+1, t+7, t+14
models_bed = {}
for h in ['t+1', 't+7', 't+14']:
    m_path = os.path.join(MODEL_DIR, bed_config[h]['model_file'])
    assert os.path.exists(m_path), f"Missing model for {h}: {m_path}"
    models_bed[h] = joblib.load(m_path)
    print(f"Loaded {h} Model: {bed_config[h]['model_file']} ({type(models_bed[h]).__name__})")

# Load one sample from bed occupancy dataset
bed_csv_path = os.path.join(DATA_DIR, "bed_occupancy_dataset.csv")
df_bed = pd.read_csv(bed_csv_path)

# Pick an interesting CHC ward sample from the test period
chc_samples = df_bed[df_bed['centre_type'] == 'CHC']
sample_bed = chc_samples.iloc[-20] if len(chc_samples) > 20 else df_bed.iloc[-1]

print(f"\n[Sample Input Details]:")
print(f"  Date:                   {sample_bed['date']}")
print(f"  Facility:               {sample_bed['centre_name']} ({sample_bed['centre_type']})")
print(f"  Ward:                   {sample_bed['ward_name']} Ward (Total Capacity: {sample_bed['total_beds']} beds)")
print(f"  Current Occupied:       {sample_bed['current_occupied_beds']} beds ({sample_bed['current_occupancy_rate']*100:.1f}% occupancy)")
print(f"  Past 7-Day Mean:        {sample_bed['occupied_7d_mean']} beds (Std: {sample_bed['occupied_7d_std']})")
print(f"  7-Day Prior Lag (t-7):  {sample_bed['occupied_lag_7d']} beds")

# Vectorize for inference
sample_bed_df = pd.DataFrame([sample_bed])
cat_cols_bed = ['ward_name', 'centre_type', 'district_id', 'day_of_week', 'day_of_month', 'month']
num_cols_bed = [
    'total_beds', 'current_occupied_beds', 'current_available_beds', 'current_occupancy_rate',
    'occupied_lag_1d', 'occupied_lag_2d', 'occupied_lag_7d', 'occupied_lag_14d',
    'occupied_7d_mean', 'occupied_14d_mean', 'occupied_7d_std',
    'is_weekend', 'is_monsoon'
]

X_bed_raw = pd.get_dummies(sample_bed_df[cat_cols_bed + num_cols_bed], columns=cat_cols_bed)
X_bed_vec = pd.DataFrame(0, index=[0], columns=bed_feature_cols)
for c in X_bed_raw.columns:
    if c in X_bed_vec.columns:
        X_bed_vec[c] = X_bed_raw[c].values[0]

print(f"\n[Multi-Horizon Forecast Predictions]:")
for h in ['t+1', 't+7', 't+14']:
    target_col = bed_config[h]['target_col']
    ground_truth = sample_bed[target_col]
    
    pred_occ = int(np.round(np.clip(models_bed[h].predict(X_bed_vec.values)[0], 0, sample_bed['total_beds'] + 2)))
    pred_rate = round(pred_occ / sample_bed['total_beds'] * 100.0, 1)
    
    print(f"  Forecast Horizon {h:<4} ({target_col}):")
    print(f"    - Ground Truth:  {ground_truth} beds ({ground_truth / sample_bed['total_beds'] * 100:.1f}%)")
    print(f"    - Predicted Occ: {pred_occ} beds ({pred_rate}% occupancy rate)")
    print(f"    - Absolute Diff: {abs(pred_occ - ground_truth)} beds")

print("\n  => Bed Occupancy Multi-Horizon Models Inference: PASS")

print("\n" + "=" * 85)
print("ALL PHASE 5E AI MODEL ARTIFACTS LOADED AND PREDICTED WITH 100% SUCCESS!")
print("=" * 85)
