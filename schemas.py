from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ListingBase(BaseModel):
    title: str
    description: Optional[str] = None
    price: float
    city: str
    available_until: Optional[datetime] = None


class ListingCreate(ListingBase):
    pass


class ListingResponse(ListingBase):
    item_id: int
    seller_id: int
    is_sold: bool

    class Config:
        from_attributes = True
