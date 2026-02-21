"""Paper CRUD API endpoints."""
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.paper import Paper
from app.models.analysis import PaperSection, PaperEntity, PaperReference, PaperTable
from app.models.task import AsyncTask
from app.schemas.paper import (
    PaperSummary, PaperDetail, PaperSectionSchema,
    PaperEntitySchema, ReferenceSchema, ExtractedTableSchema, PaperCreateResponse,
)
from app.schemas.common import PaginatedResponse, TaskResponse, TaskStatusEnum
from app.utils.file_utils import save_upload_file, get_file_size, delete_file
from app.config import settings
from app.tasks.worker import create_task_record, launch_background_task
from app.services.parsing_service import run_parsing_pipeline

router = APIRouter()


@router.post("/upload", response_model=PaperCreateResponse)
async def upload_paper(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Upload a PDF paper and trigger parsing."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    # Save file
    file_path = await save_upload_file(file, settings.upload_dir)
    file_size = get_file_size(file_path)

    # Create paper record
    paper = Paper(
        id=str(uuid.uuid4()),
        title=file.filename.replace(".pdf", ""),
        pdf_path=file_path,
        file_size=file_size,
        parsing_status="pending",
    )
    db.add(paper)
    db.commit()
    db.refresh(paper)

    # Create and launch parsing task
    task = create_task_record(db, paper.id, "parsing")
    launch_background_task(
        task.id,
        run_parsing_pipeline,
        paper.id, task.id,
    )

    return PaperCreateResponse(
        paper_id=paper.id,
        task_id=task.id,
        message="Paper uploaded successfully. Parsing started.",
    )


@router.get("", response_model=PaginatedResponse[PaperSummary])
async def list_papers(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """List all uploaded papers with pagination."""
    from sqlalchemy.orm import lazyload

    # Use lazy loading to avoid loading relationships
    query = db.query(Paper).options(lazyload('*'))

    if search:
        query = query.filter(
            Paper.title.ilike(f"%{search}%") | Paper.abstract.ilike(f"%{search}%")
        )

    # Get total count efficiently
    total = query.count()

    # Get paginated results
    papers = query.order_by(Paper.upload_date.desc()).offset((page - 1) * per_page).limit(per_page).all()

    return PaginatedResponse(
        items=[PaperSummary.model_validate(p) for p in papers],
        total=total,
        page=page,
        per_page=per_page,
        total_pages=(total + per_page - 1) // per_page,
    )


@router.get("/{paper_id}", response_model=PaperDetail)
async def get_paper(paper_id: str, db: Session = Depends(get_db)):
    """Get detailed paper information."""
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    return PaperDetail.model_validate(paper)


@router.delete("/{paper_id}")
async def delete_paper(paper_id: str, db: Session = Depends(get_db)):
    """Delete a paper and all associated data."""
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    delete_file(paper.pdf_path)
    db.delete(paper)
    db.commit()
    return {"ok": True}


@router.post("/{paper_id}/reparse", response_model=TaskResponse)
async def reparse_paper(paper_id: str, db: Session = Depends(get_db)):
    """Re-trigger parsing for an existing paper (clears old sections/entities)."""
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    # Clear old parsed data
    from app.models.analysis import EntityRelationship
    db.query(EntityRelationship).filter(EntityRelationship.paper_id == paper_id).delete()
    db.query(PaperEntity).filter(PaperEntity.paper_id == paper_id).delete()
    db.query(PaperSection).filter(PaperSection.paper_id == paper_id).delete()
    db.query(PaperReference).filter(PaperReference.paper_id == paper_id).delete()
    db.query(PaperTable).filter(PaperTable.paper_id == paper_id).delete()
    paper.parsing_status = "pending"
    db.commit()

    task = create_task_record(db, paper.id, "parsing")
    launch_background_task(task.id, run_parsing_pipeline, paper.id, task.id)

    return TaskResponse(task_id=task.id, status=TaskStatusEnum.pending, message="Re-parsing started")


@router.get("/{paper_id}/sections", response_model=list[PaperSectionSchema])
async def get_sections(paper_id: str, db: Session = Depends(get_db)):
    """Get parsed sections of a paper."""
    sections = (
        db.query(PaperSection)
        .filter(PaperSection.paper_id == paper_id)
        .order_by(PaperSection.order)
        .all()
    )
    return [PaperSectionSchema.model_validate(s) for s in sections]


@router.get("/{paper_id}/entities", response_model=list[PaperEntitySchema])
async def get_entities(
    paper_id: str,
    entity_type: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Get recognized entities of a paper."""
    query = db.query(PaperEntity).filter(PaperEntity.paper_id == paper_id)
    if entity_type:
        query = query.filter(PaperEntity.entity_type == entity_type)
    entities = query.all()
    return [PaperEntitySchema.model_validate(e) for e in entities]


@router.get("/{paper_id}/references", response_model=list[ReferenceSchema])
async def get_references(paper_id: str, db: Session = Depends(get_db)):
    """Get parsed references of a paper."""
    refs = (
        db.query(PaperReference)
        .filter(PaperReference.paper_id == paper_id)
        .order_by(PaperReference.order)
        .all()
    )
    return [ReferenceSchema.model_validate(r) for r in refs]


@router.get("/{paper_id}/tables", response_model=list[ExtractedTableSchema])
async def get_tables(paper_id: str, db: Session = Depends(get_db)):
    """Get extracted tables from a paper."""
    tables = db.query(PaperTable).filter(PaperTable.paper_id == paper_id).all()
    return [ExtractedTableSchema.model_validate(t) for t in tables]
