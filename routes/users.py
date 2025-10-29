# routes/users.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import SessionLocal
from models import User

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/users/")
def create_user(name: str, email: str, type: str, db: Session = Depends(get_db)):
    user = User(name=name, email=email, type=type)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.get("/users/")
def list_users(db: Session = Depends(get_db)):
    return db.query(User).all()
