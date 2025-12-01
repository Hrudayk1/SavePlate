from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime

from database import get_db
from models import Support, User, Order, Donation, Notification
from schemas import SupportResponse

router = APIRouter(prefix="/support", tags=["Support"])


# CREATE SUPPORT TICKET
@router.post("/create", response_model=SupportResponse)
def create_ticket(
    user_id: int = Query(..., description="User submitting the ticket"),
    reason: str = Query(..., description="Describe your issue"),
    order_id: int | None = Query(None, description="Order ID (optional)"),
    donation_id: int | None = Query(None, description="Donation ID (optional)"),
    db: Session = Depends(get_db)
):
    # Validate user
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Validate order if provided
    if order_id:
        order = db.query(Order).filter(Order.order_id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

    # Validate donation if provided
    if donation_id:
        donation = db.query(Donation).filter(Donation.donation_id == donation_id).first()
        if not donation:
            raise HTTPException(status_code=404, detail="Donation not found")

    # Create support ticket
    ticket = Support(
        user_id=user_id,
        order_id=order_id,
        donation_id=donation_id,
        reason=reason,
        submitted_at=datetime.utcnow(),
    )

    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    # Notify user
    db.add(Notification(
        user_id=user_id,
        message=f"Your support request (ID: {ticket.support_id}) has been submitted.",
        created_at=datetime.utcnow(),
    ))

    # Notify all support accounts
    support_staff = db.query(User).filter(User.type == "Support").all()
    for staff in support_staff:
        db.add(Notification(
            user_id=staff.user_id,
            message=f"New support request #{ticket.support_id} submitted by user {user_id}.",
            created_at=datetime.utcnow(),
        ))

    db.commit()

    return ticket


# GET TICKET LIST (OPTIONAL FILTER BY USER ID)
@router.get("/list", response_model=list[SupportResponse])
def list_tickets(
    user_id: int | None = Query(None, description="Filter tickets by user ID (optional)"),
    db: Session = Depends(get_db)
):
    query = db.query(Support)

    if user_id is not None:
        query = query.filter(Support.user_id == user_id)

    tickets = query.order_by(Support.submitted_at.desc()).all()
    return tickets


# RESOLVE SUPPORT TICKET
@router.post("/resolve", response_model=SupportResponse)
def resolve_ticket(
    support_user_id: int = Query(..., description="Support account resolving the ticket"),
    support_id: int = Query(..., description="Support ticket ID"),
    db: Session = Depends(get_db)
):
    # Validate support user
    support_user = db.query(User).filter(User.user_id == support_user_id).first()
    if not support_user:
        raise HTTPException(status_code=404, detail="Support user not found")

    if support_user.type != "Support":
        raise HTTPException(status_code=403, detail="Only Support accounts can resolve tickets")

    # Validate ticket
    ticket = db.query(Support).filter(Support.support_id == support_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Support ticket not found")

    if ticket.is_resolved:
        raise HTTPException(status_code=400, detail="Ticket already resolved")

    # Resolve ticket
    ticket.is_resolved = True
    ticket.resolved_at = datetime.utcnow()

    db.commit()
    db.refresh(ticket)

    # Notify ticket owner
    db.add(Notification(
        user_id=ticket.user_id,
        message=f"Your support request #{ticket.support_id} has been resolved.",
        created_at=datetime.utcnow(),
    ))

    # Notify support user
    db.add(Notification(
        user_id=support_user_id,
        message=f"You resolved support request #{ticket.support_id}.",
        created_at=datetime.utcnow(),
    ))

    db.commit()

    return ticket
