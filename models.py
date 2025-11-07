from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    type = Column(String, nullable=False)  # "Business" or "Consumer"

    listings = relationship("Listing", back_populates="seller")


class Listing(Base):
    __tablename__ = "listings"

    item_id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String)
    cuisine = Column(String)
    price = Column(Float, nullable=False)
    city = Column(String, nullable=False)
    available_until = Column(DateTime, default=datetime.utcnow)
    is_sold = Column(Boolean, default=False)

    seller_id = Column(Integer, ForeignKey("users.user_id"))
    seller_name = Column(String, nullable=False)
    seller = relationship("User", back_populates="listings")
