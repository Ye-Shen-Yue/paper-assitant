"""Parsing status API endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.paper import Paper
from app.models.task import AsyncTask
from app.schemas.common import TaskResponse, TaskStatusEnum
from app.tasks.worker import create_task_record, launch_background_task
from app.services.parsing_service import run_parsing_pipeline

router = APIRouter()


@router.post("/{paper_id}/start", response_model=TaskResponse)
async def start_parsing(paper_id: str, db: Session = Depends(get_db)):
    """Trigger parsing for a paper."""
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    if paper.parsing_status == "parsing":
        raise HTTPException(status_code=409, detail="Parsing already in progress")

    # Reset status
    paper.parsing_status = "pending"
    db.commit()

    task = create_task_record(db, paper_id, "parsing")
    launch_background_task(task.id, run_parsing_pipeline, paper_id, task.id)

    return TaskResponse(
        task_id=task.id,
        status=TaskStatusEnum.PENDING,
        message="Parsing started",
    )


@router.get("/{paper_id}/status")
async def get_parsing_status(paper_id: str, db: Session = Depends(get_db)):
    """Get parsing status for a paper."""
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    # Get latest parsing task
    task = (
        db.query(AsyncTask)
        .filter(AsyncTask.paper_id == paper_id, AsyncTask.task_type == "parsing")
        .order_by(AsyncTask.created_at.desc())
        .first()
    )

    return {
        "paper_id": paper_id,
        "parsing_status": paper.parsing_status,
        "task": {
            "task_id": task.id,
            "progress": task.progress,
            "current_step": task.current_step,
            "status": task.status,
            "error_message": task.error_message,
        } if task else None,
    }
