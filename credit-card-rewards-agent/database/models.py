"""
SQLAlchemy ORM models for the structured side of the system.

These mirror the tables described in the capstone spec:
  - card_documents
  - reward_rules
  - transfer_partners
  - user_profiles
  - recommendation_logs

Unstructured PDF/text chunks + embeddings live in Chroma (see rag/ingest_docs.py),
not in these SQL tables, per the "unstructured vs structured" split in the spec.
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey
)
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class CardDocument(Base):
    __tablename__ = "card_documents"

    document_id = Column(Integer, primary_key=True, autoincrement=True)
    card_name = Column(String(120), nullable=False)
    issuer = Column(String(120))
    document_type = Column(String(120))
    effective_date = Column(String(20))
    source_path = Column(String(500))
    uploaded_at = Column(DateTime, default=datetime.utcnow)


class RewardRule(Base):
    """Structured, extracted reward rule -- used by the calculator tool so
    that math doesn't depend on the LLM re-deriving numbers from raw text."""
    __tablename__ = "reward_rules"

    rule_id = Column(Integer, primary_key=True, autoincrement=True)
    card_name = Column(String(120), nullable=False)
    spend_category = Column(String(80), nullable=False)  # flights, hotels, dining, groceries, utilities, rent, insurance, wallet, fuel, international, other
    reward_type = Column(String(40), nullable=False)      # points | cashback
    reward_rate = Column(Float, nullable=False)           # numeric rate
    reward_unit = Column(String(80), nullable=False)      # e.g. "points_per_100_inr" or "percent_cashback"
    monthly_cap = Column(Float, nullable=True)            # cap value in reward units (points or INR), null = no cap
    annual_cap = Column(Float, nullable=True)
    exclusion_flag = Column(Boolean, default=False)       # True = category is excluded / heavily reduced
    milestone_condition = Column(Text, nullable=True)
    source_document = Column(String(120))
    confidence_score = Column(Float, default=0.9)


class TransferPartner(Base):
    __tablename__ = "transfer_partners"

    partner_id = Column(Integer, primary_key=True, autoincrement=True)
    card_name = Column(String(120), nullable=False)
    partner_name = Column(String(120), nullable=False)
    partner_type = Column(String(40))          # airline | hotel
    transfer_ratio_points = Column(Float)       # X card points
    transfer_ratio_partner_units = Column(Float)  # = Y partner units
    minimum_points = Column(Float)
    maximum_points = Column(Float)
    effective_date = Column(String(20))
    source_document = Column(String(120))


class UserProfile(Base):
    __tablename__ = "user_profiles"

    user_id = Column(String(80), primary_key=True)
    cards_owned = Column(Text)              # comma-separated card names
    preferred_reward_type = Column(String(40))  # cashback | airline_miles | hotel_points
    point_valuation = Column(Float, default=1.0)  # INR per point, user-defined assumption
    monthly_spend_pattern = Column(Text)     # JSON string
    preferred_partners = Column(Text)
    conversation_summary = Column(Text)


class RecommendationLog(Base):
    """Monitoring / observability table -- one row per agent turn."""
    __tablename__ = "recommendation_logs"

    query_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(80))
    query_text = Column(Text)
    intent = Column(String(60))
    retrieved_chunks_summary = Column(Text)
    recommended_card = Column(String(120))
    estimated_value = Column(Float)
    confidence_score = Column(String(20))
    guardrail_flags = Column(Text)
    latency_ms = Column(Float)
    token_usage = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
