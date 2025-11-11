from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ListingBase(BaseModel):
    title: str
    description: Optional[str] = None
    cuisine: Optional[str] = None
    price: float
    city: str
    available_until: Optional[datetime] = None


class ListingCreate(ListingBase):
    pass


class ListingResponse(ListingBase):
    item_id: int
    seller_name: str
    is_sold: bool

    class Config:
        from_attributes = True

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

    class Config:
        from_attributes = True

