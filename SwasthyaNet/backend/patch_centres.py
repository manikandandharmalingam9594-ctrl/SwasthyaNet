import re

with open("routers/centres.py", "r") as f:
    content = f.read()

# Add get_current_user to the router level
content = content.replace('router = APIRouter(prefix="/centres", tags=["centres"])', 
                          'router = APIRouter(prefix="/centres", tags=["centres"], dependencies=[Depends(get_current_user)])')

# For get_centres, we won't add verify_centre_access because there's no centre_id. 
# We'll just leave it for now or we could add RoleChecker for admin.
# Let's add verify_centre_access to all endpoints with {centre_id}
def replacer(match):
    prefix = match.group(1)
    return prefix + ', user: dict = Depends(verify_centre_access)'

# Replace `def get_centre*(centre_id: int, db: Session = Depends(get_db)):`
content = re.sub(r'(def get_[a-z_]+\(centre_id: int, db: Session = Depends\(get_db\))', replacer, content)

with open("routers/centres.py", "w") as f:
    f.write(content)
print("Updated centres.py")
