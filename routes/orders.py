from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime
from database import get_db
from models import User, Listing, Order, Notification, Payment
from schemas import OrderResponse

router = APIRouter(prefix="/orders", tags=["Orders"])


# Place order
@router.post("/place", response_model=OrderResponse)
def place_order(
    buyer_id: int = Query(..., description="ID of the Consumer placing the order"),
    listing_id: int = Query(..., description="ID of the listing being ordered"),
    db: Session = Depends(get_db),
):
    # Validate buyer
    buyer = db.query(User).filter(User.user_id == buyer_id).first()
    if not buyer:
        raise HTTPException(status_code=404, detail="Buyer not found")
    if buyer.type != "Consumer":
        raise HTTPException(status_code=403, detail="Only Consumers can place orders")

    # Validate listing
    listing = db.query(Listing).filter(Listing.item_id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    if listing.is_sold:
        raise HTTPException(status_code=400, detail="Listing already sold")

    # Validate seller
    seller = db.query(User).filter(User.user_id == listing.seller_id).first()
    if not seller:
        raise HTTPException(status_code=404, detail="Seller not found")

    # Create order
    new_order = Order(
        seller_id=seller.user_id,
        seller_name=seller.name,
        buyer_id=buyer.user_id,
        buyer_name=buyer.name,
        item_id=listing.item_id,
        item_name=listing.title,
        price=listing.price,
        ordered_at=datetime.utcnow(),
    )

    # Mark listing as sold
    listing.is_sold = True

    db.add(new_order)
    db.commit()
    db.refresh(new_order)

    # Notifications
    db.add_all([
        Notification(
            user_id=seller.user_id,
            message=f"New order placed for your listing '{listing.title}' by {buyer.name} at ₹{listing.price}",
            created_at=datetime.utcnow()
        ),
        Notification(
            user_id=buyer.user_id,
            message=f"You placed an order for '{listing.title}' from {seller.name} at ₹{listing.price}",
            created_at=datetime.utcnow()
        )
    ])
    db.commit()

    payment = db.query(Payment).filter(Payment.order_id == new_order.order_id).first()

    return OrderResponse(
        order_id=new_order.order_id,
        seller_id=new_order.seller_id,
        seller_name=new_order.seller_name,
        item_id=new_order.item_id,
        item_name=new_order.item_name,
        price=new_order.price,
        ordered_at=new_order.ordered_at,
        buyer_id=new_order.buyer_id,
        buyer_name=new_order.buyer_name,
        payment_status=True if payment else False
    )


# Get orders (buyer/seller filtering)
@router.get("/", response_model=list[OrderResponse])
def get_orders(
    buyer_id: int | None = Query(None, description="Filter by buyer ID"),
    seller_id: int | None = Query(None, description="Filter by seller ID"),
    db: Session = Depends(get_db),
):
    query = db.query(Order)

    if buyer_id:
        query = query.filter(Order.buyer_id == buyer_id)
    if seller_id:
        query = query.filter(Order.seller_id == seller_id)

    orders = query.all()
    if not orders:
        raise HTTPException(status_code=404, detail="No orders found")

    results = []

    for o in orders:
        payment = db.query(Payment).filter(Payment.order_id == o.order_id).first()

        results.append(
            OrderResponse(
                order_id=o.order_id,
                seller_id=o.seller_id,
                seller_name=o.seller_name,
                item_id=o.item_id,
                item_name=o.item_name,
                price=o.price,
                ordered_at=o.ordered_at,
                buyer_id=o.buyer_id,
                buyer_name=o.buyer_name,
                payment_status=True if payment else False
            )
        )

    return results
