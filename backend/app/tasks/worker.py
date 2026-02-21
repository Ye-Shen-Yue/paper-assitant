import asyncio
import uuid
from datetime import datetime, timezone
from typing import Dict, Callable, Awaitable
from concurrent.futures import ThreadPoolExecutor

from sqlalchemy.orm import Session
from app.models.task import AsyncTask
from app.database import SessionLocal


# In-memory task registry for tracking running tasks
_running_tasks: Dict[str, asyncio.Task] = {}
_executor = ThreadPoolExecutor(max_workers=4)


def get_new_db() -> Session:
    """Create a new database session for background tasks."""
    return SessionLocal()


def create_task_record(db: Session, paper_id: str, task_type: str) -> AsyncTask:
    """Create a new task record in the database."""
    task = AsyncTask(
        id=str(uuid.uuid4()),
        paper_id=paper_id,
        task_type=task_type,
        status="pending",
        progress=0.0,
        current_step="Queued",
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def update_task_progress(
    db: Session, task_id: str, progress: float, current_step: str, status: str = "running"
):
    """Update task progress."""
    task = db.query(AsyncTask).filter(AsyncTask.id == task_id).first()
    if task:
        task.progress = progress
        task.current_step = current_step
        task.status = status
        task.updated_at = datetime.now(timezone.utc)
        db.commit()


def complete_task(db: Session, task_id: str, result: dict = None):
    """Mark task as completed."""
    task = db.query(AsyncTask).filter(AsyncTask.id == task_id).first()
    if task:
        task.status = "completed"
        task.progress = 1.0
        task.current_step = "Done"
        task.result = result
        task.updated_at = datetime.now(timezone.utc)
        db.commit()


def fail_task(db: Session, task_id: str, error_message: str):
    """Mark task as failed."""
    task = db.query(AsyncTask).filter(AsyncTask.id == task_id).first()
    if task:
        task.status = "failed"
        task.current_step = "Failed"
        task.error_message = error_message
        task.updated_at = datetime.now(timezone.utc)
        db.commit()


def launch_background_task(
    task_id: str,
    sync_func: Callable,
    *args,
    **kwargs,
):
    """Launch a background task that runs a sync function in a thread pool.

    The sync_func should NOT receive a db session - it should create its own
    using get_new_db(). The first arg should be paper_id, second should be task_id.
    """
    async def _wrapper():
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(_executor, lambda: sync_func(*args, **kwargs))
        except Exception as e:
            print(f"Background task {task_id} failed: {e}")
            import traceback
            traceback.print_exc()
        finally:
            _running_tasks.pop(task_id, None)

    loop = asyncio.get_event_loop()
    async_task = loop.create_task(_wrapper())
    _running_tasks[task_id] = async_task
    return async_task
