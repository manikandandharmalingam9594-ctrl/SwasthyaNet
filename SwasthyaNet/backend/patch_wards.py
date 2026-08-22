with open("routers/wards.py", "r") as f:
    content = f.read()

if "user: dict = Depends(get_current_user)" not in content:
    content = content.replace("db: Session = Depends(get_db)):", "db: Session = Depends(get_db), user: dict = Depends(get_current_user)):")
    content = content.replace('raise HTTPException(status_code=404, detail="Ward not found")', 'raise HTTPException(status_code=404, detail="Ward not found")\n    verify_centre_access(ward.centre_id, user, db)')
    with open("routers/wards.py", "w") as f:
        f.write(content)
    print("Updated wards.py")
