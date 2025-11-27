from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from database import get_db
from models import User, CharityProfile, Donation, Notification
from schemas import DonationCreate, DonationResponse

router = APIRouter(prefix="/donate", tags=["Donations"])


@router.post("/", response_model=DonationResponse)
def donate_food(
    business_id: int,
    charity_id: int,
    data: DonationCreate,
    db: Session = Depends(get_db)
):
    # Validate business user
    business = db.query(User).filter(User.user_id == business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business user not found")
    if business.type != "Business":
        raise HTTPException(status_code=403, detail="Only business users can donate food")

    # Validate charity entry
    charity = db.query(CharityProfile).filter(
        CharityProfile.charity_id == charity_id
    ).first()

    if not charity:
        raise HTTPException(status_code=404, detail="Charity not found")

    # Create Donation record (separate table)
    donation = Donation(
        business_id=business.user_id,
        charity_id=charity.charity_id,
        title=data.title,
        description=data.description,
        cuisine=data.cuisine,
        city=data.city,
        photo_url=data.photo_url,
        allergens=data.allergens,
        available_until=data.available_until,
        prepared_at=data.prepared_at,
        expires_at=data.expires_at,
        is_collected=False
    )

    db.add(donation)

    # Notifications: notify charity and business
    charity_notification = Notification(
        user_id=charity.user_id,
        message=f"New donation available from {business.name}: '{data.title}'",
        created_at=datetime.utcnow()
    )

    business_notification = Notification(
        user_id=business.user_id,
        message=f"You have successfully donated '{data.title}' to {charity.org_name}.",
        created_at=datetime.utcnow()
    )

    db.add_all([charity_notification, business_notification])

    db.commit()
    db.refresh(donation)

    return donation


# Get donations received by a charity (charity_id as query param)
@router.get("/received", response_model=list[DonationResponse])
def get_donations_received(charity_id: int, db: Session = Depends(get_db)):
    charity = db.query(CharityProfile).filter(CharityProfile.charity_id == charity_id).first()
    if not charity:
        raise HTTPException(status_code=404, detail="Charity not found")

    donations = db.query(Donation).filter(Donation.charity_id == charity_id).order_by(Donation.created_at.desc()).all()
    return donations


# Get donations posted by a business
@router.get("/posted", response_model=list[DonationResponse])
def get_donations_posted(business_id: int, db: Session = Depends(get_db)):
    business = db.query(User).filter(User.user_id == business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business user not found")

    donations = db.query(Donation).filter(Donation.business_id == business_id).order_by(Donation.created_at.desc()).all()
    return donations


# Mark donation as collected
@router.post("/collect/{donation_id}", response_model=DonationResponse)
def mark_donation_collected(
    donation_id: int,
    charity_id: int,
    db: Session = Depends(get_db)
):
    # Check donation
    donation = db.query(Donation).filter(Donation.donation_id == donation_id).first()
    if not donation:
        raise HTTPException(status_code=404, detail="Donation not found")

    # Check charity matches
    charity = db.query(CharityProfile).filter(CharityProfile.charity_id == charity_id).first()
    if not charity:
        raise HTTPException(status_code=404, detail="Charity not found")

    if donation.charity_id != charity_id:
        raise HTTPException(
            status_code=403,
            detail="This donation does not belong to the specified charity"
        )

    # Mark as collected
    donation.is_collected = True
    donation.collected_at = datetime.utcnow()  # Optional: only if field exists

    # Notify business
    business = db.query(User).filter(User.user_id == donation.business_id).first()
    if business:
        business_notification = Notification(
            user_id=business.user_id,
            message=f"Your donation '{donation.title}' was collected by {charity.org_name}.",
            created_at=datetime.utcnow()
        )
        db.add(business_notification)

    db.commit()
    db.refresh(donation)

    return donation