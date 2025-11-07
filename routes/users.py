from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from enum import Enum
from database import SessionLocal
from models import User

router = APIRouter(prefix="/users", tags=["Users"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Enum for user type 
class UserType(str, Enum):
    business = "Business"
    consumer = "Consumer"


# Create user (Business or Consumer)
@router.post("/", response_model=dict)
def create_user(
    name: str,
    email: str,
    type: UserType,  # dropdown
    db: Session = Depends(get_db)
):
    user = User(name=name, email=email, type=type.value)
    db.add(user)
    db.commit()
    db.refresh(user)
    return {
        "message": "User created successfully",
        "user_id": user.user_id,
        "name": user.name,
        "email": user.email,
        "type": user.type,
    }


# List all users
@router.get("/", response_model=list[dict])
def list_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return [
        {"user_id": u.user_id, "name": u.name, "email": u.email, "type": u.type}
        for u in users
    ]
