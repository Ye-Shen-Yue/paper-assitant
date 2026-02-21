import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Integer, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship

from app.database import Base


def generate_uuid():
    return str(uuid.uuid4())


def utcnow():
    return datetime.now(timezone.utc)


class Paper(Base):
    __tablename__ = "papers"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    title = Column(String(500), nullable=False, default="Untitled")
    authors = Column(JSON, default=list)
    abstract = Column(Text, default="")
    language = Column(String(10), default="en")
    doi = Column(String(200), nullable=True)
    venue = Column(String(300), nullable=True)
    year = Column(Integer, nullable=True)
    keywords = Column(JSON, default=list)

    pdf_path = Column(String(500), nullable=False)
    file_size = Column(Integer, default=0)
    page_count = Column(Integer, default=0)

    parsing_status = Column(String(20), default="pending")

    upload_date = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    sections = relationship("PaperSection", back_populates="paper", cascade="all, delete-orphan")
    entities = relationship("PaperEntity", back_populates="paper", cascade="all, delete-orphan")
    references = relationship("PaperReference", back_populates="paper", cascade="all, delete-orphan")
    tables = relationship("PaperTable", back_populates="paper", cascade="all, delete-orphan")
