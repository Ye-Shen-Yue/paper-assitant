import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Integer, Float, DateTime, JSON

from app.database import Base


def generate_uuid():
    return str(uuid.uuid4())


def utcnow():
    return datetime.now(timezone.utc)


class AsyncTask(Base):
    __tablename__ = "async_tasks"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    paper_id = Column(String(36), nullable=True)  # Nullable for non-paper tasks like arxiv_crawl
    task_type = Column(String(50), nullable=False)  # parsing, analysis, review, comparison, arxiv_crawl
    status = Column(String(20), default="pending")   # pending, running, completed, failed
    progress = Column(Float, default=0.0)
    current_step = Column(String(200), default="")
    result = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)


class PaperProfile(Base):
    __tablename__ = "paper_profiles"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    paper_id = Column(String(36), nullable=False, unique=True)
    innovation_score = Column(Float, default=0.0)
    method_complexity_score = Column(Float, default=0.0)
    experiment_sufficiency_score = Column(Float, default=0.0)
    reproducibility_score = Column(Float, default=0.0)
    impact_prediction_score = Column(Float, default=0.0)
    overall_assessment = Column(Text, default="")
    dimensions_detail = Column(JSON, default=list)  # Full detail with reasoning
    created_at = Column(DateTime, default=utcnow)


class PaperReview(Base):
    __tablename__ = "paper_reviews"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    paper_id = Column(String(36), nullable=False, unique=True)
    summary = Column(Text, default="")
    strengths = Column(JSON, default=list)
    weaknesses = Column(JSON, default=list)
    questions_to_authors = Column(JSON, default=list)
    overall_recommendation = Column(String(50), default="")
    confidence = Column(Float, default=0.0)
    controversy_claims = Column(JSON, default=list)
    reproducibility_checklist = Column(JSON, default=list)
    reproducibility_score = Column(Float, default=0.0)
    created_at = Column(DateTime, default=utcnow)


class PaperContribution(Base):
    __tablename__ = "paper_contributions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    paper_id = Column(String(36), nullable=False)
    level = Column(String(50), nullable=False)  # theoretical, technical, application
    description = Column(Text, default="")
    evidence = Column(JSON, default=list)
    significance = Column(String(20), default="moderate")


class PaperLimitation(Base):
    __tablename__ = "paper_limitations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    paper_id = Column(String(36), nullable=False)
    category = Column(String(100), nullable=False)
    description = Column(Text, default="")
    severity = Column(String(20), default="minor")
    suggestion = Column(Text, default="")
