import re

for r in ["alerts", "health_scores", "sync"]:
    path = f"routers/{r}.py"
    with open(path, "r") as f:
        content = f.read()
    
    # Restrict GET / endpoints
    content = content.replace("dependencies=[Depends(get_current_user)]", "dependencies=[Depends(RoleChecker(['SUPER_ADMIN', 'DISTRICT_ADMIN']))]")
    
    with open(path, "w") as f:
        f.write(content)
    print(f"Restricted global routes in {r}.py to admins")
