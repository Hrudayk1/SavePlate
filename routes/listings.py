from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional
from datetime import datetime

from database import get_db
from models import User, Listing
from schemas import ListingCreate, ListingResponse

router = APIRouter(prefix="/listings", tags=["Listings"])


# Create a new listing (only Business users)
@router.post("/", response_model=ListingResponse)
def create_listing(user_id: int, listing: ListingCreate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.type != "Business":
        raise HTTPException(status_code=403, detail="Only Business users can create listings")

    new_listing = Listing(
        **listing.dict(),
        seller_id=user.user_id,
        seller_name=user.name
    )

    db.add(new_listing)
    db.commit()
    db.refresh(new_listing)
    return new_listing


# View all listings (Consumers + Businesses)
@router.get("/", response_model=list[ListingResponse])
def get_all_listings(
    city: Optional[str] = None,
    cuisine: Optional[str] = None,
    search: Optional[str] = None,
    include_sold: bool = False,
    db: Session = Depends(get_db)
):
    query = db.query(Listing)

    # Optional filters
    if city:
        query = query.filter(Listing.city.ilike(f"%{city}%"))
    if cuisine:
        query = query.filter(Listing.cuisine.ilike(f"%{cuisine}%"))

    # Optional search filter across multiple fields
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                Listing.title.ilike(search_pattern),
                Listing.description.ilike(search_pattern),
                Listing.city.ilike(search_pattern),
                Listing.cuisine.ilike(search_pattern),
                Listing.seller_name.ilike(search_pattern)
            )
        )

    # Optional filter to include/exclude sold listings
    if not include_sold:
        query = query.filter(Listing.is_sold == False)

    return query.all()


# Update listing (only the seller, any field can be updated)
@router.put("/{listing_id}/update", response_model=ListingResponse)
def update_listing(
    listing_id: int,
    user_id: int,
    title: Optional[str] = None,
    description: Optional[str] = None,
    city: Optional[str] = None,
    cuisine: Optional[str] = None,
    price: Optional[float] = None,
    available_until: Optional[datetime] = None,
    is_sold: Optional[bool] = None,
    prepared_at: Optional[datetime] = None,
    expires_at: Optional[datetime] = None,
    allergens: Optional[str] = None,
    photo_url: Optional[str] = None,
    db: Session = Depends(get_db)
):
    listing = db.query(Listing).filter(Listing.item_id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    if listing.seller_id != user_id:
        raise HTTPException(status_code=403, detail="You can only update your own listings")

    if title is not None: listing.title = title
    if description is not None: listing.description = description
    if city is not None: listing.city = city
    if cuisine is not None: listing.cuisine = cuisine
    if price is not None: listing.price = price
    if available_until is not None: listing.available_until = available_until
    if is_sold is not None: listing.is_sold = is_sold
    if prepared_at is not None: listing.prepared_at = prepared_at
    if expires_at is not None: listing.expires_at = expires_at
    if allergens is not None: listing.allergens = allergens
    if photo_url is not None: listing.photo_url = photo_url

    db.commit()
    db.refresh(listing)
    return listing


# Delete listing (only the seller)
@router.delete("/{listing_id}")
def delete_listing(listing_id: int, user_id: int, db: Session = Depends(get_db)):
    listing = db.query(Listing).filter(Listing.item_id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    if listing.seller_id != user_id:
        raise HTTPException(status_code=403, detail="You can only delete your own listings")

    db.delete(listing)
    db.commit()
    return {"message": "Listing deleted successfully"}
