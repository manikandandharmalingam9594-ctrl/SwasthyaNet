import os

routers = ["districts", "centres", "wards", "inventory", "attendance", "transfers", "alerts", "health_scores", "sync", "medicines", "doctors"]
for r in routers:
    path = f"routers/{r}.py"
    with open(path, "r") as f:
        content = f.read()
    
    # Check if we already added dependencies
    if "from dependencies import" not in content:
        # Add import
        content = content.replace(
            "import models, schemas",
            "import models, schemas\nfrom dependencies import get_current_user, RoleChecker, verify_centre_access, verify_district_access"
        )
        with open(path, "w") as f:
            f.write(content)
        print(f"Added dependencies import to {r}")
