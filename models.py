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
    type = Column(String, nullable=False)  # "Business" or "Consumer" or "Charity"

    listings = relationship("Listing", back_populates="seller")
    buyer_orders = relationship("Order", foreign_keys="[Order.buyer_id]", back_populates="buyer")
    seller_orders = relationship("Order", foreign_keys="[Order.seller_id]", back_populates="seller")
    buyer_negotiations = relationship("Negotiation", foreign_keys="[Negotiation.buyer_id]", back_populates="buyer")
    seller_negotiations = relationship("Negotiation", foreign_keys="[Negotiation.seller_id]", back_populates="seller")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete")
    charity_profiles = relationship("CharityProfile", back_populates="user")
    donations_posted = relationship("Donation", back_populates="business", foreign_keys="Donation.business_id")


class Listing(Base):
    __tablename__ = "listings"

    item_id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String)
    cuisine = Column(String)
    price = Column(Float, nullable=False)
    city = Column(String, nullable=False)
    available_until = Column(DateTime, default=datetime.utcnow)

    # Food safety tracking
    prepared_at = Column(DateTime, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    allergens = Column(String, nullable=True)   
    photo_url = Column(String, nullable=True)

    is_sold = Column(Boolean, default=False)

    # Dynamic pricing fields
    dynamic_pricing_enabled = Column(Boolean, default=False)
    original_price = Column(Float, nullable=False)

    seller_id = Column(Integer, ForeignKey("users.user_id"))
    seller_name = Column(String, nullable=False)

    # Relationships
    seller = relationship("User", back_populates="listings")
    orders = relationship("Order", back_populates="listing")
    negotiations = relationship("Negotiation", back_populates="listing")

    def compute_dynamic_price(self, now):
        """
        Compute new price using the simple rule:
         - hours_left >= 24  => original_price
         - 12 <= hours_left < 24 => 50% of original_price
         - hours_left < 12 => 25% of original_price
        Returns the computed price (float).
        """
        try:
            total_seconds = (self.expires_at - now).total_seconds()
        except Exception:
            # If expires_at invalid, fallback to current price
            return self.price

        hours_left = total_seconds / 3600.0

        if hours_left < 0:
            # expired
            return 0.0

        if hours_left >= 24:
            return round(float(self.original_price), 2)
        if 12 <= hours_left < 24:
            return round(float(self.original_price) * 0.5, 2)
        # hours_left < 12
        return round(float(self.original_price) * 0.25, 2)


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

    buyer_proposed_price = Column(Float, nullable=False)
    seller_response_price = Column(Float, nullable=True)

    status = Column(String, default="Pending")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    listing = relationship("Listing")
    buyer = relationship("User", foreign_keys=[buyer_id])
    seller = relationship("User", foreign_keys=[seller_id])


class Notification(Base):
    __tablename__ = "notifications"

    notification_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    message = Column(String, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="notifications")


class Payment(Base):
    __tablename__ = "payments"

    payment_id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.order_id"), nullable=False)
    buyer_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    seller_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    amount = Column(Float, nullable=False)
    status = Column(String, default="success")
    created_at = Column(DateTime, default=datetime.utcnow)


class CharityProfile(Base):
    __tablename__ = "charity_profiles"

    charity_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)

    org_name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    city = Column(String, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="charity_profiles")
    donations_received = relationship("Donation", back_populates="charity", foreign_keys="Donation.charity_id")


class Donation(Base):
    __tablename__ = "donations"

    donation_id = Column(Integer, primary_key=True, index=True)

    business_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    charity_id = Column(Integer, ForeignKey("charity_profiles.charity_id"), nullable=False)

    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    cuisine = Column(String, nullable=True)
    city = Column(String, nullable=False)
    allergens = Column(String, nullable=True)
    photo_url = Column(String, nullable=True)

    available_until = Column(DateTime, nullable=True)
    prepared_at = Column(DateTime, nullable=False)
    expires_at = Column(DateTime, nullable=False)

    is_collected = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    business = relationship("User", back_populates="donations_posted", foreign_keys=[business_id])
    charity = relationship("CharityProfile", back_populates="donations_received", foreign_keys=[charity_id])
