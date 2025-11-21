from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional
from datetime import datetime

from database import get_db
from models import User, Listing, Notification
from schemas import ListingCreate, ListingResponse

router = APIRouter(prefix="/listings", tags=["Listings"])


def _recalculate_and_persist_for_listings(db: Session, listings):
    """
    Recalculate dynamic price for provided listing objects.
    If price changes, update DB and create a notification for seller.
    Returns True if any changes were committed (for caller to commit).
    """
    now = datetime.utcnow()
    notifications_to_add = []
    any_change = False

    for listing in listings:
        if not listing.dynamic_pricing_enabled:
            continue

        new_price = listing.compute_dynamic_price(now)

        # If computed price is different from stored price -> update & notify
        # Use simple float comparison with rounding to 2 decimals
        if round(float(listing.price), 2) != round(float(new_price), 2):
            old_price = listing.price
            listing.price = new_price
            any_change = True

            # Create notification for seller
            msg = f"Dynamic pricing updated: new price for '{listing.title}' is ₹{listing.price}"
            notifications_to_add.append(
                Notification(
                    user_id=listing.seller_id,
                    message=msg,
                    created_at=datetime.utcnow()
                )
            )

    if notifications_to_add:
        db.add_all(notifications_to_add)

    return any_change


# Create a new listing (only Business users)
@router.post("/", response_model=ListingResponse)
def create_listing(user_id: int, listing: ListingCreate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.type != "Business":
        raise HTTPException(status_code=403, detail="Only Business users can create listings")

    # Ensure original_price is set to the initial price
    new_listing = Listing(
        **listing.dict(),
        seller_id=user.user_id,
        seller_name=user.name,
        original_price=listing.price  # store initial price as original_price
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

    listings = query.all()

    # Recalculate and persist dynamic prices for those listings
    changed = _recalculate_and_persist_for_listings(db, listings)
    if changed:
        db.commit()
        # Refresh the objects so values returned reflect changes
        for l in listings:
            db.refresh(l)

    return listings


# Get single listing, with dynamic price recalculation
@router.get("/{listing_id}", response_model=ListingResponse)
def get_listing(listing_id: int, db: Session = Depends(get_db)):
    listing = db.query(Listing).filter(Listing.item_id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    changed = _recalculate_and_persist_for_listings(db, [listing])
    if changed:
        db.commit()
        db.refresh(listing)

    return listing


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
    dynamic_pricing_enabled: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    listing = db.query(Listing).filter(Listing.item_id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    if listing.seller_id != user_id:
        raise HTTPException(status_code=403, detail="You can only update your own listings")

    # Basic updates
    if title is not None:
        listing.title = title
    if description is not None:
        listing.description = description
    if city is not None:
        listing.city = city
    if cuisine is not None:
        listing.cuisine = cuisine

    # If seller manually sets a new price, we treat that as the new original_price
    if price is not None:
        listing.price = price
        listing.original_price = price

    if available_until is not None:
        listing.available_until = available_until
    if is_sold is not None:
        listing.is_sold = is_sold
    if prepared_at is not None:
        listing.prepared_at = prepared_at
    if expires_at is not None:
        listing.expires_at = expires_at
    if allergens is not None:
        listing.allergens = allergens
    if photo_url is not None:
        listing.photo_url = photo_url

    # Handle dynamic pricing toggle
    if dynamic_pricing_enabled is not None:
        # Option A: when disabling, freeze price at whatever it currently is (do nothing to revert)
        if dynamic_pricing_enabled and not listing.dynamic_pricing_enabled:
            # turning ON: ensure original_price is set (store whatever current price is)
            listing.original_price = listing.price

        # turning OFF: we freeze price (do not revert to original_price)
        listing.dynamic_pricing_enabled = dynamic_pricing_enabled

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
