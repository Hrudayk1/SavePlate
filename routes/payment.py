from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from database import get_db
from models import Order, Payment, Notification

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("/{order_id}/pay")
def pay_for_order(order_id: int, db: Session = Depends(get_db)):

    # Fetch order
    order = db.query(Order).filter(Order.order_id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Prevent double payment
    existing_payment = (
        db.query(Payment)
        .filter(Payment.order_id == order_id)
        .first()
    )
    if existing_payment:
        raise HTTPException(status_code=400, detail="Order already paid")

    # Create payment entry
    payment = Payment(
        order_id=order.order_id,
        buyer_id=order.buyer_id,
        seller_id=order.seller_id,
        amount=order.price,
        status="success",
        created_at=datetime.utcnow()
    )

    db.add(payment)

    # Create notifications
    notifications = [
        Notification(
            user_id=order.buyer_id,
            message=f"Payment successful for Order #{order.order_id}. Amount ₹{order.price}",
            created_at=datetime.utcnow()
        ),
        Notification(
            user_id=order.seller_id,
            message=f"Order #{order.order_id} has been paid by buyer. Amount ₹{order.price}",
            created_at=datetime.utcnow()
        )
    ]

    db.add_all(notifications)

    db.commit()
    db.refresh(payment)

    return {
        "message": "Payment recorded successfully",
        "payment_id": payment.payment_id,
        "order_id": order.order_id,
        "amount": payment.amount
    }
