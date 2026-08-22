with open("main.py", "r") as f:
    content = f.read()

if "import auth" not in content:
    content = content.replace("import (", "import (\n    auth,")
    content = content.replace('app.include_router(districts.router', 'app.include_router(auth.router, prefix="/api")\napp.include_router(districts.router')
    with open("main.py", "w") as f:
        f.write(content)
        print("Registered auth router in main.py")
