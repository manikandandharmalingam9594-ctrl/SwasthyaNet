# 🏥 SwasthyaNet

SwasthyaNet is an AI-powered healthcare management platform for PHCs, CHCs, District Administrators, and Super Administrators.

---

## 🚀 Features

### 🔐 Authentication & RBAC

* JWT-based authentication
* Super Admin, District Admin, PHC Staff, and CHC Staff roles
* Centre-level and district-level access control

### 👤 User Management

* Create and manage users
* Activate / deactivate accounts
* Role and centre assignment

### 🏥 Healthcare Centre Management

* PHC / CHC management
* District-wise centre monitoring
* Centre health scores

### 💊 Medicine Inventory

* View medicine stock
* IN / OUT stock transactions
* Stock history and audit logging
* Low-stock monitoring

### 🛏️ Bed Occupancy

* Ward-wise bed monitoring
* Occupancy updates
* Capacity validation
* Historical occupancy tracking

### 👨‍⚕️ Doctor Attendance

* Doctor listing
* PRESENT / ABSENT attendance
* Attendance tracking

### 🚨 Alerts

* Low-stock alerts
* Medicine stock-out alerts
* Bed occupancy alerts
* Doctor absence alerts
* Risk-based alert levels

### 🎙️ Voice-Based Inventory Intake

* Voice input for inventory operations
* Speech-to-text
* Medicine and quantity extraction
* Inventory transaction processing

### 🤖 AI Medicine Stock-Out Prediction

* Two-stage LightGBM architecture
* Stock-out risk prediction
* Days-until-stockout prediction
* Consumption-based prediction

### 📊 AI Bed Occupancy Forecasting

* LightGBM forecasting
* Next-day (`t+1`) prediction
* 7-day (`t+7`) prediction
* 14-day (`t+14`) prediction
* Occupancy and surge-risk prediction

### 📈 Role-Based Dashboards

* Super Admin Dashboard
* District Admin Dashboard
* PHC Staff Dashboard
* CHC Staff Dashboard

---

## 🏗️ Tech Stack

### Frontend

* React.js
* React Router
* JavaScript
* REST API

### Backend

* Python
* FastAPI
* SQLAlchemy
* Pydantic

### Database

* PostgreSQL

### Machine Learning

* Python
* Pandas
* NumPy
* Scikit-learn
* LightGBM
* Joblib

### Authentication & Security

* JWT
* bcrypt
* Role-Based Access Control (RBAC)

### AI / Voice

* Speech-to-Text
* Voice processing
* LightGBM
* Real-time ML inference

---

## ⚙️ Installation

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/SwasthyaNet.git
cd SwasthyaNet
```

### 2. Backend Setup

Navigate to the backend directory:

```bash
cd backend
```

Create a virtual environment:

```bash
python -m venv venv
```

**Windows:**

```bash
venv\Scripts\activate
```

**Mac/Linux:**

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

### 3. Environment Configuration

Create a `.env` file in the backend directory and configure the required environment variables.

Example:

```env
DATABASE_URL=your_database_url
SECRET_KEY=your_secret_key
```

### 4. Start Backend

From the `backend` directory:

```bash
uvicorn main:app --reload
```

Backend:

```text
http://127.0.0.1:8000
```

Swagger API Documentation:

```text
http://127.0.0.1:8000/docs
```

### 5. Start Frontend

Open another terminal and navigate to the frontend directory:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Start the development server:

```bash
npm run dev
```

Open the URL provided by Vite in your browser.

---

## 🧪 Quick Test

### 1. Test Authentication

1. Login with a valid user.
2. Verify successful authentication.
3. Verify the correct role-based dashboard is displayed.

### 2. Test Healthcare Management

1. Test medicine inventory IN / OUT operations.
2. Test bed occupancy updates.
3. Test doctor attendance.
4. Check generated alerts.

### 3. Test AI Features

1. Test AI medicine stock-out prediction.
2. Test AI bed occupancy forecasting.
3. Verify prediction results.

### 4. Test Role-Based Access

1. Login as different user roles.
2. Verify role-specific dashboards.
3. Verify unauthorized users cannot access other centres or districts.

---

## 🧪 Automated Tests

From the `backend` directory:

```bash
python verify_ai_endpoints.py
```

```bash
python verify_bed_consistency.py
```

```bash
python verify_phase5e_models.py
```

---

## 📊 API Documentation

Once the backend is running, access the interactive Swagger API documentation:

```text
http://127.0.0.1:8000/docs
```

---

## 🔒 Security

* JWT-based authentication
* Password hashing using bcrypt
* Role-Based Access Control
* Centre-level access restrictions
* District-level access restrictions
* Protected API endpoints

---

## 🤖 AI Capabilities

SwasthyaNet integrates machine learning to support healthcare resource management through:

* Medicine stock-out risk prediction
* Days-until-stockout prediction
* Bed occupancy forecasting
* Surge-risk prediction
* Consumption-based analysis
* Real-time ML inference

---

## 📌 Project Overview

SwasthyaNet brings healthcare centre management, inventory monitoring, attendance tracking, alerts, dashboards, voice-based inventory operations, and AI-powered predictions into a single platform.
