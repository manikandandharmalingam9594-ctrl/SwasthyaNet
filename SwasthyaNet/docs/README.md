# SwasthyaNet (स्वास्थ्यनेट / ஸ்வஸ்த்யாநெட்)
> **Integrated Regional Public Healthcare Management & Predictive AI Platform**

SwasthyaNet is an intelligent, full-stack healthcare operations platform designed for primary and community healthcare networks (PHCs and CHCs) across Tamil Nadu districts. It features multi-tier Role-Based Access Control (RBAC), multi-lingual voice inventory intake (English, Tamil, Hindi), real-time GIS mapping, and machine learning models for early medicine stock-out warning and multi-horizon bed occupancy forecasting.

---

## 🌟 Key Features

1. **Multi-Tier Role-Based Dashboards**:
   - **Super Admin**: State-wide operational intelligence across all 7 districts and 18 healthcare centres, user management, and system-wide AI risk radars.
   - **District Admin**: District-level facility monitoring, aggregated stock-out warnings, ward surge radar, and staff management.
   - **CHC Staff**: Community Health Centre facility management, multi-ward bed occupancy updates, medicine inventory tracking, and doctor attendance.
   - **PHC Staff**: Primary Health Centre operations, multilingual voice inventory intake, and local facility monitoring.

2. **Multilingual Voice-Powered Inventory Intake**:
   - Web Speech API integration supporting **English (`en-IN`)**, **Tamil (`ta-IN`)**, and **Hindi (`hi-IN`)**.
   - Natural language parsing for speech commands (e.g., *"Add 50 Paracetamol"* / *"பாராசிட்டமால் 50 சேர்த்தல்"* / *"50 पैरासिटामोल जोड़ें"*).

3. **Predictive AI Intelligence (Phase 5 ML Engine)**:
   - **Medicine Stock-Out Prediction**: Two-stage hierarchical model (Balanced LightGBM Classifier + Depletion Regressor + Physical Burn Constraint) predicting days until depletion and risk categories (`CRITICAL` $\le 7\text{d}$, `HIGH` $\le 14\text{d}$, `MEDIUM`, `LOW`).
   - **Bed Occupancy Multi-Horizon Forecasting**: Tuned LightGBM regressors predicting ward occupancy for $t+1$ (Tomorrow), $t+7$ (Next Week), and $t+14$ (2 Weeks Ahead) with capacity surge risk detection ($\ge 90\%$).

4. **GIS Interactive Mapping**:
   - Leaflet-based interactive district and facility location maps with live health score indicators and facility metrics.

---

## 🏗️ System Architecture

```
SwasthyaNet/
├── backend/                        # FastAPI Backend Application
│   ├── main.py                     # App entry point & router registration
│   ├── database.py                 # SQLAlchemy DB session & engine
│   ├── models.py                   # PostgreSQL schema definitions (15 tables)
│   ├── schemas.py                  # Pydantic request/response schemas
│   ├── dependencies.py             # JWT & RBAC security dependencies
│   ├── routers/                    # Modular API Routers
│   │   ├── auth.py                 # Authentication & JWT tokens
│   │   ├── ai.py                   # Real-time ML inference endpoints
│   │   ├── centres.py              # Health centre queries
│   │   ├── inventory.py            # Medicine inventory transactions
│   │   ├── wards.py                # Ward & bed occupancy updates
│   │   ├── doctors.py              # Doctor management
│   │   ├── attendance.py           # Doctor attendance tracking
│   │   ├── alerts.py               # Incident alerts
│   │   ├── health_scores.py        # Composite health score queries
│   │   ├── transfers.py            # Inter-facility medicine transfers
│   │   ├── users.py                # User administration
│   │   └── sync.py                 # Offline sync records
│   ├── ml_models/                  # Serialized Champion LightGBM Models
│   │   ├── stockout_stage1_classifier.joblib
│   │   ├── stockout_stage2_regressor.joblib
│   │   ├── bed_occ_t+1_champion_lgb.joblib
│   │   ├── bed_occ_t+7_champion_lgb.joblib
│   │   └── bed_occ_t+14_champion_lgb.joblib
│   └── requirements.txt            # Python dependencies
│
└── frontend/                       # React (Vite) Frontend Application
    ├── src/
    │   ├── components/             # Reusable UI Components
    │   │   ├── AiStockoutPredictionSection.jsx
    │   │   ├── AiBedForecastSection.jsx
    │   │   ├── AiAggregatedInsightsSection.jsx
    │   │   ├── DistrictMap.jsx
    │   │   ├── VoiceInventoryIntake.jsx
    │   │   └── UserManager.jsx
    │   ├── pages/                  # Dashboard Views
    │   │   ├── Login.jsx
    │   │   ├── PhcDashboard.jsx
    │   │   ├── ChcDashboard.jsx
    │   │   ├── DistrictAdminDashboard.jsx
    │   │   ├── SuperAdminDashboard.jsx
    │   │   └── CentreDetails.jsx
    │   ├── context/                # AuthContext & state
    │   └── services/               # Axios API client
    ├── package.json
    └── vite.config.js
```

