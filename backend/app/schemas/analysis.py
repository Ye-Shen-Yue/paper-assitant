from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class DimensionScore(BaseModel):
    dimension: str
    score: float
    reasoning: str
    evidence: List[str]


class PaperProfileSchema(BaseModel):
    paper_id: str
    dimensions: List[DimensionScore]
    overall_assessment: str
    generated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ContributionSchema(BaseModel):
    level: str
    description: str
    evidence: List[str]
    significance: str


class ContributionResult(BaseModel):
    paper_id: str
    contributions: List[ContributionSchema]
    summary: str = ""


class LimitationSchema(BaseModel):
    category: str
    description: str
    severity: str
    suggestion: str


class LimitationResult(BaseModel):
    paper_id: str
    limitations: List[LimitationSchema]
    summary: str = ""


class RelationshipSchema(BaseModel):
    source_entity_id: str
    target_entity_id: str
    source_text: str = ""
    target_text: str = ""
    relation_type: str
    description: str
    confidence: float

    class Config:
        from_attributes = True
