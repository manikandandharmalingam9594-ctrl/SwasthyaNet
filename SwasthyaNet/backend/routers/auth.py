from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import jwt
import os
from passlib.context import CryptContext
from dotenv import load_dotenv

import models, schemas
from database import get_db

load_dotenv()
JWT_SECRET = os.getenv("JWT_SECRET", "default_secret")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

router = APIRouter(prefix="/auth", tags=["auth"])

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=ALGORITHM)
    return encoded_jwt

@router.post("/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    access_token = create_access_token(
        data={
            "sub": user.email, 
            "role": user.role, 
            "user_id": user.user_id,
            "centre_id": user.centre_id,
            "district_id": user.district_id
        }
    )
    
    return {
        "access_token": access_token, 
        "token_type": "bearer", 
        "user": user,
        "must_change_password": bool(user.must_change_password)
    }

@router.get("/verify-activation-token", response_model=schemas.ActivationTokenVerifyResponse)
def verify_activation(token: str, db: Session = Depends(get_db)):
    from email_service import verify_activation_token
    try:
        payload = verify_activation_token(token)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        
    user_id = payload.get("user_id")
    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User account not found")
        
    centre_name = None
    district_name = None
    if user.centre_id:
        centre = db.query(models.HealthCentre).filter(models.HealthCentre.centre_id == user.centre_id).first()
        if centre:
            centre_name = centre.centre_name
    if user.district_id:
        district = db.query(models.District).filter(models.District.district_id == user.district_id).first()
        if district:
            district_name = district.district_name

    return {
        "valid": True,
        "user_id": user.user_id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "centre_name": centre_name,
        "district_name": district_name,
        "is_activated": bool(user.is_activated)
    }

@router.post("/activate-account", response_model=schemas.Token)
def activate_account(req: schemas.UserActivationRequest, db: Session = Depends(get_db)):
    from email_service import verify_activation_token
    try:
        payload = verify_activation_token(req.token)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        
    user_id = payload.get("user_id")
    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This account has been deactivated. Please contact your administrator.")

    # Validate temporary password if provided
    if req.temporary_password:
        if not verify_password(req.temporary_password, user.password_hash):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The temporary password provided is incorrect")

    # Update password and activate user
    user.password_hash = get_password_hash(req.new_password)
    user.is_activated = True
    user.must_change_password = False
    
    db.commit()
    db.refresh(user)

    # Automatically issue token for immediate login
    access_token = create_access_token(
        data={
            "sub": user.email, 
            "role": user.role, 
            "user_id": user.user_id,
            "centre_id": user.centre_id,
            "district_id": user.district_id
        }
    )

    return {
        "access_token": access_token, 
        "token_type": "bearer", 
        "user": user,
        "must_change_password": False
    }
