from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Text, Date, DateTime,
    ForeignKey, Index
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    leads = relationship("Lead", back_populates="user", cascade="all, delete-orphan")
    searches = relationship("SearchHistory", back_populates="user", cascade="all, delete-orphan")
    messages = relationship("GeneratedMessage", back_populates="user", cascade="all, delete-orphan")


class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    provider_id = Column(String(255), nullable=True)
    business_name = Column(String(255), nullable=False, index=True)
    category = Column(String(255), nullable=True)
    phone = Column(String(100), nullable=True)
    website = Column(String(500), nullable=True)
    address = Column(Text, nullable=True)
    city = Column(String(255), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    rating = Column(Float, default=0.0)
    review_count = Column(Integer, default=0)
    source = Column(String(100), default="Authorized Business API")
    source_url = Column(String(500), nullable=True)
    service = Column(String(255), nullable=False, index=True)
    lead_score = Column(Integer, default=0, index=True)
    opportunity_type = Column(String(255), nullable=True)
    opportunity_reason = Column(Text, nullable=True)
    confidence = Column(String(50), default="Moderate")
    status = Column(String(50), default="New", index=True)
    notes = Column(Text, nullable=True)
    follow_up_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="leads")
    messages = relationship("GeneratedMessage", back_populates="lead")

    __table_args__ = (
        Index("idx_leads_user_provider", "user_id", "provider_id"),
        Index("idx_leads_user_status", "user_id", "status"),
    )


class SearchHistory(Base):
    __tablename__ = "searches"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    service = Column(String(255), nullable=False)
    category = Column(String(255), nullable=False)
    location = Column(String(255), nullable=False)
    radius = Column(String(50), nullable=False)
    keywords = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="searches")

    __table_args__ = (
        Index("idx_searches_user_date", "user_id", "created_at"),
    )


class GeneratedMessage(Base):
    __tablename__ = "generated_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    lead_id = Column(Integer, ForeignKey("leads.id", ondelete="SET NULL"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="messages")
    lead = relationship("Lead", back_populates="messages")
