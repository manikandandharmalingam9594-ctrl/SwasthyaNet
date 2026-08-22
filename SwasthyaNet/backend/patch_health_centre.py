with open("models.py", "r") as f:
    content = f.read()
if "users = relationship" not in content:
    content = content.replace(
        'wards = relationship("Ward", back_populates="centre")',
        'wards = relationship("Ward", back_populates="centre")\n    users = relationship("User", back_populates="centre")'
    )
    with open("models.py", "w") as f:
        f.write(content)
        print("Added users relationship to HealthCentre")
