import os
import re
import json
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import httpx

from database import get_db
import models
import schemas
from dependencies import get_current_user, verify_centre_access, verify_district_access
from routers.ai import get_medicine_stockout_prediction, get_bed_occupancy_forecast

router = APIRouter(prefix="/chatbot", tags=["chatbot"])

# -----------------------------------------------------------------------------
# Intent Definitions
# -----------------------------------------------------------------------------
INTENT_INVENTORY = "INVENTORY"
INTENT_STOCKOUT = "STOCKOUT"
INTENT_BED_STATUS = "BED_STATUS"
INTENT_BED_FORECAST = "BED_FORECAST"
INTENT_ALERTS = "ALERTS"
INTENT_NAVIGATION = "NAVIGATION"
INTENT_UNKNOWN = "UNKNOWN"


# -----------------------------------------------------------------------------
# Entity Extraction Helpers
# -----------------------------------------------------------------------------
def find_mentioned_medicine(text: str, db: Session) -> Optional[models.Medicine]:
    """Find medicine mentioned in user message."""
    all_meds = db.query(models.Medicine).all()
    text_lower = text.lower()
    
    # Direct name match
    for med in all_meds:
        med_name = med.medicine_name.lower()
        if med_name in text_lower or (len(med_name) > 3 and re.search(r'\b' + re.escape(med_name) + r'\b', text_lower)):
            return med
            
    # Common medicine nicknames / partials
    aliases = {
        "paracetamol": ["dolo", "crocin", "calpol", "pcm", "fever tablet"],
        "amoxicillin": ["mox", "novamox", "amox"],
        "azithromycin": ["zithro", "azithral"],
        "ibuprofen": ["brufen"],
        "ors": ["oral rehydration", "electral", "hydration salt"],
        "zinc": ["zinc tablet"],
        "cetirizine": ["cetzine", "allergy tablet"],
        "metformin": ["glycomet", "sugar tablet"],
        "salbutamol": ["asthalin", "inhaler"]
    }
    for generic, alt_list in aliases.items():
        for alt in alt_list:
            if alt in text_lower:
                for med in all_meds:
                    if generic in med.medicine_name.lower():
                        return med
                        
    return None


def find_mentioned_ward(text: str, centre_id: int, db: Session) -> Optional[models.Ward]:
    """Find ward mentioned in user message within a centre."""
    wards = db.query(models.Ward).filter(models.Ward.centre_id == centre_id).all()
    text_lower = text.lower()
    
    for ward in wards:
        w_name = ward.ward_name.lower()
        if w_name in text_lower:
            return ward
            
    # Fallback to keyword matching
    keywords = ["emergency", "general", "maternity", "pediatric", "icu", "male", "female"]
    for kw in keywords:
        if kw in text_lower:
            for ward in wards:
                if kw in ward.ward_name.lower():
                    return ward
                    
    return None


def find_mentioned_centre(text: str, db: Session, district_id: Optional[int] = None) -> Optional[models.HealthCentre]:
    """Find health centre mentioned by name or ID in user query."""
    query = db.query(models.HealthCentre)
    if district_id:
        query = query.filter(models.HealthCentre.district_id == district_id)
    centres = query.all()
    
    text_lower = text.lower()
    for c in centres:
        c_name = c.centre_name.lower()
        # Check centre name substring
        if c_name in text_lower or c_name.replace("phc", "").replace("chc", "").strip() in text_lower:
            return c
            
    # Check ID mentions like "centre 1", "centre #2"
    id_match = re.search(r'\bcentre\s*#?\s*(\d+)\b', text_lower)
    if id_match:
        c_id = int(id_match.group(1))
        for c in centres:
            if c.centre_id == c_id:
                return c
                
    return None


