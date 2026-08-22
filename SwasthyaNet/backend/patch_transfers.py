import re

with open("routers/transfers.py", "r") as f:
    content = f.read()

# Add get_current_user to all router dependencies
if "dependencies=[Depends(get_current_user)]" not in content:
    content = content.replace('router = APIRouter(prefix="/transfers", tags=["transfers"])',
                              'router = APIRouter(prefix="/transfers", tags=["transfers"], dependencies=[Depends(get_current_user)])')

# get_transfers -> only SUPER_ADMIN, DISTRICT_ADMIN
if "user: dict = Depends(RoleChecker(['SUPER_ADMIN', 'DISTRICT_ADMIN']))" not in content:
    content = content.replace('def get_transfers(db: Session = Depends(get_db)):',
                              "def get_transfers(db: Session = Depends(get_db), user: dict = Depends(RoleChecker(['SUPER_ADMIN', 'DISTRICT_ADMIN']))):")

# create_transfer -> verify from_centre_id
if "verify_centre_access(transfer.from_centre_id, user, db)" not in content:
    content = content.replace('def create_transfer(transfer: schemas.TransferCreate, db: Session = Depends(get_db)):',
                              'def create_transfer(transfer: schemas.TransferCreate, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):\n    verify_centre_access(transfer.from_centre_id, user, db)')

# approve/reject -> only DISTRICT_ADMIN / SUPER_ADMIN.
# Wait, for approve/reject, maybe I should check verify_district_access using transfer.from_centre_id! But the requirement says "DISTRICT_ADMIN: Approve/reject medicine transfers."
if "user: dict = Depends(RoleChecker(['SUPER_ADMIN', 'DISTRICT_ADMIN']))" not in content:
    content = content.replace('def approve_transfer(transfer_id: int, db: Session = Depends(get_db)):',
                              "def approve_transfer(transfer_id: int, db: Session = Depends(get_db), user: dict = Depends(RoleChecker(['SUPER_ADMIN', 'DISTRICT_ADMIN']))):")
    content = content.replace('def reject_transfer(transfer_id: int, db: Session = Depends(get_db)):',
                              "def reject_transfer(transfer_id: int, db: Session = Depends(get_db), user: dict = Depends(RoleChecker(['SUPER_ADMIN', 'DISTRICT_ADMIN']))):")

with open("routers/transfers.py", "w") as f:
    f.write(content)
print("Updated transfers.py")
