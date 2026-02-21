"""Review API endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.paper import Paper
from app.models.task import PaperReview
from app.schemas.common import TaskResponse, TaskStatusEnum
from app.schemas.review import (
    ReviewConfig, ReviewResult,
    ControversyResult, ControversyClaim,
    ReproducibilityResult, ReproducibilityItem,
)
from app.tasks.worker import create_task_record, launch_background_task
from app.services.review_service import run_review_generation

router = APIRouter()


@router.post("/{paper_id}/generate", response_model=TaskResponse)
async def trigger_review(
    paper_id: str,
    config: ReviewConfig = ReviewConfig(),
    db: Session = Depends(get_db),
):
    """Generate auto-review for a paper."""
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    task = create_task_record(db, paper_id, "review")
    launch_background_task(
        task.id, run_review_generation,
        paper_id, task.id, config.language,
    )

    return TaskResponse(task_id=task.id, status=TaskStatusEnum.PENDING, message="Review generation started")


@router.get("/{paper_id}", response_model=ReviewResult)
async def get_review(paper_id: str, db: Session = Depends(get_db)):
    """Get auto-review results."""
    review = db.query(PaperReview).filter(PaperReview.paper_id == paper_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not generated yet")

    return ReviewResult(
        paper_id=paper_id,
        summary=review.summary,
        strengths=review.strengths or [],
        weaknesses=review.weaknesses or [],
        questions_to_authors=review.questions_to_authors or [],
        overall_recommendation=review.overall_recommendation,
        confidence=review.confidence,
        generated_at=review.created_at,
    )


@router.get("/{paper_id}/controversy", response_model=ControversyResult)
async def get_controversy(paper_id: str, db: Session = Depends(get_db)):
    """Get controversy detection results."""
    review = db.query(PaperReview).filter(PaperReview.paper_id == paper_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not generated yet")

    claims = []
    for claim_data in (review.controversy_claims or []):
        claims.append(ControversyClaim(
            claim=claim_data.get("claim", ""),
            evidence_for=claim_data.get("evidence_for", []),
            evidence_against=claim_data.get("evidence_against", []),
            consistency_score=float(claim_data.get("consistency_score", 0)),
            assessment=claim_data.get("assessment", ""),
        ))

    overall = sum(c.consistency_score for c in claims) / len(claims) if claims else 0.0

    return ControversyResult(
        paper_id=paper_id,
        claims=claims,
        overall_consistency=overall,
    )


@router.get("/{paper_id}/reproducibility", response_model=ReproducibilityResult)
async def get_reproducibility(paper_id: str, db: Session = Depends(get_db)):
    """Get reproducibility checklist."""
    review = db.query(PaperReview).filter(PaperReview.paper_id == paper_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not generated yet")

    checklist = []
    for item_data in (review.reproducibility_checklist or []):
        checklist.append(ReproducibilityItem(
            criterion=item_data.get("criterion", ""),
            status=item_data.get("status", "not_met"),
            details=item_data.get("details", ""),
        ))

    return ReproducibilityResult(
        paper_id=paper_id,
        checklist=checklist,
        overall_score=review.reproducibility_score,
        summary=f"Reproducibility score: {review.reproducibility_score:.1%}",
    )
