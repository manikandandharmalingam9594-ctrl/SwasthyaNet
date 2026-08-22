with open("routers/inventory.py", "r") as f:
    content = f.read()

if "user: dict = Depends(get_current_user)" not in content:
    content = content.replace("db: Session = Depends(get_db)):", "db: Session = Depends(get_db), user: dict = Depends(get_current_user)):")
    content = content.replace('raise HTTPException(status_code=404, detail="Inventory record not found")', 'raise HTTPException(status_code=404, detail="Inventory record not found")\n        verify_centre_access(inventory.centre_id, user, db)')
    with open("routers/inventory.py", "w") as f:
        f.write(content)
    print("Updated inventory.py")
