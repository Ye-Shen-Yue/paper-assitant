"""Task status API endpoints."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.task import AsyncTask
from app.schemas.common import TaskStatusResponse, TaskStatusEnum

router = APIRouter()


@router.get("/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str, db: Session = Depends(get_db)):
    """Get status of an async task."""
    task = db.query(AsyncTask).filter(AsyncTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return TaskStatusResponse(
        task_id=task.id,
        paper_id=task.paper_id,
        task_type=task.task_type,
        status=TaskStatusEnum(task.status),
        progress=task.progress,
        current_step=task.current_step,
        created_at=task.created_at,
        updated_at=task.updated_at,
        error_message=task.error_message,
    )


@router.get("", response_model=list[TaskStatusResponse])
async def list_tasks(
    paper_id: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """List recent tasks."""
    query = db.query(AsyncTask)
    if paper_id:
        query = query.filter(AsyncTask.paper_id == paper_id)
    if status:
        query = query.filter(AsyncTask.status == status)

    tasks = query.order_by(AsyncTask.created_at.desc()).limit(50).all()
    return [
        TaskStatusResponse(
            task_id=t.id,
            paper_id=t.paper_id,
            task_type=t.task_type,
            status=TaskStatusEnum(t.status),
            progress=t.progress,
            current_step=t.current_step,
            created_at=t.created_at,
            updated_at=t.updated_at,
            error_message=t.error_message,
        )
        for t in tasks
    ]
