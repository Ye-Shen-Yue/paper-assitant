import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Integer, Float, DateTime, ForeignKey, JSON

from app.database import Base


def generate_uuid():
    return str(uuid.uuid4())


def utcnow():
    return datetime.now(timezone.utc)


class PaperSection(Base):
    __tablename__ = "paper_sections"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    paper_id = Column(String(36), ForeignKey("papers.id", ondelete="CASCADE"), nullable=False)
    section_type = Column(String(50), nullable=False)
    heading = Column(String(500), default="")
    content = Column(Text, default="")
    page_start = Column(Integer, default=0)
    page_end = Column(Integer, default=0)
    order = Column(Integer, default=0)

    from sqlalchemy.orm import relationship
    paper = relationship("Paper", back_populates="sections")


class PaperEntity(Base):
    __tablename__ = "paper_entities"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    paper_id = Column(String(36), ForeignKey("papers.id", ondelete="CASCADE"), nullable=False)
    section_id = Column(String(36), ForeignKey("paper_sections.id"), nullable=True)
    text = Column(String(500), nullable=False)
    entity_type = Column(String(50), nullable=False)
    start_char = Column(Integer, default=0)
    end_char = Column(Integer, default=0)
    confidence = Column(Float, default=0.0)

    from sqlalchemy.orm import relationship
    paper = relationship("Paper", back_populates="entities")


class PaperReference(Base):
    __tablename__ = "paper_references"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    paper_id = Column(String(36), ForeignKey("papers.id", ondelete="CASCADE"), nullable=False)
    raw_text = Column(Text, nullable=False)
    title = Column(String(500), nullable=True)
    authors = Column(JSON, default=list)
    year = Column(Integer, nullable=True)
    venue = Column(String(300), nullable=True)
    doi = Column(String(200), nullable=True)
    order = Column(Integer, default=0)

    from sqlalchemy.orm import relationship
    paper = relationship("Paper", back_populates="references")


class PaperTable(Base):
    __tablename__ = "paper_tables"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    paper_id = Column(String(36), ForeignKey("papers.id", ondelete="CASCADE"), nullable=False)
    section_id = Column(String(36), ForeignKey("paper_sections.id"), nullable=True)
    caption = Column(Text, default="")
    headers = Column(JSON, default=list)
    rows = Column(JSON, default=list)
    page = Column(Integer, default=0)

    from sqlalchemy.orm import relationship
    paper = relationship("Paper", back_populates="tables")


class EntityRelationship(Base):
    __tablename__ = "entity_relationships"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    paper_id = Column(String(36), ForeignKey("papers.id", ondelete="CASCADE"), nullable=False)
    source_entity_id = Column(String(36), ForeignKey("paper_entities.id"), nullable=False)
    target_entity_id = Column(String(36), ForeignKey("paper_entities.id"), nullable=False)
    relation_type = Column(String(50), nullable=False)
    description = Column(Text, default="")
    confidence = Column(Float, default=0.0)
