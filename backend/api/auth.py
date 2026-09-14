from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.config.database import get_db, init_db
from backend.models.models import User, Farm, Field
from backend.auth.security import hash_password, verify_password, create_access_token
from backend.auth.deps import get_current_user
import re

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

# Ensure tables exist on first import
try:
    init_db()
except Exception:
    pass

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

class RegisterIn(BaseModel):
    name: str
    email: str
    password: str
    confirm_password: str

class LoginIn(BaseModel):
    email: str
    password: str

@router.get("/")
def auth_home():
    return {"message": "Authentication API is working."}

@router.post("/register")
def register(payload: RegisterIn, db: Session = Depends(get_db)):
    email = payload.email.lower().strip()
    if not EMAIL_RE.match(email):
        raise HTTPException(400, "Enter a valid email address.")
    if len(payload.password) < 8:
        raise HTTPException(400, "Password must be at least 8 characters.")
    if payload.password != payload.confirm_password:
        raise HTTPException(400, "Passwords do not match.")
    if not payload.name or len(payload.name.strip()) < 2:
        raise HTTPException(400, "Name is required.")
    exists = db.query(User).filter(User.email == email).first()
    if exists:
        raise HTTPException(400, "Email already registered.")
    user = User(name=payload.name.strip(), email=email, password_hash=hash_password(payload.password))
    db.add(user)
    db.flush()
    # Auto-create farm + default field for new farmer
    farm = Farm(user_id=user.id, name=f"{user.name}'s Farm")
    db.add(farm)
    db.flush()
    field = Field(id=f"FIELD_{user.id[:6].upper()}", farm_id=farm.id, name="Field 1")
    db.add(field)
    db.commit()
    db.refresh(user)
    token = create_access_token({"sub": user.id, "email": user.email})
    return {"token": token, "user": {"id": user.id, "name": user.name, "email": user.email}}

@router.post("/login")
def login(payload: LoginIn, db: Session = Depends(get_db)):
    email = payload.email.lower().strip()
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    token = create_access_token({"sub": user.id, "email": user.email})
    return {"token": token, "user": {"id": user.id, "name": user.name, "email": user.email}}

@router.get("/me")
def me(current_user: User = Depends(get_current_user)):
    return {"id": current_user.id, "name": current_user.name, "email": current_user.email}

@router.post("/logout")
def logout(current_user: User = Depends(get_current_user)):
    # Stateless JWT — client discards token. Endpoint exists for symmetry.
    return {"message": "Logged out"}
