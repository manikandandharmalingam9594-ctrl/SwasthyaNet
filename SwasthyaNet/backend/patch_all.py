import os

routers = ["doctors", "medicines", "sync", "health_scores", "alerts", "attendance", "inventory", "wards", "districts"]
for r in routers:
    path = f"routers/{r}.py"
    with open(path, "r") as f:
        content = f.read()
    
    # Add get_current_user to router if not present (except for districts which has RoleChecker)
    if "dependencies=[Depends(get_current_user)]" not in content and "dependencies=[Depends(RoleChecker" not in content:
        content = content.replace(f'router = APIRouter(prefix="/{r.replace("_", "-")}", tags=["{r}"])',
                                  f'router = APIRouter(prefix="/{r.replace("_", "-")}", tags=["{r}"], dependencies=[Depends(get_current_user)])')
        # Some prefixes might not have hyphens replaced in the code if they don't have underscores or match exactly
        content = content.replace(f'router = APIRouter(prefix="/{r}", tags=["{r}"])',
                                  f'router = APIRouter(prefix="/{r}", tags=["{r}"], dependencies=[Depends(get_current_user)])')
                                  
    with open(path, "w") as f:
        f.write(content)
    print(f"Patched {r}")
