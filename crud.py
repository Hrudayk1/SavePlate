from sqlalchemy.orm import Session
from models import User, Listing

# Existing user-related CRUD
def create_user(db: Session, name: str, email: str, type: str):
    user = User(name=name, email=email, type=type)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def get_users(db: Session):
    return db.query(User).all()


# New listing-related CRUD
def create_listing(db: Session, listing_data):
    listing = Listing(**listing_data.dict())
    db.add(listing)
    db.commit()
    db.refresh(listing)
    return listing

def get_listings(db: Session):
    return db.query(Listing).all()
