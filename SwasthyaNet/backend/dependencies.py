from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from typing import List
from routers.auth import JWT_SECRET, ALGORITHM
from database import get_db
from sqlalchemy.orm import Session
import models

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

class RoleChecker:
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, user: dict = Depends(get_current_user)):
        if user.get("role") not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return user

def verify_centre_access(centre_id: int, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    role = user.get("role")
    if role == "SUPER_ADMIN":
        return user
        
    if role == "DISTRICT_ADMIN":
        centre = db.query(models.HealthCentre).filter(models.HealthCentre.centre_id == centre_id).first()
        if not centre or centre.district_id != user.get("district_id"):
            raise HTTPException(status_code=403, detail="Centre not in your district")
        return user
        
    if role in ["PHC_STAFF", "CHC_STAFF"]:
        if user.get("centre_id") != centre_id:
            raise HTTPException(status_code=403, detail="You do not have access to this centre's data")
            
    return user

def verify_district_access(district_id: int, user: dict = Depends(get_current_user)):
    role = user.get("role")
    if role == "SUPER_ADMIN":
        return user
        
    if role == "DISTRICT_ADMIN":
        if user.get("district_id") != district_id:
            raise HTTPException(status_code=403, detail="You do not have access to this district")
        return user
        
    raise HTTPException(status_code=403, detail="Insufficient permissions")
