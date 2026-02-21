"""Recommendation system models for user profiling and activity tracking."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Integer, Float, DateTime, JSON, ForeignKey

from app.database import Base


def generate_uuid():
    return str(uuid.uuid4())


def utcnow():
    return datetime.now(timezone.utc)


class UserActivity(Base):
    """Track user interactions with papers for building user profile."""
    __tablename__ = "user_activities"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), nullable=False, index=True)  # Local storage based user ID
    paper_id = Column(String(36), ForeignKey("papers.id", ondelete="CASCADE"), nullable=False)
    activity_type = Column(String(50), nullable=False)  # 'view', 'chat', 'note', 'export', 'save', 'scroll', 'click'
    duration_seconds = Column(Integer, default=0)  # Time spent on activity
    created_at = Column(DateTime, default=utcnow)
    meta_info = Column(JSON, default=dict)  # Additional context like scroll_depth, reading_mode


class PaperEmbedding(Base):
    """Store vector embeddings for papers to enable similarity search."""
    __tablename__ = "paper_embeddings"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    paper_id = Column(String(36), ForeignKey("papers.id", ondelete="CASCADE"), nullable=False, unique=True)
    embedding = Column(JSON, default=list)  # 1536-dimensional vector as JSON array
    keywords = Column(JSON, default=list)  # Extracted keywords from paper
    topics = Column(JSON, default=list)  # Topic classification (e.g., ['NLP', 'LLM'])
    model_name = Column(String(100), default="text-embedding-3-small")  # Which embedding model used
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)


class UserProfile(Base):
    """Cache user research profile for faster recommendation queries."""
    __tablename__ = "user_profiles"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), nullable=False, unique=True)
    topic_distribution = Column(JSON, default=dict)  # {"NLP": 0.4, "CV": 0.3, ...}
    method_preferences = Column(JSON, default=list)  # ["Transformer", "LLM", ...]
    profile_embedding = Column(JSON, default=list)  # User profile as vector
    reading_pattern = Column(String(50), default="browser")  # 'browser' or 'researcher'
    total_papers_read = Column(Integer, default=0)
    total_reading_time = Column(Integer, default=0)  # In seconds
    streak_days = Column(Integer, default=0)  # Consecutive reading days
    last_read_papers = Column(JSON, default=list)  # List of recently read paper IDs
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)


class UserCollection(Base):
    """User-created collections of papers."""
    __tablename__ = "user_collections"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, default="")
    paper_ids = Column(JSON, default=list)  # List of paper IDs in collection
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)


class RecommendationLog(Base):
    """Track recommendation performance for algorithm improvement."""
    __tablename__ = "recommendation_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), nullable=False, index=True)
    paper_id = Column(String(36), ForeignKey("papers.id", ondelete="CASCADE"), nullable=False)
    recommendation_type = Column(String(50), nullable=False)  # 'content_based', 'collaborative', 'trending'
    score = Column(Float, default=0.0)  # Similarity score
    clicked = Column(Integer, default=0)  # 0 or 1
    rated = Column(Integer, nullable=True)  # User rating 1-5
    created_at = Column(DateTime, default=utcnow)
