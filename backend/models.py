"""
models.py — SQLAlchemy database models
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, Text, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    analyses = relationship("Analysis", back_populates="user", cascade="all, delete-orphan")
    contacts = relationship("Contact", back_populates="user", cascade="all, delete-orphan")


class Contact(Base):
    __tablename__ = "contacts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    source = Column(String(50), default="whatsapp")  # whatsapp, instagram, audio
    health_score = Column(Float, default=50.0)
    status = Column(String(50), default="Stable")  # Thriving, Stable, Declining, Dormant
    last_message_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="contacts")


class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    contact_name = Column(String(255), nullable=True)
    source = Column(String(50), default="whatsapp")
    heat_score = Column(Float, default=0)
    decay_score = Column(Float, default=0)
    emotion = Column(String(100), nullable=True)
    route = Column(String(50), nullable=True)
    report = Column(Text, nullable=True)
    nudges = Column(JSON, nullable=True)
    scoring_layers = Column(JSON, nullable=True)
    message_count = Column(Float, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="analyses")


class EpisodicMemory(Base):
    """Chronological log of all relationship events (Tier 2: Episodic Memory)."""
    __tablename__ = "episodic_memories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    contact_name = Column(String(255), nullable=False)
    event_type = Column(String(50), nullable=False)  # conflict, milestone, sentiment_shift, decay_alert, reconnection, analysis
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)


class SemanticMemory(Base):
    """Structured facts about each contact — the knowledge graph (Tier 3: Semantic Memory)."""
    __tablename__ = "semantic_memories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    contact_name = Column(String(255), nullable=False)
    fact_type = Column(String(50), nullable=False)  # career, family_member, location, preference, milestone, hobby
    fact_value = Column(Text, nullable=False)
    confidence = Column(Float, default=0.8)
    extracted_at = Column(DateTime, default=datetime.utcnow)