# -----------------------------------------------------------------------------
# Role-Aware Navigation Resolver
# -----------------------------------------------------------------------------
def detect_navigation_action(
    text: str,
    user_role: str,
    user_centre_id: Optional[int],
    user_district_id: Optional[int],
    db: Session
) -> Optional[schemas.NavigationAction]:
    """
    Detect if the user is asking to navigate / open a page or section,
    and validate if the destination is authorized for the user's role.
    """
    text_lower = text.lower()

    # Navigation trigger keywords
    nav_triggers = [
        r'\b(?:open|go\s+to|navigate\s+to|show\s+page|take\s+me\s+to|switch\s+to|view\s+page|launch|head\s+to)\b',
        r'\b(?:and\s+open|and\s+show|and\s+navigate|and\s+go\s+to)\b',
        r'\b(?:show\s+me\s+the|bring\s+up)\b'
    ]

    is_nav_command = any(re.search(t, text_lower) for t in nav_triggers)
    # Also handle standalone direct destinations like "open inventory", "show bed occupancy"
    if not is_nav_command and not re.search(r'\b(?:open|show|go)\s+(?:inventory|beds?|alerts?|users?|staff|dashboard)\b', text_lower):
        return None

    # 1. Super Admin Dashboard
    if re.search(r'\bsuper\s*admin\s*(?:dashboard|page|view)?\b', text_lower):
        if user_role == "SUPER_ADMIN":
            return schemas.NavigationAction(
                destination="SUPER_ADMIN_DASHBOARD",
                action="OPEN_PAGE",
                params={"tab": "overview"},
                authorized=True
            )
        return schemas.NavigationAction(
            destination="SUPER_ADMIN_DASHBOARD",
            action="OPEN_PAGE",
            authorized=False,
            reason="Only Super Administrators are authorized to access the Super Admin Dashboard."
        )

    # 2. District Admin Dashboard
    if re.search(r'\bdistrict\s*(?:admin\s*)?(?:dashboard|page|view)\b', text_lower):
        if user_role in ["SUPER_ADMIN", "DISTRICT_ADMIN"]:
            return schemas.NavigationAction(
                destination="DISTRICT_ADMIN_DASHBOARD",
                action="OPEN_PAGE",
                params={"tab": "overview", "district_id": user_district_id},
                authorized=True
            )
        return schemas.NavigationAction(
            destination="DISTRICT_ADMIN_DASHBOARD",
            action="OPEN_PAGE",
            authorized=False,
            reason="Only District Administrators and Super Administrators are authorized to access the District Admin Dashboard."
        )

    # 3. User / Staff Management
    if re.search(r'\b(?:user\s*management|staff\s*management|manage\s*users?|manage\s*staff|user\s*accounts?|users?\s*page|users?\s*tab)\b', text_lower):
        if user_role == "SUPER_ADMIN":
            return schemas.NavigationAction(
                destination="USER_MANAGEMENT",
                action="OPEN_PAGE",
                params={"tab": "users"},
                authorized=True
            )
        elif user_role == "DISTRICT_ADMIN":
            return schemas.NavigationAction(
                destination="USER_MANAGEMENT",
                action="OPEN_PAGE",
                params={"tab": "staff", "district_id": user_district_id},
                authorized=True
            )
        return schemas.NavigationAction(
            destination="USER_MANAGEMENT",
            action="OPEN_PAGE",
            authorized=False,
            reason="Healthcare staff accounts do not have permission to access User Management."
        )

    # 4. AI Insights & Forecasting Section / Tab
    if re.search(r'\b(?:ai\s*insights?|ai\s*predictions?|predictive\s*forecasts?|insights?\s*tab|forecasts?\s*tab|ai\s*section)\b', text_lower):
        tab_name = "ai_insights"
        return schemas.NavigationAction(
            destination="AI_INSIGHTS",
            action="OPEN_PAGE",
            params={"tab": tab_name, "centre_id": user_centre_id},
            authorized=True
        )

    # 5. Inventory Page / Section
    if re.search(r'\b(?:inventory|medicine\s*inventory|stock\s*management|stock\s*page|inventory\s*section|manage\s*inventory)\b', text_lower):
        return schemas.NavigationAction(
            destination="INVENTORY",
            action="OPEN_PAGE",
            params={"section_id": "inventory-section", "centre_id": user_centre_id},
            authorized=True
        )

    # 6. Beds / Bed Occupancy Section
    if re.search(r'\b(?:bed\s*occupancy|beds?\s*page|beds?\s*section|manage\s*beds?|bed\s*status\s*page|ward\s*beds?)\b', text_lower):
        return schemas.NavigationAction(
            destination="BED_STATUS",
            action="OPEN_PAGE",
            params={"section_id": "beds-section", "centre_id": user_centre_id},
            authorized=True
        )

    # 7. Bed Forecast
    if re.search(r'\b(?:bed\s*forecast|surge\s*forecast|forecast\s*beds?\s*page)\b', text_lower):
        return schemas.NavigationAction(
            destination="BED_FORECAST",
            action="OPEN_PAGE",
            params={"section_id": "bed-forecast-section", "centre_id": user_centre_id},
            authorized=True
        )

    # 8. Doctor Attendance
    if re.search(r'\b(?:attendance|doctor\s*attendance|mark\s*attendance|staff\s*attendance)\b', text_lower):
        return schemas.NavigationAction(
            destination="ATTENDANCE",
            action="OPEN_PAGE",
            params={"section_id": "attendance-section", "centre_id": user_centre_id},
            authorized=True
        )

    # 9. Alerts
    if re.search(r'\b(?:alerts?\s*page|active\s*alerts|emergency\s*alerts?\s*page|alerts?\s*section)\b', text_lower):
        return schemas.NavigationAction(
            destination="ALERTS",
            action="OPEN_PAGE",
            params={"centre_id": user_centre_id},
            authorized=True
        )

    # 10. PHC / CHC Dashboard or Generic Dashboard
    if re.search(r'\b(?:phc\s*dashboard|phc\s*page)\b', text_lower):
        return schemas.NavigationAction(
            destination="PHC_DASHBOARD",
            action="OPEN_PAGE",
            params={"centre_id": user_centre_id},
            authorized=True
        )

    if re.search(r'\b(?:chc\s*dashboard|chc\s*page)\b', text_lower):
        return schemas.NavigationAction(
            destination="CHC_DASHBOARD",
            action="OPEN_PAGE",
            params={"centre_id": user_centre_id},
            authorized=True
        )

    if re.search(r'\b(?:dashboard|home|overview|main\s*page)\b', text_lower):
        dest = (
            "SUPER_ADMIN_DASHBOARD" if user_role == "SUPER_ADMIN"
            else "DISTRICT_ADMIN_DASHBOARD" if user_role == "DISTRICT_ADMIN"
            else "PHC_DASHBOARD" if user_role == "PHC_STAFF"
            else "CHC_DASHBOARD"
        )
        return schemas.NavigationAction(
            destination=dest,
            action="OPEN_PAGE",
            params={"centre_id": user_centre_id},
            authorized=True
        )

    return None


