from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models, schemas
from dependencies import get_current_user, RoleChecker, verify_centre_access, verify_district_access

router = APIRouter(prefix="/inventory", tags=["inventory"], dependencies=[Depends(get_current_user)])

@router.put("/{inventory_id}", response_model=schemas.MedicineInventory)
def update_inventory(inventory_id: int, update_data: schemas.InventoryUpdate, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    inventory = db.query(models.MedicineInventory).filter(models.MedicineInventory.inventory_id == inventory_id).first()
    if not inventory:
        raise HTTPException(status_code=404, detail="Inventory not found")
    
    trans_type = update_data.transaction_type.upper()
    if trans_type == "IN":
        trans_type = "RECEIVED"
    elif trans_type == "OUT":
        trans_type = "DISPENSED"
        
    valid_types = ['RECEIVED', 'DISPENSED', 'ADJUSTED', 'TRANSFER_IN', 'TRANSFER_OUT']
    if trans_type not in valid_types:
        raise HTTPException(status_code=400, detail=f"Invalid transaction type. Must be one of {valid_types}")
        
    if trans_type in ['DISPENSED', 'TRANSFER_OUT']:
        if inventory.current_stock < update_data.quantity:
            raise HTTPException(status_code=400, detail="Insufficient stock")
        inventory.current_stock -= update_data.quantity
    else:
        inventory.current_stock += update_data.quantity
        
    try:
        history = models.MedicineStockHistory(
            centre_id=inventory.centre_id,
            medicine_id=inventory.medicine_id,
            quantity=update_data.quantity,
            transaction_type=trans_type
        )
        db.add(history)
        
        db.commit()
        db.refresh(inventory)
        return inventory
    except Exception as e:
        db.rollback()
        print(e); raise HTTPException(status_code=400, detail="Database transaction failed")
