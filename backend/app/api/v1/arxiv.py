"""arXiv integration API endpoints for subscriptions and paper pushing."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db
from app.models.arxiv import ArxivPaper, ArxivSubscription, ArxivPushRecord, ArxivCrawlLog
from app.models.paper import Paper
from app.services.arxiv_service import get_arxiv_service, ARXIV_CATEGORIES
from app.tasks.worker import create_task_record, launch_background_task
from app.services.arxiv_crawler import run_arxiv_crawl

router = APIRouter()


# ========== Schemas ==========

class ArxivSubscriptionCreate(BaseModel):
    user_id: str
    name: str = Field(..., min_length=1, max_length=200)
    keywords: List[str] = []
    categories: List[str] = []
    authors: List[str] = []
    max_results: int = Field(default=50, ge=1, le=200)


class ArxivSubscriptionUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    keywords: Optional[List[str]] = None
    categories: Optional[List[str]] = None
    authors: Optional[List[str]] = None
    max_results: Optional[int] = Field(None, ge=1, le=200)
    is_active: Optional[bool] = None


class ArxivSubscriptionResponse(BaseModel):
    id: str
    user_id: str
    name: str
    keywords: List[str]
    categories: List[str]
    authors: List[str]
    max_results: int
    is_active: bool
    last_crawled: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class ArxivPaperResponse(BaseModel):
    id: str
    title: str
    authors: List[str]
    summary: str
    categories: List[str]
    primary_category: str
    published: Optional[datetime]
    pdf_url: str
    arxiv_url: str


class ArxivPushRecordResponse(BaseModel):
    id: str
    user_id: str
    subscription_id: str
    arxiv_paper: ArxivPaperResponse
    match_score: float
    is_read: bool
    is_imported: bool
    imported_paper_id: Optional[str]
    created_at: datetime


class ArxivSearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    max_results: int = Field(default=20, ge=1, le=100)


class ArxivImportRequest(BaseModel):
    arxiv_id: str
    user_id: str


class ArxivCategoryInfo(BaseModel):
    code: str
    name: str


# ========== Subscription Management ==========

@router.post("/subscriptions", response_model=ArxivSubscriptionResponse)
async def create_subscription(
    request: ArxivSubscriptionCreate,
    db: Session = Depends(get_db),
):
    """Create a new arXiv subscription."""
    subscription = ArxivSubscription(
        user_id=request.user_id,
        name=request.name,
        keywords=request.keywords or [],
        categories=request.categories or [],
        authors=request.authors or [],
        max_results=request.max_results,
        is_active=True,
    )
    db.add(subscription)
    db.commit()
    db.refresh(subscription)
    return subscription


@router.get("/subscriptions/{user_id}", response_model=List[ArxivSubscriptionResponse])
async def list_subscriptions(
    user_id: str,
    db: Session = Depends(get_db),
):
    """List all subscriptions for a user."""
    subscriptions = (
        db.query(ArxivSubscription)
        .filter(ArxivSubscription.user_id == user_id)
        .order_by(ArxivSubscription.created_at.desc())
        .all()
    )
    return subscriptions


@router.get("/subscriptions/detail/{subscription_id}", response_model=ArxivSubscriptionResponse)
async def get_subscription(
    subscription_id: str,
    db: Session = Depends(get_db),
):
    """Get a specific subscription."""
    subscription = db.query(ArxivSubscription).filter(
        ArxivSubscription.id == subscription_id
    ).first()
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return subscription


@router.put("/subscriptions/{subscription_id}", response_model=ArxivSubscriptionResponse)
async def update_subscription(
    subscription_id: str,
    request: ArxivSubscriptionUpdate,
    db: Session = Depends(get_db),
):
    """Update a subscription."""
    subscription = db.query(ArxivSubscription).filter(
        ArxivSubscription.id == subscription_id
    ).first()
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")

    if request.name is not None:
        subscription.name = request.name
    if request.keywords is not None:
        subscription.keywords = request.keywords
    if request.categories is not None:
        subscription.categories = request.categories
    if request.authors is not None:
        subscription.authors = request.authors
    if request.max_results is not None:
        subscription.max_results = request.max_results
    if request.is_active is not None:
        subscription.is_active = request.is_active

    db.commit()
    db.refresh(subscription)
    return subscription


@router.delete("/subscriptions/{subscription_id}")
async def delete_subscription(
    subscription_id: str,
    db: Session = Depends(get_db),
):
    """Delete a subscription."""
    subscription = db.query(ArxivSubscription).filter(
        ArxivSubscription.id == subscription_id
    ).first()
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")

    db.delete(subscription)
    db.commit()
    return {"success": True, "message": "Subscription deleted"}


# ========== Direct arXiv Search ==========

@router.post("/search")
async def search_arxiv(
    request: ArxivSearchRequest,
    db: Session = Depends(get_db),
):
    """Direct search on arXiv."""
    arxiv = get_arxiv_service()
    papers = arxiv.search_papers(
        query=request.query,
        max_results=request.max_results,
        sort_by="submittedDate",
        sort_order="descending",
    )

    # Cache papers in database
    for paper in papers:
        existing = db.query(ArxivPaper).filter(ArxivPaper.id == paper.id).first()
        if not existing:
            db.add(paper)

    if papers:
        db.commit()

    return {
        "total": len(papers),
        "papers": [
            {
                "id": p.id,
                "title": p.title,
                "authors": p.authors,
                "summary": p.summary,
                "categories": p.categories,
                "primary_category": p.primary_category,
                "published": p.published,
                "pdf_url": p.pdf_url,
                "arxiv_url": p.arxiv_url,
            }
            for p in papers
        ],
    }


@router.get("/search/advanced")
async def advanced_search(
    keywords: Optional[str] = None,
    categories: Optional[str] = None,
    authors: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    max_results: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Advanced search with multiple criteria."""
    # Parse parameters
    keyword_list = [k.strip() for k in keywords.split(",") if k.strip()] if keywords else None
    category_list = [c.strip() for c in categories.split(",") if c.strip()] if categories else None
    author_list = [a.strip() for a in authors.split(",") if a.strip()] if authors else None

    date_from_dt = datetime.strptime(date_from, "%Y-%m-%d") if date_from else None
    date_to_dt = datetime.strptime(date_to, "%Y-%m-%d") if date_to else None

    # Build query
    query = get_arxiv_service().build_query(
        keywords=keyword_list,
        categories=category_list,
        authors=author_list,
        date_from=date_from_dt,
        date_to=date_to_dt,
    )

    # Search
    arxiv = get_arxiv_service()
    papers = arxiv.search_papers(query, max_results=max_results)

    # Cache papers
    for paper in papers:
        existing = db.query(ArxivPaper).filter(ArxivPaper.id == paper.id).first()
        if not existing:
            db.add(paper)

    if papers:
        db.commit()

    return {
        "query": query,
        "total": len(papers),
        "papers": [
            {
                "id": p.id,
                "title": p.title,
                "authors": p.authors,
                "summary": p.summary,
                "categories": p.categories,
                "primary_category": p.primary_category,
                "published": p.published,
                "pdf_url": p.pdf_url,
                "arxiv_url": p.arxiv_url,
            }
            for p in papers
        ],
    }


