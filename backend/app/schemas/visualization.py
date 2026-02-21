from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime


class GraphNode(BaseModel):
    id: str
    label: str
    node_type: str
    size: float
    metadata: Dict = {}


class GraphEdge(BaseModel):
    source: str
    target: str
    relation: str
    weight: float


class GraphData(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]


class FlowchartData(BaseModel):
    mermaid_code: str
    steps: List[Dict] = []


class TimelineEntry(BaseModel):
    year: int
    event: str
    category: str
    related_paper: Optional[str] = None


class TimelineData(BaseModel):
    entries: List[TimelineEntry]
    current_paper_position: Dict = {}


class RadarData(BaseModel):
    dimensions: List[str]
    scores: List[float]
    max_score: float = 10.0
    paper_title: str


class ExportRequest(BaseModel):
    visualization_type: str
    format: str = "svg"
    theme: str = "academic"
    width: int = 1200
    height: int = 800
