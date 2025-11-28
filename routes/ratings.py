from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
from models import Rating, User, Order, Donation
from schemas import RatingResponse, RatingSummary

router = APIRouter(prefix="/ratings", tags=["Ratings"])


# RATE ORDER
@router.post("/rate-order", response_model=RatingResponse)
def rate_order(
    buyer_id: int = Query(...),
    order_id: int = Query(...),
    score: int = Query(...),
    db: Session = Depends(get_db)
):
    if score < 1 or score > 5:
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")

    buyer = db.query(User).filter(User.user_id == buyer_id).first()
    if not buyer:
        raise HTTPException(status_code=404, detail="Buyer not found")
    if buyer.type != "Consumer":
        raise HTTPException(status_code=403, detail="Only consumers can rate orders")

    order = db.query(Order).filter(Order.order_id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    seller = db.query(User).filter(User.user_id == order.seller_id).first()
    if not seller:
        raise HTTPException(status_code=404, detail="Seller not found")
    if seller.type != "Business":
        raise HTTPException(status_code=403, detail="Only business accounts can be rated")

    # CHECK DUPLICATE RATING
    existing = (
        db.query(Rating)
        .filter(Rating.rater_id == buyer_id, Rating.order_id == order_id)
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="You have already rated this order")

    rating = Rating(
        rater_id=buyer_id,
        rated_id=seller.user_id,
        order_id=order_id,
        donation_id=None,
        score=score
    )

    db.add(rating)
    db.commit()
    db.refresh(rating)

    return rating


# RATE DONATION
@router.post("/rate-donation", response_model=RatingResponse)
def rate_donation(
    charity_user_id: int = Query(..., description="User ID of the charity account"),
    donation_id: int = Query(...),
    score: int = Query(...),
    db: Session = Depends(get_db)
):
    if score < 1 or score > 5:
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")

    charity_user = db.query(User).filter(User.user_id == charity_user_id).first()
    if not charity_user:
        raise HTTPException(status_code=404, detail="Charity user account not found")
    if charity_user.type != "Charity":
        raise HTTPException(status_code=403, detail="Only charity accounts can rate donations")

    donation = db.query(Donation).filter(Donation.donation_id == donation_id).first()
    if not donation:
        raise HTTPException(status_code=404, detail="Donation not found")

    business = db.query(User).filter(User.user_id == donation.business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    if business.type != "Business":
        raise HTTPException(status_code=403, detail="Only business accounts can be rated")

    # CHECK DUPLICATE RATING
    existing = (
        db.query(Rating)
        .filter(Rating.rater_id == charity_user_id, Rating.donation_id == donation_id)
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="You have already rated this donation")

    rating = Rating(
        rater_id=charity_user_id,
        rated_id=business.user_id,
        order_id=None,
        donation_id=donation_id,
        score=score
    )

    db.add(rating)
    db.commit()
    db.refresh(rating)

    return rating


# GET BUSINESS RATING SUMMARY
@router.get("/{business_id}", response_model=RatingSummary)
def get_business_rating(business_id: int, db: Session = Depends(get_db)):

    user = db.query(User).filter(User.user_id == business_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.type != "Business":
        raise HTTPException(status_code=403, detail="Only business accounts have ratings")

    ratings = db.query(Rating).filter(Rating.rated_id == business_id).all()

    if not ratings:
        return RatingSummary(
            rated_id=business_id,
            average_rating=0.0,
            total_ratings=0
        )

    avg = sum(r.score for r in ratings) / len(ratings)

    return RatingSummary(
        rated_id=user.user_id,
        average_rating=round(avg, 2),
        total_ratings=len(ratings)
    )
