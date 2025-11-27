from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import User, CharityProfile
from schemas import CharityCreate, CharityResponse

router = APIRouter(prefix="/charity", tags=["Charity"])


# Create a charity profile (only charity users)
@router.post("/", response_model=CharityResponse)
def create_charity_profile(
    user_id: int,
    data: CharityCreate,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.type != "Charity":
        raise HTTPException(status_code=403, detail="Only users of type Charity can create charity profiles")

    profile = CharityProfile(
        user_id=user_id,
        org_name=data.org_name,
        description=data.description,
        city=data.city
    )

    db.add(profile)
    db.commit()
    db.refresh(profile)

    return profile


# Get all charity profiles (optional city filter)
@router.get("/", response_model=list[CharityResponse])
def list_charities(
    city: str | None = None,
    db: Session = Depends(get_db)
):
    query = db.query(CharityProfile)
    if city:
        query = query.filter(CharityProfile.city.ilike(f"%{city}%"))

    return query.all()
