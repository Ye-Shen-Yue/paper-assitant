"""Chat API endpoints for AI assistant."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional, Literal

from app.database import get_db
from app.models.paper import Paper
from app.services.chat_service import ChatService

router = APIRouter()


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    message: str
    history: Optional[List[ChatMessage]] = []
    selected_text: Optional[str] = None
    language: Optional[str] = "en"


class ChatResponse(BaseModel):
    response: str


class QuickActionRequest(BaseModel):
    action: Literal["summarize", "translate", "explain", "critique"]
    text: Optional[str] = None
    target_language: Optional[str] = "zh"


@router.post("/{paper_id}/chat", response_model=ChatResponse)
async def chat_with_paper(
    paper_id: str,
    request: ChatRequest,
    db: Session = Depends(get_db),
):
    """Chat with AI assistant about a specific paper."""
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    chat_service = ChatService(db)
    response = chat_service.chat(
        paper=paper,
        message=request.message,
        history=[msg.model_dump() for msg in (request.history or [])],
        selected_text=request.selected_text,
        language=request.language or "en",
    )

    return ChatResponse(response=response)


@router.post("/{paper_id}/quick-action", response_model=ChatResponse)
async def quick_action(
    paper_id: str,
    request: QuickActionRequest,
    db: Session = Depends(get_db),
):
    """Perform quick actions like summarize, translate, explain, or critique."""
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    chat_service = ChatService(db)

    if request.action == "summarize":
        response = chat_service.summarize(paper, language="zh" if request.target_language == "zh" else "en")
    elif request.action == "translate":
        text = request.text or paper.abstract or ""
        response = chat_service.translate(text, request.target_language or "zh")
    elif request.action == "explain":
        text = request.text or paper.abstract or ""
        context = f"Paper: {paper.title}"
        response = chat_service.explain(text, context, language="zh" if request.target_language == "zh" else "en")
    elif request.action == "critique":
        response = chat_service.critique(paper, language="zh" if request.target_language == "zh" else "en")
    else:
        raise HTTPException(status_code=400, detail="Invalid action")

    return ChatResponse(response=response)