---

## 🚀 Getting Started & Initialization

### Prerequisites
- **Node.js**: `v18.x` or higher (`npm` installed)
- **Python**: `v3.10` – `v3.12`
- **PostgreSQL**: `v14` or higher installed and running locally

---

### Step 1: Clone the Repository
```bash
git clone https://github.com/manikandandharmalingam9594-ctrl/SwasthyaNet.git
cd SwasthyaNet
```

---

### Step 2: Backend Setup

1. **Navigate to the backend folder**:
   ```bash
   cd backend
   ```

2. **Create and activate a virtual environment**:
   ```bash
   # Windows (PowerShell)
   python -m venv venv
   .\venv\Scripts\Activate.ps1

   # Linux / macOS
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables**:
   Create a `.env` file in `backend/.env`:
   ```ini
   DATABASE_URL=postgresql://postgres:postgres@localhost:5432/swasthyanet
   JWT_SECRET=your_super_secret_jwt_key_here_32_chars_min
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=1440
   ```

5. **Initialize PostgreSQL Database**:
   Create the database in PostgreSQL:
   ```sql
   CREATE DATABASE swasthyanet;
   ```
   *(The database tables and relations will be auto-generated by SQLAlchemy on first startup).*

6. **Start the FastAPI Backend Server**:
   ```bash
   uvicorn main:app --reload --port 8000
   ```
   - API Docs: `http://localhost:8000/docs`
   - Health Check: `http://localhost:8000/health`

---

### Step 3: Frontend Setup

1. **Navigate to the frontend folder** (in a new terminal):
   ```bash
   cd frontend
   ```

2. **Install Node dependencies**:
   ```bash
   npm install
   ```

3. **Start the Vite development server**:
   ```bash
   npm run dev
   ```
   - Open browser: `http://localhost:5173`

---

## 🔑 Default User Roles & Credentials

For initial testing and evaluation, the following pre-configured credentials can be used:

| Role | Email / Username | Default Password | Access Scope |
|---|---|---|---|
| **Super Admin** | `superadmin@swasthyanet.com` | `testpassword123` | Global state-wide access across all 7 districts & 18 facilities |
| **District Admin** | `admin.coimbatore@swasthyanet.com` | `testpassword123` | Coimbatore District (PHC 1, PHC 2, CHC 3) |
| **CHC Staff** | `staff03@swasthyanet.com` | `testchc123` | Coimbatore Central CHC (Centre ID: 3) |
| **PHC Staff** | `staff01@swasthyanet.com` | `testpassword123` | Coimbatore Central PHC (Centre ID: 1) |

---

## 📡 Key API Endpoints

### Authentication & Core
- `POST /api/auth/login` — JWT Authentication with role and facility claims.
- `GET /api/districts` — List all districts (Super Admin / District Admin).
- `GET /api/centres` — List health centres with RBAC filters.

### Machine Learning & AI Predictions
- `GET /api/ai/stockout/{centre_id}/{medicine_id}` — Real-time predicted days until stock-out, consumption burn rate, and risk level (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`).
- `GET /api/ai/bed-forecast/{centre_id}/{ward_id}` — Multi-horizon ward occupancy forecast ($t+1, t+7, t+14$) and surge risk flags.

### Facility Operations
- `GET /api/centres/{id}/inventory` — Live medicine inventory stock levels.
- `PUT /api/inventory/{id}` — Update medicine stock with IN/OUT audit logging.
- `GET /api/centres/{id}/beds` — Latest ward occupancy snapshots.
- `PUT /api/wards/{id}/occupancy` — Update ward occupied bed count (with capacity boundary validation).
- `POST /api/attendance` — Mark daily doctor attendance (`PRESENT` / `ABSENT`).

---

## 🧪 Testing & Verification

Run automated test suites from the `backend/` directory:

```bash
# Verify AI endpoints, RBAC isolation & 15-table DB schema audit
python verify_ai_endpoints.py

# Verify bed occupancy consistency and capacity enforcement
python verify_bed_consistency.py

# Verify standalone ML model loading and inference
python verify_phase5e_models.py
```


