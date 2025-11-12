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
    buyer_orders = relationship("Order", foreign_keys="[Order.buyer_id]", back_populates="buyer")
    seller_orders = relationship("Order", foreign_keys="[Order.seller_id]", back_populates="seller")
    buyer_negotiations = relationship("Negotiation", foreign_keys="[Negotiation.buyer_id]", back_populates="buyer")
    seller_negotiations = relationship("Negotiation", foreign_keys="[Negotiation.seller_id]", back_populates="seller")


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

    # Relationships
    seller = relationship("User", back_populates="listings")
    orders = relationship("Order", back_populates="listing")
    negotiations = relationship("Negotiation", back_populates="listing")


class Order(Base):
    __tablename__ = "orders"

    order_id = Column(Integer, primary_key=True, index=True)
    seller_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    seller_name = Column(String, nullable=False)
    buyer_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    buyer_name = Column(String, nullable=False)
    item_id = Column(Integer, ForeignKey("listings.item_id"), nullable=False)
    item_name = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    ordered_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    listing = relationship("Listing", back_populates="orders")
    buyer = relationship("User", foreign_keys=[buyer_id], back_populates="buyer_orders")
    seller = relationship("User", foreign_keys=[seller_id], back_populates="seller_orders")


class Negotiation(Base):
    __tablename__ = "negotiations"

    negotiation_id = Column(Integer, primary_key=True, index=True)
    listing_id = Column(Integer, ForeignKey("listings.item_id"), nullable=False)
    buyer_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    seller_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)

    proposed_price = Column(Float, nullable=False)
    seller_response_price = Column(Float, nullable=True)
    status = Column(String, default="Pending")  # "Pending", "Accepted", "Rejected", "Countered"

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    listing = relationship("Listing", back_populates="negotiations")
    buyer = relationship("User", foreign_keys=[buyer_id], back_populates="buyer_negotiations")
    seller = relationship("User", foreign_keys=[seller_id], back_populates="seller_negotiations")
