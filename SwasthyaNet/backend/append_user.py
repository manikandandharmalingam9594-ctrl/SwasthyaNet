model_code = """
class User(Base):
    __tablename__ = "users"
    user_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)
    password_hash = Column(Text, nullable=False)
    role = Column(String(30), nullable=False)
    centre_id = Column(Integer, ForeignKey("health_centres.centre_id"))
    language = Column(String(20))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    district_id = Column(Integer, ForeignKey("districts.district_id"))
    
    centre = relationship("HealthCentre", back_populates="users")
"""

with open("models.py", "a") as f:
    f.write(model_code)

schema_code = """
class UserBase(BaseModel):
    name: str
    email: str
    role: str
    centre_id: Optional[int] = None
    language: Optional[str] = None
    is_active: Optional[bool] = True
    district_id: Optional[int] = None

class User(UserBase):
    user_id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
    
class Token(BaseModel):
    access_token: str
    token_type: str
    user: User
"""

with open("schemas.py", "a") as f:
    f.write(schema_code)
