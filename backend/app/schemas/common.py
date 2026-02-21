from pydantic import BaseModel
from typing import Generic, TypeVar, Optional, List
from datetime import datetime
from enum import Enum

T = TypeVar("T")


class TaskStatusEnum(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    per_page: int
    total_pages: int


class TaskResponse(BaseModel):
    task_id: str
    status: TaskStatusEnum
    message: str


class TaskStatusResponse(BaseModel):
    task_id: str
    paper_id: str
    task_type: str
    status: TaskStatusEnum
    progress: float
    current_step: str
    created_at: datetime
    updated_at: datetime
    error_message: Optional[str] = None


class ErrorResponse(BaseModel):
    detail: str
    error_code: str
