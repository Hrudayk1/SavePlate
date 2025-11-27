from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from database import get_db
from models import Message, User
from schemas import MessageCreate, MessageResponse

router = APIRouter(prefix="/chat", tags=["Chat"])


# SEND MESSAGE
@router.post("/send", response_model=MessageResponse)
def send_message(
    message: MessageCreate,
    sender_id: int,
    receiver_id: int,
    db: Session = Depends(get_db)
):
    sender = db.query(User).filter(User.user_id == sender_id).first()
    if not sender:
        raise HTTPException(status_code=404, detail="Sender not found")

    receiver = db.query(User).filter(User.user_id == receiver_id).first()
    if not receiver:
        raise HTTPException(status_code=404, detail="Receiver not found")

    msg = Message(
        sender_id=sender_id,
        receiver_id=receiver_id,
        content=message.content,
        timestamp=datetime.utcnow()
    )

    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg


# FETCH CONVERSATION
@router.get("/conversation", response_model=list[MessageResponse])
def get_conversation(
    user1: int,
    user2: int,
    db: Session = Depends(get_db)
):
    messages = (
        db.query(Message)
        .filter(
            ((Message.sender_id == user1) & (Message.receiver_id == user2)) |
            ((Message.sender_id == user2) & (Message.receiver_id == user1))
        )
        .order_by(Message.timestamp.asc())
        .all()
    )
    return messages