# ========== Push Management ==========

@router.get("/pushes/{user_id}")
async def get_user_pushes(
    user_id: str,
    unread_only: bool = Query(default=False),
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Get papers pushed to user."""
    query = db.query(ArxivPushRecord).filter(ArxivPushRecord.user_id == user_id)

    if unread_only:
        query = query.filter(ArxivPushRecord.is_read == False)

    pushes = query.order_by(ArxivPushRecord.created_at.desc()).limit(limit).all()

    result = []
    for push in pushes:
        paper = db.query(ArxivPaper).filter(ArxivPaper.id == push.arxiv_paper_id).first()
        if paper:
            result.append({
                "id": push.id,
                "user_id": push.user_id,
                "subscription_id": push.subscription_id,
                "arxiv_paper": {
                    "id": paper.id,
                    "title": paper.title,
                    "authors": paper.authors,
                    "summary": paper.summary,
                    "categories": paper.categories,
                    "primary_category": paper.primary_category,
                    "published": paper.published,
                    "pdf_url": paper.pdf_url,
                    "arxiv_url": paper.arxiv_url,
                },
                "match_score": push.match_score,
                "is_read": push.is_read,
                "is_imported": push.is_imported,
                "imported_paper_id": push.imported_paper_id,
                "created_at": push.created_at,
            })

    return {"total": len(result), "pushes": result}


@router.post("/pushes/{push_id}/read")
async def mark_push_as_read(
    push_id: str,
    db: Session = Depends(get_db),
):
    """Mark a push record as read."""
    push = db.query(ArxivPushRecord).filter(ArxivPushRecord.id == push_id).first()
    if not push:
        raise HTTPException(status_code=404, detail="Push record not found")

    push.is_read = True
    db.commit()
    return {"success": True}


@router.get("/pushes/{user_id}/unread-count")
async def get_unread_count(
    user_id: str,
    db: Session = Depends(get_db),
):
    """Get count of unread pushes."""
    count = db.query(ArxivPushRecord).filter(
        ArxivPushRecord.user_id == user_id,
        ArxivPushRecord.is_read == False
    ).count()
    return {"unread_count": count}


# ========== Paper Import ==========

@router.post("/import")
async def import_arxiv_paper(
    request: ArxivImportRequest,
    db: Session = Depends(get_db),
):
    """Import an arXiv paper to local library."""
    from app.services.arxiv_crawler import import_arxiv_paper_to_local

    try:
        paper = import_arxiv_paper_to_local(db, request.arxiv_id, request.user_id)
        return {
            "success": True,
            "paper_id": paper.id,
            "message": "Paper imported successfully",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== Crawl Operations ==========

@router.post("/crawl/{subscription_id}")
async def trigger_crawl(
    subscription_id: str,
    db: Session = Depends(get_db),
):
    """Manually trigger crawl for a subscription."""
    try:
        subscription = db.query(ArxivSubscription).filter(
            ArxivSubscription.id == subscription_id
        ).first()

        if not subscription:
            raise HTTPException(status_code=404, detail="Subscription not found")

        # Create task record
        task = create_task_record(db, None, "arxiv_crawl")

        # Launch background task
        launch_background_task(
            task.id,
            run_arxiv_crawl,
            subscription_id,
            task.id,
        )

        return {"success": True, "task_id": task.id, "message": "Crawl started"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Trigger crawl failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to start crawl: {str(e)}")


@router.get("/crawl/logs/{subscription_id}")
async def get_crawl_logs(
    subscription_id: str,
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """Get crawl logs for a subscription."""
    logs = (
        db.query(ArxivCrawlLog)
        .filter(ArxivCrawlLog.subscription_id == subscription_id)
        .order_by(ArxivCrawlLog.started_at.desc())
        .limit(limit)
        .all()
    )

    return {
        "total": len(logs),
        "logs": [
            {
                "id": log.id,
                "status": log.status,
                "papers_found": log.papers_found,
                "papers_new": log.papers_new,
                "papers_pushed": log.papers_pushed,
                "started_at": log.started_at,
                "completed_at": log.completed_at,
            }
            for log in logs
        ],
    }


# ========== Categories ==========

@router.get("/categories")
async def get_categories():
    """Get list of arXiv categories."""
    return [
        {"code": code, "name": name}
        for code, name in ARXIV_CATEGORIES.items()
    ]


@router.get("/categories/search")
async def search_categories(
    q: str = Query(..., min_length=1),
):
    """Search arXiv categories by keyword."""
    q_lower = q.lower()
    results = [
        {"code": code, "name": name}
        for code, name in ARXIV_CATEGORIES.items()
        if q_lower in code.lower() or q_lower in name.lower()
    ]
    return {"total": len(results), "categories": results}
