from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
import models, schemas
from dependencies import get_current_user, RoleChecker
from routers.auth import get_password_hash

router = APIRouter(
    prefix="/users", 
    tags=["users"], 
    dependencies=[Depends(RoleChecker(["SUPER_ADMIN", "DISTRICT_ADMIN"]))]
)

@router.get("", response_model=List[schemas.User])
def get_users(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    role = current_user.get("role")
    
    if role == "SUPER_ADMIN":
        return db.query(models.User).order_by(models.User.user_id).all()
        
    if role == "DISTRICT_ADMIN":
        district_id = current_user.get("district_id")
        return db.query(models.User).filter(
            models.User.district_id == district_id
        ).order_by(models.User.user_id).all()
        
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")

@router.get("/{user_id}", response_model=schemas.User)
def get_user_by_id(user_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    target_user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
        
    role = current_user.get("role")
    if role == "DISTRICT_ADMIN":
        if target_user.district_id != current_user.get("district_id"):
            raise HTTPException(status_code=403, detail="User not in your district")
            
    return target_user

@router.post("", response_model=schemas.User, status_code=status.HTTP_201_CREATED)
def create_user(user_in: schemas.UserCreate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    caller_role = current_user.get("role")
    target_role = user_in.role.upper()
    
    # 1. Validate Target Role
    valid_roles = ["SUPER_ADMIN", "DISTRICT_ADMIN", "PHC_STAFF", "CHC_STAFF"]
    if target_role not in valid_roles:
        raise HTTPException(status_code=400, detail=f"Invalid role '{user_in.role}'. Allowed: {valid_roles}")
        
    # 2. Check Role Creation Permissions
    if caller_role == "DISTRICT_ADMIN":
        if target_role not in ["PHC_STAFF", "CHC_STAFF"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="District Admin can only create PHC_STAFF or CHC_STAFF users"
            )
            
    # 3. Check for existing email
    existing_user = db.query(models.User).filter(models.User.email == user_in.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail=f"User with email '{user_in.email}' already exists")
        
    # 4. District & Centre Assignment Validations
    assigned_district_id = user_in.district_id
    assigned_centre_id = user_in.centre_id

    if caller_role == "DISTRICT_ADMIN":
        caller_district_id = current_user.get("district_id")
        assigned_district_id = caller_district_id
        
        if not assigned_centre_id:
            raise HTTPException(status_code=400, detail="centre_id is required for staff users")
            
        centre = db.query(models.HealthCentre).filter(models.HealthCentre.centre_id == assigned_centre_id).first()
        if not centre:
            raise HTTPException(status_code=404, detail="Health centre not found")
        if centre.district_id != caller_district_id:
            raise HTTPException(status_code=403, detail="Cannot assign staff to a centre outside your district")
        if target_role == "PHC_STAFF" and centre.centre_type != "PHC":
            raise HTTPException(status_code=400, detail=f"Cannot assign PHC_STAFF to a {centre.centre_type} centre")
        if target_role == "CHC_STAFF" and centre.centre_type != "CHC":
            raise HTTPException(status_code=400, detail=f"Cannot assign CHC_STAFF to a {centre.centre_type} centre")
            
    elif caller_role == "SUPER_ADMIN":
        if target_role == "DISTRICT_ADMIN":
            if not assigned_district_id:
                raise HTTPException(status_code=400, detail="district_id is required for DISTRICT_ADMIN")
            district = db.query(models.District).filter(models.District.district_id == assigned_district_id).first()
            if not district:
                raise HTTPException(status_code=404, detail="District not found")
                
        elif target_role in ["PHC_STAFF", "CHC_STAFF"]:
            if not assigned_centre_id:
                raise HTTPException(status_code=400, detail="centre_id is required for staff users")
            centre = db.query(models.HealthCentre).filter(models.HealthCentre.centre_id == assigned_centre_id).first()
            if not centre:
                raise HTTPException(status_code=404, detail="Health centre not found")
            # Set district_id from centre if not provided or ensure consistency
            if assigned_district_id and assigned_district_id != centre.district_id:
                raise HTTPException(status_code=400, detail="Centre does not belong to the specified district")
            assigned_district_id = centre.district_id
            
            if target_role == "PHC_STAFF" and centre.centre_type != "PHC":
                raise HTTPException(status_code=400, detail=f"Cannot assign PHC_STAFF to a {centre.centre_type} centre")
            if target_role == "CHC_STAFF" and centre.centre_type != "CHC":
                raise HTTPException(status_code=400, detail=f"Cannot assign CHC_STAFF to a {centre.centre_type} centre")

    # 5. Determine or Generate Temporary Password
    raw_password = user_in.password
    if not raw_password or not raw_password.strip():
        from email_service import generate_temporary_password
        raw_password = generate_temporary_password(12)

    # 6. Create new user with hashed password and pending activation flags
    new_user = models.User(
        name=user_in.name,
        email=user_in.email,
        password_hash=get_password_hash(raw_password),
        role=target_role,
        centre_id=assigned_centre_id,
        district_id=assigned_district_id,
        language=user_in.language or "en",
        is_active=user_in.is_active if user_in.is_active is not None else True,
        is_activated=False,
        must_change_password=True
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # 7. Generate Activation Token & Send Onboarding Email
    try:
        from email_service import create_activation_token, send_activation_email
        
        centre_name = None
        district_name = None
        if new_user.centre_id:
            c = db.query(models.HealthCentre).filter(models.HealthCentre.centre_id == new_user.centre_id).first()
            if c:
                centre_name = c.centre_name
        if new_user.district_id:
            d = db.query(models.District).filter(models.District.district_id == new_user.district_id).first()
            if d:
                district_name = d.district_name
                
        token = create_activation_token(user_id=new_user.user_id, email=new_user.email, role=new_user.role)
        send_activation_email(
            to_email=new_user.email,
            name=new_user.name,
            role=new_user.role,
            temp_password=raw_password,
            activation_token=token,
            centre_name=centre_name,
            district_name=district_name
        )
    except Exception as e:
        print(f"[ERROR] Failed to dispatch activation email: {e}")

    return new_user

@router.post("/{user_id}/resend-activation")
def resend_activation_email(
    user_id: int, 
    db: Session = Depends(get_db), 
    current_user: dict = Depends(get_current_user)
):
    target_user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
        
    caller_role = current_user.get("role")
    if caller_role == "DISTRICT_ADMIN":
        if target_user.district_id != current_user.get("district_id"):
            raise HTTPException(status_code=403, detail="Cannot manage users outside your district")
            
    from email_service import generate_temporary_password, create_activation_token, send_activation_email
    
    # Generate new temporary password and reset activation flag
    new_temp_pwd = generate_temporary_password(12)
    target_user.password_hash = get_password_hash(new_temp_pwd)
    target_user.must_change_password = True
    target_user.is_activated = False
    db.commit()
    db.refresh(target_user)
    
    centre_name = None
    district_name = None
    if target_user.centre_id:
        c = db.query(models.HealthCentre).filter(models.HealthCentre.centre_id == target_user.centre_id).first()
        if c:
            centre_name = c.centre_name
    if target_user.district_id:
        d = db.query(models.District).filter(models.District.district_id == target_user.district_id).first()
        if d:
            district_name = d.district_name
            
    token = create_activation_token(user_id=target_user.user_id, email=target_user.email, role=target_user.role)
    dispatch_res = send_activation_email(
        to_email=target_user.email,
        name=target_user.name,
        role=target_user.role,
        temp_password=new_temp_pwd,
        activation_token=token,
        centre_name=centre_name,
        district_name=district_name
    )
    
    return {
        "status": "success",
        "message": f"Activation email and new temporary password sent to {target_user.email}",
        "email_dispatched": dispatch_res.get("sent", True),
        "method": dispatch_res.get("method", "none")
    }

@router.patch("/{user_id}/status", response_model=schemas.User)
def update_user_status(
    user_id: int, 
    status_in: schemas.UserStatusUpdate, 
    db: Session = Depends(get_db), 
    current_user: dict = Depends(get_current_user)
):
    target_user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
        
    caller_role = current_user.get("role")
    
    if caller_role == "DISTRICT_ADMIN":
        if target_user.district_id != current_user.get("district_id"):
            raise HTTPException(status_code=403, detail="Cannot modify user outside your district")
        if target_user.role in ["SUPER_ADMIN", "DISTRICT_ADMIN"]:
            raise HTTPException(status_code=403, detail="Cannot modify status of administrative users")
            
    # Prevent self-deactivation if it is the current user
    if target_user.user_id == current_user.get("user_id") and not status_in.is_active:
        raise HTTPException(status_code=400, detail="Cannot deactivate your own account")
        
    target_user.is_active = status_in.is_active
    db.commit()
    db.refresh(target_user)
    return target_user
