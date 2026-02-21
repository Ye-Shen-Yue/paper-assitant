"""Recommendation system API endpoints."""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db
from app.models.recommendation import UserActivity, UserProfile, PaperEmbedding, UserCollection, RecommendationLog
from app.models.paper import Paper
from app.schemas.paper import PaperSummary
from app.services.recommendation_service import RecommendationService

router = APIRouter()


class TrackActivityRequest(BaseModel):
    user_id: str
    paper_id: str
    activity_type: str  # 'view', 'chat', 'note', 'export', 'save', 'scroll', 'click'
    duration_seconds: Optional[int] = 0
    meta_info: Optional[dict] = {}


class TrackActivityResponse(BaseModel):
    success: bool
    activity_id: str


class UserProfileResponse(BaseModel):
    user_id: str
    topic_distribution: dict
    method_preferences: List[str]
    reading_pattern: str
    total_papers_read: int
    total_reading_time: int
    streak_days: int
    last_read_papers: List[str]
    updated_at: Optional[datetime]


class RecommendationItem(BaseModel):
    paper: PaperSummary
    reason: str
    reason_text: str
    score: float


class RecommendationsResponse(BaseModel):
    recommendations: List[RecommendationItem]
    total: int


class TrendDataRequest(BaseModel):
    topics: Optional[List[str]] = None
    years: int = 10


class TrendDataResponse(BaseModel):
    heatmap_data: List[dict]
    keyword_evolution: List[dict]
    emerging_topics: List[dict]
    ai_summary: str


@router.post("/activities/track", response_model=TrackActivityResponse)
async def track_activity(
    request: TrackActivityRequest,
    db: Session = Depends(get_db),
):
    """Track user activity for building user profile."""
    activity = UserActivity(
        user_id=request.user_id,
        paper_id=request.paper_id,
        activity_type=request.activity_type,
        duration_seconds=request.duration_seconds or 0,
        meta_info=request.meta_info or {},
    )
    db.add(activity)
    db.commit()
    db.refresh(activity)

    # Update user profile in background (could be async)
    service = RecommendationService(db)
    service.update_user_profile(request.user_id)

    return TrackActivityResponse(success=True, activity_id=activity.id)


@router.get("/profile/{user_id}", response_model=UserProfileResponse)
async def get_user_profile(
    user_id: str,
    db: Session = Depends(get_db),
):
    """Get user research profile."""
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()

    if not profile:
        # Return empty profile
        return UserProfileResponse(
            user_id=user_id,
            topic_distribution={},
            method_preferences=[],
            reading_pattern="browser",
            total_papers_read=0,
            total_reading_time=0,
            streak_days=0,
            last_read_papers=[],
            updated_at=None,
        )

    return UserProfileResponse(
        user_id=profile.user_id,
        topic_distribution=profile.topic_distribution or {},
        method_preferences=profile.method_preferences or [],
        reading_pattern=profile.reading_pattern or "browser",
        total_papers_read=profile.total_papers_read or 0,
        total_reading_time=profile.total_reading_time or 0,
        streak_days=profile.streak_days or 0,
        last_read_papers=profile.last_read_papers or [],
        updated_at=profile.updated_at,
    )


@router.post("/profile/{user_id}/refresh")
async def refresh_user_profile(
    user_id: str,
    db: Session = Depends(get_db),
):
    """Manually refresh user profile."""
    service = RecommendationService(db)
    service.update_user_profile(user_id)
    return {"success": True, "message": "Profile updated"}


@router.get("/recommendations/{user_id}", response_model=RecommendationsResponse)
async def get_recommendations(
    user_id: str,
    limit: int = Query(10, ge=1, le=50),
    type: str = Query("mixed", enum=["mixed", "content", "collaborative", "trending"]),
    db: Session = Depends(get_db),
):
    """Get personalized paper recommendations for user."""
    service = RecommendationService(db)
    recommendations = service.generate_recommendations(user_id, limit=limit, rec_type=type)

    return RecommendationsResponse(
        recommendations=recommendations,
        total=len(recommendations),
    )


@router.post("/recommendations/{user_id}/feedback")
async def log_recommendation_feedback(
    user_id: str,
    paper_id: str,
    recommendation_type: str,
    clicked: bool = False,
    rated: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """Log user feedback on recommendations for algorithm improvement."""
    log = RecommendationLog(
        user_id=user_id,
        paper_id=paper_id,
        recommendation_type=recommendation_type,
        clicked=1 if clicked else 0,
        rated=rated,
    )
    db.add(log)
    db.commit()
    return {"success": True}


@router.get("/trends/{user_id}", response_model=TrendDataResponse)
async def get_trend_data(
    user_id: str,
    topics: Optional[str] = None,  # Comma-separated list
    years: int = Query(10, ge=1, le=20),
    db: Session = Depends(get_db),
):
    """Get research trend data for visualization."""
    topic_list = topics.split(",") if topics else None

    service = RecommendationService(db)
    trend_data = service.get_trend_data(user_id, topic_list, years)

    return TrendDataResponse(**trend_data)


# Collection management endpoints
class CollectionCreateRequest(BaseModel):
    user_id: str
    name: str
    description: Optional[str] = ""


class CollectionResponse(BaseModel):
    id: str
    user_id: str
    name: str
    description: str
    paper_ids: List[str]
    paper_count: int
    created_at: datetime
    updated_at: datetime


@router.post("/collections", response_model=CollectionResponse)
async def create_collection(
    request: CollectionCreateRequest,
    db: Session = Depends(get_db),
):
    """Create a new paper collection."""
    collection = UserCollection(
        user_id=request.user_id,
        name=request.name,
        description=request.description or "",
    )
    db.add(collection)
    db.commit()
    db.refresh(collection)

    return CollectionResponse(
        id=collection.id,
        user_id=collection.user_id,
        name=collection.name,
        description=collection.description,
        paper_ids=collection.paper_ids or [],
        paper_count=len(collection.paper_ids or []),
        created_at=collection.created_at,
        updated_at=collection.updated_at,
    )


@router.get("/collections/{user_id}", response_model=List[CollectionResponse])
async def list_collections(
    user_id: str,
    db: Session = Depends(get_db),
):
    """List all collections for a user."""
    collections = db.query(UserCollection).filter(UserCollection.user_id == user_id).all()

    return [
        CollectionResponse(
            id=c.id,
            user_id=c.user_id,
            name=c.name,
            description=c.description,
            paper_ids=c.paper_ids or [],
            paper_count=len(c.paper_ids or []),
            created_at=c.created_at,
            updated_at=c.updated_at,
        )
        for c in collections
    ]


@router.post("/collections/{collection_id}/papers")
async def add_paper_to_collection(
    collection_id: str,
    paper_id: str,
    db: Session = Depends(get_db),
):
    """Add a paper to a collection."""
    collection = db.query(UserCollection).filter(UserCollection.id == collection_id).first()
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")

    paper_ids = collection.paper_ids or []
    if paper_id not in paper_ids:
        paper_ids.append(paper_id)
        collection.paper_ids = paper_ids
        db.commit()

    return {"success": True}


@router.delete("/collections/{collection_id}/papers/{paper_id}")
async def remove_paper_from_collection(
    collection_id: str,
    paper_id: str,
    db: Session = Depends(get_db),
):
    """Remove a paper from a collection."""
    collection = db.query(UserCollection).filter(UserCollection.id == collection_id).first()
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")

    paper_ids = collection.paper_ids or []
    if paper_id in paper_ids:
        paper_ids.remove(paper_id)
        collection.paper_ids = paper_ids
        db.commit()

    return {"success": True}
