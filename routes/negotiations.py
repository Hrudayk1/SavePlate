# routes/negotiations.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime
from enum import Enum
from models import Negotiation, User, Listing, Order
from database import get_db
from schemas import NegotiationResponse


router = APIRouter(prefix="/negotiations", tags=["Negotiations"])


# Enum for negotiation response options
class NegotiationAction(str, Enum):
    accept = "Accept"
    reject = "Reject"
    counter = "Counter"


# Consumer starts a negotiation
@router.post("/start", response_model=NegotiationResponse)
def start_negotiation(
    listing_id: int = Query(..., description="ID of the listing to negotiate for"),
    buyer_id: int = Query(..., description="ID of the Consumer starting negotiation"),
    proposed_price: float = Query(..., description="Price proposed by the buyer"),
    db: Session = Depends(get_db),
):
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
        proposed_price=proposed_price,
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
    seller_id: int = Query(..., description="ID of the seller responding"),
    action: NegotiationAction = Query(..., description="Action to take on negotiation"),
    counter_price: float | None = Query(None, description="New price if countering"),
    db: Session = Depends(get_db),
):
    negotiation = db.query(Negotiation).filter(Negotiation.negotiation_id == negotiation_id).first()
    if not negotiation:
        raise HTTPException(status_code=404, detail="Negotiation not found")

    if negotiation.seller_id != seller_id:
        raise HTTPException(status_code=403, detail="You can only respond to your own negotiations")

    if action == NegotiationAction.accept:
        negotiation.status = "Accepted"
        order_price = negotiation.seller_response_price or negotiation.proposed_price

        new_order = Order(
            seller_id=negotiation.seller_id,
            seller_name=negotiation.seller.name,
            buyer_id=negotiation.buyer_id,
            buyer_name=negotiation.buyer.name,
            item_id=negotiation.listing_id,
            item_name=negotiation.listing.title,
            price=order_price,
            ordered_at=datetime.utcnow(),
        )
        negotiation.listing.is_sold = True
        db.add(new_order)

    elif action == NegotiationAction.reject:
        negotiation.status = "Rejected"

    elif action == NegotiationAction.counter:
        if not counter_price:
            raise HTTPException(status_code=400, detail="Counter price required for counter offer")
        negotiation.status = "Countered"
        negotiation.seller_response_price = counter_price

    db.commit()
    db.refresh(negotiation)
    return negotiation


# View all negotiations (with optional filters)
@router.get("/", response_model=list[NegotiationResponse])
def get_negotiations(
    buyer_id: int | None = Query(None, description="Filter by buyer ID"),
    seller_id: int | None = Query(None, description="Filter by seller ID"),
    status: str | None = Query(None, description="Filter by negotiation status"),
    db: Session = Depends(get_db),
):
    query = db.query(Negotiation)
    if buyer_id:
        query = query.filter(Negotiation.buyer_id == buyer_id)
    if seller_id:
        query = query.filter(Negotiation.seller_id == seller_id)
    if status:
        query = query.filter(Negotiation.status.ilike(status))
    return query.all()

# Consumer responds to seller's counter
@router.put("/{negotiation_id}/consumer_respond", response_model=NegotiationResponse)
def consumer_respond_to_counter(
    negotiation_id: int,
    buyer_id: int = Query(..., description="ID of the Consumer responding"),
    action: NegotiationAction = Query(..., description="Accept / Reject"),
    db: Session = Depends(get_db),
):
    negotiation = db.query(Negotiation).filter(Negotiation.negotiation_id == negotiation_id).first()
    if not negotiation:
        raise HTTPException(status_code=404, detail="Negotiation not found")

    if negotiation.buyer_id != buyer_id:
        raise HTTPException(status_code=403, detail="You can only respond to your own negotiations")

    if negotiation.status != "Countered":
        raise HTTPException(status_code=400, detail="Only Countered negotiations can be responded to by the buyer")

    if action == NegotiationAction.accept:
        negotiation.status = "Accepted"
        agreed_price = negotiation.seller_response_price

        # Create order
        new_order = Order(
            seller_id=negotiation.seller_id,
            seller_name=negotiation.seller.name,
            buyer_id=negotiation.buyer_id,
            buyer_name=negotiation.buyer.name,
            item_id=negotiation.listing_id,
            item_name=negotiation.listing.title,
            price=agreed_price,
            ordered_at=datetime.utcnow(),
        )
        negotiation.listing.is_sold = True
        db.add(new_order)

    elif action == NegotiationAction.reject:
        negotiation.status = "Rejected"

    else:
        raise HTTPException(status_code=400, detail="Invalid action for buyer")

    db.commit()
    db.refresh(negotiation)
    return negotiation
