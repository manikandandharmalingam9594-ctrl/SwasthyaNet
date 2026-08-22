import models

print("User model attributes:")
for attr in dir(models.User):
    if not attr.startswith("_"):
        print(attr)
