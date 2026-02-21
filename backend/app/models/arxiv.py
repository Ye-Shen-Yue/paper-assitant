"""arXiv integration models for paper crawling and subscription management."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Integer, Float, DateTime, JSON, Boolean, ForeignKey

from app.database import Base


def generate_uuid():
    return str(uuid.uuid4())


def utcnow():
    return datetime.now(timezone.utc)


class ArxivPaper(Base):
    """Cache arXiv papers for faster access and duplicate detection."""
    __tablename__ = "arxiv_papers"

    id = Column(String(50), primary_key=True)  # arXiv ID (e.g., 2401.12345)
    title = Column(Text, nullable=False)
    authors = Column(JSON, default=list)  # List of author names
    summary = Column(Text, default="")  # Abstract
    categories = Column(JSON, default=list)  # arXiv categories like cs.CL, cs.CV
    primary_category = Column(String(50), default="")  # Main category
    published = Column(DateTime, nullable=True)  # First published date
    updated = Column(DateTime, nullable=True)  # Last updated date
    pdf_url = Column(String(500), default="")  # Direct PDF URL
    arxiv_url = Column(String(500), default="")  # arXiv abstract page URL
    doi = Column(String(200), nullable=True)  # DOI if available
    journal_ref = Column(Text, nullable=True)  # Journal reference if published
    created_at = Column(DateTime, default=utcnow)


class ArxivSubscription(Base):
    """User subscriptions for arXiv paper tracking."""
    __tablename__ = "arxiv_subscriptions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), nullable=False, index=True)
    name = Column(String(200), nullable=False)  # e.g., "NLP Latest Papers"
    keywords = Column(JSON, default=list)  # Keywords to search for
    categories = Column(JSON, default=list)  # arXiv categories like ["cs.CL", "cs.LG"]
    authors = Column(JSON, default=list)  # Specific authors to track
    max_results = Column(Integer, default=50)  # Max papers per crawl
    is_active = Column(Boolean, default=True)
    last_crawled = Column(DateTime, nullable=True)  # Last successful crawl time
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)


class ArxivPushRecord(Base):
    """Records of papers pushed to users based on their subscriptions."""
    __tablename__ = "arxiv_push_records"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), nullable=False, index=True)
    subscription_id = Column(String(36), ForeignKey("arxiv_subscriptions.id", ondelete="CASCADE"), nullable=False)
    arxiv_paper_id = Column(String(50), ForeignKey("arxiv_papers.id", ondelete="CASCADE"), nullable=False)
    match_score = Column(Float, default=0.0)  # 0-1 matching score
    is_read = Column(Boolean, default=False)  # User has read this push
    is_imported = Column(Boolean, default=False)  # Paper imported to local library
    imported_paper_id = Column(String(36), nullable=True)  # Reference to local Paper if imported
    created_at = Column(DateTime, default=utcnow)


class ArxivCrawlLog(Base):
    """Log of arXiv crawling activities."""
    __tablename__ = "arxiv_crawl_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    subscription_id = Column(String(36), ForeignKey("arxiv_subscriptions.id"), nullable=True)
    status = Column(String(20), default="running")  # running, completed, failed
    papers_found = Column(Integer, default=0)
    papers_new = Column(Integer, default=0)
    papers_pushed = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, default=utcnow)
    completed_at = Column(DateTime, nullable=True)
