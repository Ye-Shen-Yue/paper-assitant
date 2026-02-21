"""Analysis API endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.paper import Paper
from app.models.analysis import PaperEntity, EntityRelationship
from app.models.task import PaperProfile, PaperContribution, PaperLimitation
from app.schemas.common import TaskResponse, TaskStatusEnum
from app.schemas.analysis import (
    PaperProfileSchema, DimensionScore,
    ContributionResult, ContributionSchema,
    LimitationResult, LimitationSchema,
    RelationshipSchema,
)
from app.tasks.worker import create_task_record, launch_background_task
from app.services.analysis_service import (
    run_entity_extraction,
    run_paper_profiling,
    run_contribution_extraction,
    run_limitation_identification,
)

router = APIRouter()


@router.post("/{paper_id}/entities", response_model=TaskResponse)
async def trigger_entity_extraction(paper_id: str, db: Session = Depends(get_db)):
    """Trigger entity extraction for a paper."""
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    task = create_task_record(db, paper_id, "entity_extraction")
    launch_background_task(task.id, run_entity_extraction, paper_id, task.id)

    return TaskResponse(task_id=task.id, status=TaskStatusEnum.PENDING, message="Entity extraction started")


@router.post("/{paper_id}/profile", response_model=TaskResponse)
async def trigger_profiling(paper_id: str, db: Session = Depends(get_db)):
    """Trigger paper profiling."""
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    task = create_task_record(db, paper_id, "profiling")
    launch_background_task(task.id, run_paper_profiling, paper_id, task.id)

    return TaskResponse(task_id=task.id, status=TaskStatusEnum.PENDING, message="Profiling started")


@router.get("/{paper_id}/profile", response_model=PaperProfileSchema)
async def get_profile(paper_id: str, db: Session = Depends(get_db)):
    """Get paper profile results."""
    profile = db.query(PaperProfile).filter(PaperProfile.paper_id == paper_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not generated yet")

    dimensions = []
    for dim in (profile.dimensions_detail or []):
        dimensions.append(DimensionScore(
            dimension=dim.get("dimension", ""),
            score=float(dim.get("score", 0)),
            reasoning=dim.get("reasoning", ""),
            evidence=dim.get("evidence", []),
        ))

    return PaperProfileSchema(
        paper_id=paper_id,
        dimensions=dimensions,
        overall_assessment=profile.overall_assessment,
        generated_at=profile.created_at,
    )


@router.post("/{paper_id}/contributions", response_model=TaskResponse)
async def trigger_contributions(paper_id: str, db: Session = Depends(get_db)):
    """Trigger contribution extraction."""
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    task = create_task_record(db, paper_id, "contributions")
    launch_background_task(task.id, run_contribution_extraction, paper_id, task.id)

    return TaskResponse(task_id=task.id, status=TaskStatusEnum.PENDING, message="Contribution extraction started")


@router.get("/{paper_id}/contributions", response_model=ContributionResult)
async def get_contributions(paper_id: str, db: Session = Depends(get_db)):
    """Get extracted contributions."""
    contribs = db.query(PaperContribution).filter(PaperContribution.paper_id == paper_id).all()
    if not contribs:
        raise HTTPException(status_code=404, detail="Contributions not extracted yet")

    return ContributionResult(
        paper_id=paper_id,
        contributions=[
            ContributionSchema(
                level=c.level,
                description=c.description,
                evidence=c.evidence or [],
                significance=c.significance,
            ) for c in contribs
        ],
    )


@router.post("/{paper_id}/limitations", response_model=TaskResponse)
async def trigger_limitations(paper_id: str, db: Session = Depends(get_db)):
    """Trigger limitation identification."""
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    task = create_task_record(db, paper_id, "limitations")
    launch_background_task(task.id, run_limitation_identification, paper_id, task.id)

    return TaskResponse(task_id=task.id, status=TaskStatusEnum.PENDING, message="Limitation identification started")


@router.get("/{paper_id}/limitations", response_model=LimitationResult)
async def get_limitations(paper_id: str, db: Session = Depends(get_db)):
    """Get identified limitations."""
    lims = db.query(PaperLimitation).filter(PaperLimitation.paper_id == paper_id).all()
    if not lims:
        raise HTTPException(status_code=404, detail="Limitations not identified yet")

    return LimitationResult(
        paper_id=paper_id,
        limitations=[
            LimitationSchema(
                category=l.category,
                description=l.description,
                severity=l.severity,
                suggestion=l.suggestion,
            ) for l in lims
        ],
    )


@router.get("/{paper_id}/relationships", response_model=list[RelationshipSchema])
async def get_relationships(paper_id: str, db: Session = Depends(get_db)):
    """Get extracted entity relationships."""
    rels = db.query(EntityRelationship).filter(EntityRelationship.paper_id == paper_id).all()
    result = []
    for r in rels:
        source = db.query(PaperEntity).filter(PaperEntity.id == r.source_entity_id).first()
        target = db.query(PaperEntity).filter(PaperEntity.id == r.target_entity_id).first()
        result.append(RelationshipSchema(
            source_entity_id=r.source_entity_id,
            target_entity_id=r.target_entity_id,
            source_text=source.text if source else "",
            target_text=target.text if target else "",
            relation_type=r.relation_type,
            description=r.description,
            confidence=r.confidence,
        ))
    return result
