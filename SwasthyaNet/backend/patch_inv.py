with open("routers/inventory.py", "r") as f:
    code = f.read()
code = code.replace("raise HTTPException(status_code=400", "print(e); raise HTTPException(status_code=400")
with open("routers/inventory.py", "w") as f:
    f.write(code)