# -----------------------------------------------------------------------------
# Intent Classification Engine
# -----------------------------------------------------------------------------
def classify_intent(text: str) -> str:
    """
    Classify intent using rule-based heuristics & keyword patterns.
    Recognizes: INVENTORY, STOCKOUT, BED_STATUS, BED_FORECAST, ALERTS, NAVIGATION, UNKNOWN.
    """
    text_lower = text.lower()
    
    # 1. STOCKOUT (Predictive medicine stock depletion)
    stockout_patterns = [
        r'\bstock[\s-]?out\b',
        r'\bruns?\s+out\b',
        r'\bwhen\s+will.*run\s+out\b',
        r'\bdays\s+(?:remaining|left|until\s+empty|to\s+deplete)\b',
        r'\bdeplet(?:ion|ed|ing)\b',
        r'\bburn\s*rate\b',
        r'\bstock\s+prediction\b',
        r'\bpredict.*stock\b',
        r'\bforecast.*medicine\b',
        r'\bexhaust(?:ion|ed)\b',
        r'\bcritical\s+stock\s+risk\b',
        r'\bmedicines?\s+(?:are\s+)?at\s+risk\b'
    ]
    if any(re.search(p, text_lower) for p in stockout_patterns):
        return INTENT_STOCKOUT

    # 2. BED_FORECAST (Predictive multi-horizon bed occupancy)
    bed_forecast_patterns = [
        r'\bbed\s+forecast\b',
        r'\bforecast.*bed\b',
        r'\bpredict.*bed\b',
        r'\bbed.*prediction\b',
        r'\bt\+1\b|\bt\+7\b|\bt\+14\b',
        r'\bfuture\s+occupancy\b',
        r'\bupcoming\s+occupancy\b',
        r'\bsurge\s+risk\b',
        r'\bnext\s+(?:week|month|day|7\s*days|14\s*days).*bed\b',
        r'\boccupancy\s+forecast\b',
        r'\bbed.*next\s+(?:few\s+days|week)\b'
    ]
    if any(re.search(p, text_lower) for p in bed_forecast_patterns):
        return INTENT_BED_FORECAST

    # 3. Pure Navigation triggers (when not a clinical Q&A query)
    pure_nav_patterns = [
        r'^(?:open|go\s+to|navigate\s+to|take\s+me\s+to|show\s+page|switch\s+to|view)\s+(?:super\s*admin\s*dashboard|district\s*admin\s*dashboard|user\s*management|staff\s*management|inventory|bed\s*occupancy|beds|alerts|dashboard|home|attendance)',
        r'\b(?:go\s+to|open)\s+(?:user\s*management|staff\s*management|super\s*admin|district\s*admin)\b'
    ]
    if any(re.search(p, text_lower) for p in pure_nav_patterns):
        return INTENT_NAVIGATION

    # 4. BED_STATUS (Current bed occupancy & ward capacity)
    bed_status_patterns = [
        r'\bbed\s+status\b',
        r'\bhow\s+many\s+beds\b',
        r'\bavailable\s+beds?\b',
        r'\boccupied\s+beds?\b',
        r'\bbed\s+occupancy\b',
        r'\bward\s+occupancy\b',
        r'\bward\s+status\b',
        r'\btotal\s+beds?\b',
        r'\bcurrent\s+beds?\b',
        r'\bshow\s+bed\s+occupancy\b',
        r'\bbeds?\b'
    ]
    if any(re.search(p, text_lower) for p in bed_status_patterns):
        return INTENT_BED_STATUS

    # 5. ALERTS (Active emergency & clinical alerts)
    alert_patterns = [
        r'\balerts?\b',
        r'\bwarnings?\b',
        r'\bemergenc(?:y|ies)\b',
        r'\bcritical\s+alert\b',
        r'\bactive\s+issues\b',
        r'\bnotifications?\b',
        r'\boutbreaks?\b',
        r'\bepidemic\b'
    ]
    if any(re.search(p, text_lower) for p in alert_patterns):
        return INTENT_ALERTS

    # 6. INVENTORY (Current medicine stock & levels)
    inventory_patterns = [
        r'\binventory\b',
        r'\bmedicine\s+stock\b',
        r'\bcurrent\s+stock\b',
        r'\bhow\s+much.*stock\b',
        r'\bhow\s+many.*tablets?\b',
        r'\bquantity\b',
        r'\bmedicines?\s+(?:available|left|count)\b',
        r'\blow\s+stock\b',
        r'\bmedications?\b',
        r'\bdrugs?\b',
        r'\bstock\s+level\b'
    ]
    if any(re.search(p, text_lower) for p in inventory_patterns):
        return INTENT_INVENTORY

    return INTENT_UNKNOWN


