from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import engine, get_db
import models
from routers import (
    auth,
    districts, centres, wards, doctors, attendance,
    medicines, inventory, alerts, health_scores, transfers, sync, users, ai
)

# Create all database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="SwasthyaNet API")

# Setup CORS to allow the frontend to communicate with the backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for development
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Include routers
app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(districts.router, prefix="/api")
app.include_router(centres.router, prefix="/api")
app.include_router(wards.router, prefix="/api")
app.include_router(doctors.router, prefix="/api")
app.include_router(attendance.router, prefix="/api")
app.include_router(medicines.router, prefix="/api")
app.include_router(inventory.router, prefix="/api")
app.include_router(alerts.router, prefix="/api")
app.include_router(health_scores.router, prefix="/api")
app.include_router(transfers.router, prefix="/api")
app.include_router(sync.router, prefix="/api")
app.include_router(ai.router, prefix="/api")

@app.get("/")
def read_root():
    return {"message": "Welcome to SwasthyaNet API"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/db-test")
def db_test(db: Session = Depends(get_db)):
    try:
        # Test connection
        db.execute(text("SELECT 1"))
        return {"database": "connected"}
    except Exception as e:
        return {"database": "failed", "error": str(e)}
