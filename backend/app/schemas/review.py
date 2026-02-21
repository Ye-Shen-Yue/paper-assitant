from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class ReviewConfig(BaseModel):
    language: str = "en"
    style: str = "academic"
    include_controversy: bool = True
    include_reproducibility: bool = True


class ReviewResult(BaseModel):
    paper_id: str
    summary: str
    strengths: List[str]
    weaknesses: List[str]
    questions_to_authors: List[str]
    overall_recommendation: str
    confidence: float
    generated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ControversyClaim(BaseModel):
    claim: str
    evidence_for: List[str]
    evidence_against: List[str]
    consistency_score: float
    assessment: str


class ControversyResult(BaseModel):
    paper_id: str
    claims: List[ControversyClaim]
    overall_consistency: float


class ReproducibilityItem(BaseModel):
    criterion: str
    status: str
    details: str


class ReproducibilityResult(BaseModel):
    paper_id: str
    checklist: List[ReproducibilityItem]
    overall_score: float
    summary: str


class ComparisonRequest(BaseModel):
    paper_ids: List[str]
    aspects: List[str] = ["method", "dataset", "performance", "innovation"]


class ComparisonResult(BaseModel):
    comparison_id: str
    papers: List[dict]
    comparison_table: List[dict]
    narrative: str
    generated_at: Optional[datetime] = None