# -----------------------------------------------------------------------------
# Natural Language Explanation Synthesis Layer
# -----------------------------------------------------------------------------
def synthesize_explanation(
    intent: str, 
    data: Optional[Dict[str, Any]], 
    user_msg: str, 
    scope: Dict[str, Any],
    nav_action: Optional[schemas.NavigationAction] = None
) -> str:
    """
    Synthesize high-quality natural language explanation of trusted backend data
    and navigation actions.
    """
    # 1. Navigation Intent Synthesis
    if intent == INTENT_NAVIGATION and nav_action:
        if not nav_action.authorized:
            return (
                f"🚫 **Access Restricted: Unauthorized Navigation**\n\n"
                f"{nav_action.reason or 'Your current user role does not have permission to access this page.'}\n\n"
                f"_Role-Based Access Control (RBAC) is strictly enforced._"
            )
        
        dest_display = nav_action.destination.replace('_', ' ').title()
        return (
            f"🚀 **Navigating to {dest_display}...**\n\n"
            f"Switching your view to the requested **{dest_display}** section. "
            f"You can also click the navigation button below if you ever need to return here."
        )

    # 2. Local High-Precision Deterministic Synthesizer for Clinical Q&A
    nav_suffix = ""
    if nav_action and nav_action.authorized:
        nav_suffix = f"\n\n🚀 *Navigating you to the **{nav_action.destination.replace('_', ' ').title()}** section...*"
    elif nav_action and not nav_action.authorized:
        nav_suffix = f"\n\n⚠️ *Note: Navigation to {nav_action.destination} was restricted due to RBAC policy ({nav_action.reason}).*"

    if intent == INTENT_STOCKOUT:
        if not data:
            return "No stock-out prediction data could be found for the requested medicine or centre." + nav_suffix
        
        med_name = data.get("medicine_name", "Medicine")
        centre_name = data.get("centre_name", "Health Centre")
        days = data.get("predicted_days_until_stockout", 0)
        risk = data.get("risk_level", "UNKNOWN")
        curr_stock = data.get("current_stock", 0)
        min_stock = data.get("minimum_stock", 0)
        burn_rate = data.get("estimated_daily_consumption", 0)
        prob = data.get("risk_probability", 0)

        risk_emoji = "🔴" if risk in ["CRITICAL", "STOCK_OUT"] else "🟡" if risk in ["HIGH", "MEDIUM"] else "🟢"
        
        lines = [
            f"### {risk_emoji} **Stock-Out Prediction for {med_name}**",
            f"**Facility:** {centre_name} ({data.get('centre_type', 'PHC')})",
            f"- **Current Available Stock:** `{curr_stock}` units (Minimum Buffer: `{min_stock}`)",
            f"- **Estimated Daily Consumption:** `{burn_rate}` units/day",
            f"- **Two-Stage LightGBM Risk Level:** **{risk}** (Stockout Probability: `{prob * 100:.1f}%`)",
            f"- **Predicted Time to Depletion:** **{days} days**",
        ]
        
        if risk in ["CRITICAL", "STOCK_OUT"]:
            lines.append(f"\n⚠️ **Action Recommendation:** Stock is at critical depletion risk within the next 7 days. Immediate replenishment or inter-facility transfer requisition is advised.")
        elif risk in ["HIGH", "MEDIUM"]:
            lines.append(f"\n⚡ **Action Recommendation:** Moderate stock depletion anticipated within 8-14 days. Monitor dispensing rates and plan supply orders.")
        else:
            lines.append(f"\n✅ **Status:** Adequate inventory buffer maintained. Normal replenishment schedule applies.")
            
        return "\n".join(lines) + nav_suffix

    elif intent == INTENT_BED_FORECAST:
        if not data:
            return "No bed forecast data could be found for the requested ward or health centre." + nav_suffix
            
        w_name = data.get("ward_name", "Ward")
        centre_name = data.get("centre_name", "Health Centre")
        total = data.get("total_beds", 0)
        curr_occ = data.get("current_occupied_beds", 0)
        curr_pct = data.get("current_occupancy_rate_pct", 0)
        fcasts = data.get("forecasts", {})

        lines = [
            f"### 🛏️ **Multi-Horizon Bed Occupancy Forecast: {w_name}**",
            f"**Facility:** {centre_name} | **Total Capacity:** `{total}` beds",
            f"**Current Status:** `{curr_occ}` occupied (`{curr_pct}%` occupancy rate)\n",
            "**LightGBM Multi-Horizon Predictions:**"
        ]

        for h_key, h_title, days_ahead in [
            ("t_plus_1", "Tomorrow (t+1)", 1),
            ("t_plus_7", "Next Week (t+7)", 7),
            ("t_plus_14", "Two Weeks (t+14)", 14)
        ]:
            if h_key in fcasts:
                fc = fcasts[h_key]
                pred_occ = fc.get("predicted_occupied_beds", 0)
                pred_pct = fc.get("predicted_occupancy_rate_pct", 0)
                status_flag = fc.get("status", "NORMAL")
                status_badge = "🔴 Surge Risk" if status_flag == "SURGE_RISK" else "🟢 Normal"
                lines.append(f"- **{h_title} ({fc.get('target_date')}):** `{pred_occ}/{total}` beds (`{pred_pct}%`) — {status_badge}")

        return "\n".join(lines) + nav_suffix

    elif intent == INTENT_BED_STATUS:
        if not data:
            return "No bed occupancy records found for this health centre." + nav_suffix
        
        centre_name = data.get("centre_name", "Health Centre")
        wards_data = data.get("wards", [])
        total_facility_beds = sum(w.get("total_beds", 0) for w in wards_data)
        total_facility_occupied = sum(w.get("occupied_beds", 0) for w in wards_data)
        total_facility_avail = max(0, total_facility_beds - total_facility_occupied)
        occ_rate = round((total_facility_occupied / max(1, total_facility_beds)) * 100, 1)

        lines = [
            f"### 🏥 **Current Bed Occupancy Status: {centre_name}**",
            f"- **Facility Total Capacity:** `{total_facility_beds}` beds",
            f"- **Currently Occupied:** `{total_facility_occupied}` beds (`{occ_rate}%`)",
            f"- **Available for Admissions:** `{total_facility_avail}` beds\n",
            "**Ward Breakdown:**"
        ]

        for w in wards_data:
            lines.append(
                f"- **{w.get('ward_name')} ({w.get('ward_type', 'General')}):** "
                f"`{w.get('occupied_beds', 0)}/{w.get('total_beds', 0)}` beds occupied "
                f"(`{w.get('occupancy_pct', 0)}%`) • `{w.get('available_beds', 0)}` available"
            )

        return "\n".join(lines) + nav_suffix

    elif intent == INTENT_INVENTORY:
        if not data:
            return "No inventory records found matching your query." + nav_suffix

        centre_name = data.get("centre_name", "Health Centre")
        items = data.get("inventory_items", [])
        low_stock_items = [i for i in items if i.get("is_low_stock")]

        lines = [
            f"### 💊 **Medicine Inventory Overview: {centre_name}**",
            f"- **Tracked Medicines:** `{len(items)}` total formulations",
            f"- **Low-Stock Alerts:** `{len(low_stock_items)}` items below minimum threshold\n"
        ]

        if low_stock_items:
            lines.append("⚠️ **Low-Stock Medicines Requiring Attention:**")
            for item in low_stock_items:
                lines.append(f"- **{item.get('medicine_name')}:** `{item.get('current_stock')}` units (Min Required: `{item.get('minimum_stock')}`)")
            lines.append("")

        lines.append("**Current Stock Levels (Summary):**")
        for item in items[:10]:
            status_text = "⚠️ Low Stock" if item.get("is_low_stock") else "✅ Adequate"
            lines.append(f"- **{item.get('medicine_name')}:** `{item.get('current_stock')}` {item.get('unit', 'units')} — {status_text}")

        if len(items) > 10:
            lines.append(f"_...and {len(items) - 10} additional medicines in stock._")

        return "\n".join(lines) + nav_suffix

    elif intent == INTENT_ALERTS:
        if not data:
            return "No active alerts found for your facility scope." + nav_suffix

        alerts_list = data.get("alerts", [])
        scope_name = data.get("scope_name", "System")

        if not alerts_list:
            return f"✅ **All Clear:** There are currently no unresolved operational or clinical alerts active for **{scope_name}**." + nav_suffix

        lines = [
            f"### 🚨 **Active Alerts ({len(alerts_list)}) — {scope_name}**\n"
        ]
        for a in alerts_list:
            severity = a.get("severity", "MEDIUM")
            sev_badge = "🔴 Critical" if severity == "HIGH" else "🟡 Warning" if severity == "MEDIUM" else "ℹ️ Info"
            title_text = a.get("title") or a.get("alert_type", "Alert")
            desc_text = f": {a.get('description')}" if a.get("description") else ""
            lines.append(f"- **[{sev_badge}] {title_text}**{desc_text} _(Centre #{a.get('centre_id')})_")

        return "\n".join(lines) + nav_suffix

    else:
        # UNKNOWN / General
        return (
            "👋 **Hello! I am the SwasthyaNet AI Assistant.**\n\n"
            "I can assist you with both **Clinical/Operational Intelligence** and **Role-Aware Navigation**:\n\n"
            "📊 **Healthcare Q&A & AI Predictions:**\n"
            "- 💊 **Inventory:** _'Show current medicine stock'_, _'Which medicines are low in stock?'_\n"
            "- 🔮 **Stock-Out Prediction (LightGBM):** _'When will Paracetamol run out?'_, _'Which medicines are at risk and open inventory?'_\n"
            "- 🛏️ **Bed Status & Forecasts:** _'Check available beds'_, _'Forecast General ward bed occupancy'_\n"
            "- 🚨 **Alerts:** _'Show active emergency alerts'_\n\n"
            "🧭 **Role-Aware Application Navigation:**\n"
            "- 🚀 _'Open inventory'_, _'Show bed occupancy'_, _'Open alerts'_\n"
            "- 🚀 _'Go to user management'_ (Authorized Admins only)\n"
            "- 🚀 _'Open Super Admin dashboard'_ (Super Admin only)\n\n"
            "🔒 _All actions strictly enforce Role-Based Access Control (RBAC). The assistant is strictly read-only._"
        )


