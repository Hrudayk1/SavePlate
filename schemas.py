from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from enum import Enum


class NegotiationStatus(str, Enum):
    pending = "Pending"
    buyer_countered = "BuyerCountered"
    seller_countered = "SellerCountered"
    accepted = "Accepted"
    rejected = "Rejected"


class NegotiationAction(str, Enum):
    accept = "Accept"
    reject = "Reject"
    counter = "Counter"


#  LISTINGS 
class ListingBase(BaseModel):
    title: str
    description: Optional[str] = None
    cuisine: Optional[str] = None
    price: float
    city: str
    available_until: Optional[datetime] = None

    # FOOD SAFETY FIELDS
    prepared_at: datetime
    expires_at: datetime
    allergens: Optional[str] = None
    photo_url: Optional[str] = None

    dynamic_pricing_enabled: Optional[bool] = False

class ListingCreate(ListingBase):
    pass


class ListingResponse(ListingBase):
    item_id: int
    seller_name: str
    is_sold: bool
    original_price: float

    class Config:
        from_attributes = True

#  ORDERS 
class OrderResponse(BaseModel):
    order_id: int
    seller_id: int
    seller_name: str
    item_id: int
    item_name: str
    price: float
    ordered_at: datetime
    buyer_id: int
    buyer_name: str
    payment_status: Optional[bool] = None

    class Config:
        from_attributes = True

#  NEGOTIATIONS 
class NegotiationBase(BaseModel):
    listing_id: int
    buyer_id: int
    buyer_proposed_price: float

class NegotiationResponse(BaseModel):
    negotiation_id: int
    listing_id: int
    buyer_id: int
    seller_id: int
    buyer_proposed_price: Optional[float] = None
    seller_response_price: Optional[float] = None
    status: NegotiationStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class SellerResponseIn(BaseModel):
    seller_id: int
    action: NegotiationAction
    counter_price: Optional[float] = None

class BuyerResponseIn(BaseModel):
    buyer_id: int
    action: NegotiationAction
    counter_price: Optional[float] = None

#  NOTIFICATIONS 
class NotificationBase(BaseModel):
    message: str

class NotificationCreate(NotificationBase):
    user_id: int

class NotificationResponse(NotificationBase):
    notification_id: int
    user_id: int
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True
        
#  PAYMENT 
class PaymentCreate(BaseModel):
    order_id: int


class PaymentResponse(BaseModel):
    payment_id: int
    order_id: int
    paid: bool
    paid_at: datetime

    class Config:
        from_attributes = True
