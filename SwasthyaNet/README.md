# SwasthyaNet (स्वास्थ्यनेट)
**Integrated Rural Healthcare Operational Intelligence & Predictive Resource Network**

SwasthyaNet is a production-grade healthcare operations and intelligence platform designed for Primary Health Centres (PHCs), Community Health Centres (CHCs), District Health Administrations, and State Healthcare Directors across India.

---

## 🌟 Key Features & Capabilities

### 🛡️ Role-Aware Multi-Tier Administration (RBAC)
* **Super Admin**: System-wide administrative oversight across all state health districts, global user management, and health centre allocation.
* **District Admin**: District-scoped governance, facility performance tracking, staff management, and inter-centre medicine transfer approvals.
* **PHC & CHC Staff**: Facility-specific operational dashboards for bed census logging, inventory tracking, and doctor attendance.

### 🧠 Machine Learning & Predictive Analytics
1. **Medicine Stock-Out Risk Model (Phase 5E Champion LightGBM)**:
   * Two-stage prediction engine estimating days until stock-out, daily consumption burn rate, and surge risk level (Critical, Warning, Normal).
2. **Multi-Horizon Bed Occupancy Surge Forecasting**:
   * Multi-horizon LightGBM models predicting ward occupancy across **$t+1$**, **$t+7$**, and **$t+14$** day horizons with automated surge risk classification ($ \ge 90\%$ load).
3. **Centre Health Scoring & Operational Alerts**:
   * Dynamic healthcare facility health scores and real-time operational alert notifications.

### 🤖 SwasthyaNet AI Healthcare & Navigation Assistant
* **Endpoint**: `POST /api/chatbot/chat`
* **Dual Support**: Healthcare Q&A / Predictions + Role-Aware Application Navigation.
* **Strict Read-Only & Zero Database Mutation**: Performs zero database mutations. The LLM never communicates with PostgreSQL directly or executes raw SQL queries.
* **Secure Navigation Architecture**: Emits structured navigation actions (`{"intent": "NAVIGATION", "destination": "INVENTORY", "action": "OPEN_PAGE", "authorized": true}`) safely validated by React Router.

---

## 🛠️ Technology Stack

| Layer | Technology / Tools |
| :--- | :--- |
| **Frontend UI** | React 19, Vite 8, TailwindCSS v4, Lucide React Icons, React Router v7, Axios, Leaflet Maps |
| **Backend API** | Python 3.10+, FastAPI, Uvicorn, Pydantic v2, PyJWT, Passlib (Bcrypt) |
| **Database & ORM** | PostgreSQL 14+ (or SQLite Fallback), SQLAlchemy ORM |
| **AI / ML Models** | LightGBM 4.7, Scikit-learn, Pandas, NumPy, Joblib |

---

## 🚀 Quick Start & User Setup Guide

### Prerequisites
* **Python**: 3.10 or higher
* **Node.js**: 18.0 or higher & `npm`
* **PostgreSQL** (Optional): 14+ database running locally (or SQLite zero-setup fallback)

---

### Step 1: Backend Setup & Installation

1. Open a terminal and navigate to the `backend` folder:
   ```bash
   cd backend
   ```

2. Create and activate a Python virtual environment:
   * **Windows (PowerShell)**:
     ```powershell
     python -m venv venv
     .\venv\Scripts\Activate.ps1
     ```
   * **Linux / macOS**:
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```

3. Install all backend dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure your `.env` file in the `backend/` directory:
   ```env
   # PostgreSQL Database (Default)
   DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/swasthyanet

   # Alternative Zero-Setup SQLite Fallback (if PostgreSQL is not installed)
   # DATABASE_URL=sqlite:///./swasthyanet.db

   JWT_SECRET="supersecretjwtkey123"
   GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
   ```

5. **Seed Complete Operational Database & Demo Users (1-Step)**:
   ```bash
   python seed_database.py
   ```
   *This automatically creates all database tables and populates them with 7 Districts, 18 Health Centres, 54 Wards, 20 Medicines, 360 Inventory Items, 71 Bed Occupancies, 58 Alerts, and 42 Users.*

6. **Start the FastAPI Backend Server**:
   ```bash
   uvicorn main:app --reload --host 127.0.0.1 --port 8000
   ```
   *The backend REST API will run at **http://127.0.0.1:8000** and interactive OpenAPI docs at **http://127.0.0.1:8000/docs**.*

---

### Step 2: Frontend Setup & Launch

1. Open a second terminal window and navigate to the `frontend` folder:
   ```bash
   cd frontend
   ```

2. Install Node.js package dependencies:
   ```bash
   npm install
   ```

3. Start the Vite React Development Server:
   ```bash
   npm run dev
   ```
   *The application UI will open locally at **http://localhost:5173**.*

---

## 🔑 Pre-Configured Demo Credentials

Password for all pre-configured accounts: **`testpassword123`**

| Role | Email Address | Password | Access Rights |
| :--- | :--- | :--- | :--- |
| **Super Admin** | `superadmin@swasthyanet.com` | `testpassword123` | System-wide admin & user management |
| **District Admin (Coimbatore)** | `admin.coimbatore@swasthyanet.com` | `testpassword123` | District-wide health facilities |
| **District Admin (Chennai)** | `admin.chennai@swasthyanet.com` | `testpassword123` | District-wide health facilities |
| **PHC Staff** | `staff01@swasthyanet.com` | `testpassword123` | PHC operational dashboard |
| **CHC Staff** | `staff03@swasthyanet.com` | `testpassword123` | CHC operational dashboard |

---

## 🧪 Verification & Automated Testing

Run the 72-point comprehensive backend test suite verifying authentication, RBAC boundaries, LightGBM models, and zero-mutation database integrity:
```bash
cd backend
python test_chatbot.py
```

---

## 📁 Project Directory Structure

```
SwasthyaNet/
├── README.md                 # Consolidated Master Project Documentation
├── backend/                  # FastAPI REST Backend & ML Pipeline
│   ├── main.py               # FastAPI Application Entrypoint
│   ├── database.py           # SQLAlchemy Database Session Manager
│   ├── models.py             # Database Schema Definitions
│   ├── schemas.py            # Pydantic Request/Response Schemas
│   ├── requirements.txt      # Python Dependencies Manifest
│   ├── seed_database.py      # Automated 1-Step Database Seeder
│   ├── database_seed.json    # Complete Production Seed Dataset
│   ├── routers/              # API Route Handlers (Auth, Users, AI, Chatbot, etc.)
│   └── ml_models/            # Trained LightGBM AI Models
└── frontend/                 # Vite + React Dashboard UI
    ├── package.json          # Node Dependencies & Scripts
    ├── index.html            # Application HTML Root
    ├── vite.config.js        # Vite Configuration & Proxy Setup
    └── src/
        ├── components/       # React UI Components & AI Widget
        ├── pages/            # Role-Aware Page Views
        ├── context/          # React Auth Context & Provider
        └── services/         # Axios API Client Interceptor
```