# -----------------------------------------------------------------------------
# POST /api/chatbot/chat
# -----------------------------------------------------------------------------
@router.post("/chat", response_model=schemas.ChatResponse)
def chatbot_chat(
    req: schemas.ChatRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """
    SwasthyaNet AI Assistant Endpoint.
    - Strictly enforces JWT authentication and RBAC.
    - Supports Healthcare Q&A and Role-Aware Application Navigation.
    - Supports combined queries (e.g. 'Which medicines are at risk and open inventory?').
    - Strictly read-only; performs zero database mutations.
    """
    user_role = user.get("role")
    user_centre_id = user.get("centre_id")
    user_district_id = user.get("district_id")
    message = req.message.strip()

    if not message:
        raise HTTPException(status_code=400, detail="Chat message cannot be empty.")

    # 1. Resolve Target Health Centre & Enforce RBAC
    target_centre_id = None
    target_centre = None

    if user_role in ["PHC_STAFF", "CHC_STAFF"]:
        # Staff can ONLY query their assigned centre
        if not user_centre_id:
            raise HTTPException(status_code=403, detail="Your user account is not assigned to any health centre.")
        if req.centre_id and req.centre_id != user_centre_id:
            raise HTTPException(status_code=403, detail="You do not have access to this centre's data.")
        target_centre_id = user_centre_id
        target_centre = db.query(models.HealthCentre).filter(models.HealthCentre.centre_id == target_centre_id).first()
        if not target_centre:
            raise HTTPException(status_code=404, detail="Assigned health centre not found.")

    elif user_role == "DISTRICT_ADMIN":
        # District Admin can query any centre in their district
        if req.centre_id:
            target_centre = db.query(models.HealthCentre).filter(models.HealthCentre.centre_id == req.centre_id).first()
            if not target_centre:
                raise HTTPException(status_code=404, detail="Health centre not found.")
            if target_centre.district_id != user_district_id:
                raise HTTPException(status_code=403, detail="Centre not in your district.")
            target_centre_id = target_centre.centre_id
        else:
            # Check if centre is mentioned by name in user text
            mentioned_c = find_mentioned_centre(message, db, district_id=user_district_id)
            if mentioned_c:
                target_centre = mentioned_c
                target_centre_id = mentioned_c.centre_id
            else:
                # Default to first centre in district or aggregate
                first_c = db.query(models.HealthCentre).filter(models.HealthCentre.district_id == user_district_id).first()
                if first_c:
                    target_centre = first_c
                    target_centre_id = first_c.centre_id

    elif user_role == "SUPER_ADMIN":
        # Super Admin has global access
        if req.centre_id:
            target_centre = db.query(models.HealthCentre).filter(models.HealthCentre.centre_id == req.centre_id).first()
            if not target_centre:
                raise HTTPException(status_code=404, detail="Health centre not found.")
            target_centre_id = target_centre.centre_id
        else:
            mentioned_c = find_mentioned_centre(message, db)
            if mentioned_c:
                target_centre = mentioned_c
                target_centre_id = mentioned_c.centre_id
            else:
                first_c = db.query(models.HealthCentre).first()
                if first_c:
                    target_centre = first_c
                    target_centre_id = first_c.centre_id

    # 2. Check for Navigation Action
    nav_action = detect_navigation_action(
        text=message,
        user_role=user_role,
        user_centre_id=target_centre_id,
        user_district_id=user_district_id,
        db=db
    )

    # 3. Classify Intent
    intent = classify_intent(message)
    
    # If pure navigation command without Q&A keywords, set intent to NAVIGATION
    if nav_action and intent in [INTENT_UNKNOWN, INTENT_NAVIGATION]:
        intent = INTENT_NAVIGATION

    trusted_data = None
    suggested_actions = []

    # 4. Process Intent & Retrieve Trusted Data
    if intent == INTENT_STOCKOUT:
        # Resolve target medicine
        target_med = None
        if req.medicine_id:
            target_med = db.query(models.Medicine).filter(models.Medicine.medicine_id == req.medicine_id).first()
        if not target_med:
            target_med = find_mentioned_medicine(message, db)
        if not target_med:
            # Default to first inventory medicine in centre
            first_inv = db.query(models.MedicineInventory).filter(
                models.MedicineInventory.centre_id == target_centre_id
            ).first()
            if first_inv:
                target_med = db.query(models.Medicine).filter(models.Medicine.medicine_id == first_inv.medicine_id).first()
            else:
                target_med = db.query(models.Medicine).first()

        if not target_centre_id or not target_med:
            raise HTTPException(status_code=400, detail="Could not determine health centre or medicine for stock-out prediction.")

        # Re-use Phase 5E LightGBM Two-Stage Champion Model Endpoint Logic
        trusted_data = get_medicine_stockout_prediction(
            centre_id=target_centre_id,
            medicine_id=target_med.medicine_id,
            db=db,
            user=user
        )
        suggested_actions = [
            f"Check {target_med.medicine_name} stock history",
            "Open medicine inventory",
            "View bed occupancy forecast"
        ]

    elif intent == INTENT_BED_FORECAST:
        # Resolve target ward
        target_ward = None
        if req.ward_id:
            target_ward = db.query(models.Ward).filter(
                models.Ward.ward_id == req.ward_id,
                models.Ward.centre_id == target_centre_id
            ).first()
        if not target_ward:
            target_ward = find_mentioned_ward(message, target_centre_id, db)
        if not target_ward:
            # Default to first ward in centre
            target_ward = db.query(models.Ward).filter(models.Ward.centre_id == target_centre_id).first()

        if not target_centre_id or not target_ward:
            raise HTTPException(status_code=400, detail="Could not determine health centre or ward for bed occupancy forecast.")

        # Re-use Multi-Horizon LightGBM Models (t+1, t+7, t+14)
        trusted_data = get_bed_occupancy_forecast(
            centre_id=target_centre_id,
            ward_id=target_ward.ward_id,
            db=db,
            user=user
        )
        suggested_actions = [
            f"Show {target_ward.ward_name} current bed status",
            "Predict Paracetamol stockout risk",
            "Show active facility alerts"
        ]

    elif intent == INTENT_BED_STATUS:
        if not target_centre_id:
            raise HTTPException(status_code=400, detail="Could not determine health centre for bed status.")

        verify_centre_access(target_centre_id, user, db)
        wards = db.query(models.Ward).filter(models.Ward.centre_id == target_centre_id).all()
        wards_list = []
        for w in wards:
            latest_occ = db.query(models.BedOccupancy).filter(
                models.BedOccupancy.ward_id == w.ward_id
            ).order_by(models.BedOccupancy.recorded_at.desc(), models.BedOccupancy.occupancy_id.desc()).first()
            
            is_emerg = w.ward_name.strip().lower() == "emergency"
            occ_val = latest_occ.occupied_beds if latest_occ else 0
            if not is_emerg:
                occ_val = min(occ_val, w.total_beds)
            avail_val = max(0, w.total_beds - occ_val)
            pct = round((occ_val / max(1, w.total_beds)) * 100, 1)

            wards_list.append({
                "ward_id": w.ward_id,
                "ward_name": w.ward_name,
                "ward_type": w.ward_name,
                "total_beds": w.total_beds,
                "occupied_beds": occ_val,
                "available_beds": avail_val,
                "occupancy_pct": pct
            })

        trusted_data = {
            "centre_id": target_centre.centre_id,
            "centre_name": target_centre.centre_name,
            "centre_type": target_centre.centre_type,
            "district_id": target_centre.district_id,
            "wards": wards_list
        }
        suggested_actions = [
            "Forecast next week bed occupancy",
            "Open medicine inventory",
            "View active alerts"
        ]

    elif intent == INTENT_INVENTORY:
        if not target_centre_id:
            raise HTTPException(status_code=400, detail="Could not determine health centre for inventory check.")

        verify_centre_access(target_centre_id, user, db)
        
        # Check if user asked about specific medicine
        specific_med = find_mentioned_medicine(message, db)
        inv_query = db.query(models.MedicineInventory).filter(models.MedicineInventory.centre_id == target_centre_id)
        if specific_med:
            inv_query = inv_query.filter(models.MedicineInventory.medicine_id == specific_med.medicine_id)
        
        inv_records = inv_query.all()
        meds_map = {m.medicine_id: m for m in db.query(models.Medicine).all()}

        items_list = []
        for inv in inv_records:
            med_obj = meds_map.get(inv.medicine_id)
            items_list.append({
                "medicine_id": inv.medicine_id,
                "medicine_name": med_obj.medicine_name if med_obj else f"Medicine #{inv.medicine_id}",
                "category": med_obj.category if med_obj else "General",
                "unit": med_obj.unit if med_obj else "units",
                "current_stock": inv.current_stock,
                "minimum_stock": inv.minimum_stock or 50,
                "is_low_stock": inv.current_stock < (inv.minimum_stock or 50)
            })

        trusted_data = {
            "centre_id": target_centre.centre_id,
            "centre_name": target_centre.centre_name,
            "centre_type": target_centre.centre_type,
            "district_id": target_centre.district_id,
            "inventory_items": items_list
        }
        suggested_actions = [
            "Predict stock-out days for low stock items",
            "Show bed occupancy",
            "Show facility alerts"
        ]

    elif intent == INTENT_ALERTS:
        # Alerts query scoped to user RBAC
        alerts_query = db.query(models.Alert).filter(
            models.Alert.status.in_(["OPEN", "ACTIVE", "Active", "Open"])
        )
        if user_role in ["PHC_STAFF", "CHC_STAFF"]:
            alerts_query = alerts_query.filter(models.Alert.centre_id == user_centre_id)
            scope_desc = f"{target_centre.centre_name if target_centre else 'Centre #' + str(user_centre_id)}"
        elif user_role == "DISTRICT_ADMIN":
            district_centres = db.query(models.HealthCentre.centre_id).filter(
                models.HealthCentre.district_id == user_district_id
            ).subquery()
            alerts_query = alerts_query.filter(models.Alert.centre_id.in_(district_centres))
            scope_desc = f"District #{user_district_id}"
        else:
            scope_desc = "System-Wide"

        alerts_records = alerts_query.all()
        alerts_list = [
            {
                "alert_id": a.alert_id,
                "centre_id": a.centre_id,
                "alert_type": a.alert_type,
                "severity": a.severity,
                "title": a.title,
                "description": a.description,
                "status": a.status
            }
            for a in alerts_records
        ]

        trusted_data = {
            "scope_name": scope_desc,
            "alerts": alerts_list
        }
        suggested_actions = [
            "Open medicine inventory",
            "View bed occupancy forecast",
            "Predict stock-out risk"
        ]

    elif intent == INTENT_NAVIGATION:
        suggested_actions = [
            "Open medicine inventory",
            "Show bed occupancy",
            "View facility alerts",
            "Go to user management"
        ]

    else:
        # UNKNOWN intent
        suggested_actions = [
            "Check Paracetamol stockout risk",
            "Open medicine inventory",
            "Forecast General ward beds",
            "View active facility alerts"
        ]

    # 5. Scope Metadata
    scope = {
        "role": user_role,
        "user_email": user.get("email"),
        "centre_id": target_centre_id,
        "centre_name": target_centre.centre_name if target_centre else None,
        "district_id": target_centre.district_id if target_centre else user_district_id
    }

    # 6. Synthesize Natural Language Answer
    answer = synthesize_explanation(intent, trusted_data, message, scope, nav_action)

    return schemas.ChatResponse(
        intent=intent,
        answer=answer,
        trusted_data=trusted_data if isinstance(trusted_data, dict) else None,
        scope=scope,
        navigation=nav_action,
        suggested_actions=suggested_actions,
        timestamp=datetime.now(timezone.utc).isoformat()
    )
