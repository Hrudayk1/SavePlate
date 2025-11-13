from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime
from models import Negotiation, User, Listing, Order
from database import get_db
from schemas import NegotiationResponse, NegotiationAction, NegotiationStatus

router = APIRouter(prefix="/negotiations", tags=["Negotiations"])

# Consumer starts a negotiation
@router.post("/start", response_model=NegotiationResponse)
def start_negotiation(listing_id: int, buyer_id: int, proposed_price: float, db: Session = Depends(get_db)):
    buyer = db.query(User).filter(User.user_id == buyer_id).first()
    if not buyer or buyer.type != "Consumer":
        raise HTTPException(status_code=403, detail="Only Consumers can start negotiations")

    listing = db.query(Listing).filter(Listing.item_id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    negotiation = Negotiation(
        listing_id=listing_id,
        buyer_id=buyer_id,
        seller_id=listing.seller_id,
        buyer_proposed_price=proposed_price,
        status="Pending",
    )

    db.add(negotiation)
    db.commit()
    db.refresh(negotiation)
    return negotiation


# Seller responds to negotiation
@router.put("/{negotiation_id}/respond", response_model=NegotiationResponse)
def respond_negotiation(
    negotiation_id: int,
    user_id: int,
    action: NegotiationAction = Query(..., description="Accept / Reject / Counter"),
    counter_price: float | None = None,
    db: Session = Depends(get_db),
):
    negotiation = db.query(Negotiation).filter(Negotiation.negotiation_id == negotiation_id).first()
    if not negotiation:
        raise HTTPException(status_code=404, detail="Negotiation not found")

    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Prevent duplicate actions
    if negotiation.status in [NegotiationStatus.accepted, NegotiationStatus.rejected]:
        raise HTTPException(
            status_code=400,
            detail=f"Negotiation already {negotiation.status.lower()}, no further actions allowed",
        )

    if action == NegotiationAction.counter:
        if counter_price is None:
            raise HTTPException(status_code=400, detail="Counter price is required")

        if user.user_id == negotiation.seller_id:
            negotiation.seller_response_price = counter_price
            negotiation.status = NegotiationStatus.seller_countered
        elif user.user_id == negotiation.buyer_id:
            negotiation.buyer_proposed_price = counter_price
            negotiation.status = NegotiationStatus.buyer_countered
        else:
            raise HTTPException(status_code=403, detail="User not part of this negotiation")

    elif action == NegotiationAction.accept:
        negotiation.status = NegotiationStatus.accepted

        final_price = negotiation.seller_response_price or negotiation.buyer_proposed_price

        new_order = Order(
            seller_id=negotiation.seller_id,
            seller_name=negotiation.seller.name,
            buyer_id=negotiation.buyer_id,
            buyer_name=negotiation.buyer.name,
            item_id=negotiation.listing_id,
            item_name=negotiation.listing.title,
            price=final_price,
            ordered_at=datetime.utcnow(),
        )
        negotiation.listing.is_sold = True
        db.add(new_order)

    elif action == NegotiationAction.reject:
        negotiation.status = NegotiationStatus.rejected

    else:
        raise HTTPException(status_code=400, detail="Invalid action")

    db.commit()
    db.refresh(negotiation)
    return negotiation


# View all negotiations (with optional filters)
@router.get("/", response_model=list[NegotiationResponse])
def get_negotiations(
    buyer_id: int | None = None,
    seller_id: int | None = None,
    status: NegotiationStatus | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(Negotiation)
    if buyer_id:
        query = query.filter(Negotiation.buyer_id == buyer_id)
    if seller_id:
        query = query.filter(Negotiation.seller_id == seller_id)
    if status:
        query = query.filter(Negotiation.status == status.value)
    return query.all()
