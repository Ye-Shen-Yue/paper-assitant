"""Visualization API endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.paper import Paper
from app.schemas.visualization import (
    GraphData, FlowchartData, TimelineData, RadarData, ExportRequest,
)
from app.services.visualization_service import (
    build_knowledge_graph,
    build_method_flowchart,
    build_innovation_timeline,
    build_radar_data,
)

router = APIRouter()


@router.get("/{paper_id}/knowledge-graph", response_model=GraphData)
async def get_knowledge_graph(paper_id: str, db: Session = Depends(get_db)):
    """Get knowledge graph data for visualization."""
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    data = build_knowledge_graph(db, paper_id)
    return GraphData(**data)


@router.get("/{paper_id}/method-flowchart", response_model=FlowchartData)
async def get_method_flowchart(paper_id: str, db: Session = Depends(get_db)):
    """Get method flowchart as Mermaid code."""
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    data = build_method_flowchart(db, paper_id)
    return FlowchartData(**data)


@router.get("/{paper_id}/timeline", response_model=TimelineData)
async def get_timeline(paper_id: str, db: Session = Depends(get_db)):
    """Get innovation timeline data."""
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    data = build_innovation_timeline(db, paper_id)
    return TimelineData(**data)


@router.get("/{paper_id}/radar", response_model=RadarData)
async def get_radar(paper_id: str, db: Session = Depends(get_db)):
    """Get radar chart data."""
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    data = build_radar_data(db, paper_id)
    return RadarData(**data)


@router.post("/{paper_id}/export")
async def export_visualization(
    paper_id: str,
    request: ExportRequest,
    db: Session = Depends(get_db),
):
    """Export visualization (returns data for frontend rendering)."""
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    # For MVP, return the data and let frontend handle export
    type_map = {
        "knowledge_graph": lambda: build_knowledge_graph(db, paper_id),
        "flowchart": lambda: build_method_flowchart(db, paper_id),
        "timeline": lambda: build_innovation_timeline(db, paper_id),
        "radar": lambda: build_radar_data(db, paper_id),
    }

    builder = type_map.get(request.visualization_type)
    if not builder:
        raise HTTPException(status_code=400, detail=f"Unknown visualization type: {request.visualization_type}")

    return {
        "data": builder(),
        "format": request.format,
        "theme": request.theme,
    }
