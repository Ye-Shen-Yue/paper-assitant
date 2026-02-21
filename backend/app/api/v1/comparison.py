"""Comparison API endpoints."""
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.paper import Paper
from app.models.task import PaperProfile
from app.schemas.review import ComparisonRequest, ComparisonResult
from app.schemas.common import TaskResponse, TaskStatusEnum
from app.core.llm.client import get_llm_client

router = APIRouter()


@router.post("", response_model=ComparisonResult)
async def compare_papers(
    request: ComparisonRequest,
    db: Session = Depends(get_db),
):
    """Compare multiple papers."""
    if len(request.paper_ids) < 2:
        raise HTTPException(status_code=400, detail="At least 2 papers required")
    if len(request.paper_ids) > 5:
        raise HTTPException(status_code=400, detail="Maximum 5 papers for comparison")

    papers = []
    papers_info = []
    for pid in request.paper_ids:
        paper = db.query(Paper).filter(Paper.id == pid).first()
        if not paper:
            raise HTTPException(status_code=404, detail=f"Paper not found: {pid}")
        papers.append(paper)
        papers_info.append({
            "id": paper.id,
            "title": paper.title,
            "abstract": paper.abstract[:500],
        })

    # Build comparison prompt
    papers_text = ""
    for i, p in enumerate(papers):
        papers_text += f"\n### Paper {i+1}: {p.title}\nAbstract: {p.abstract}\n"

    client = get_llm_client()
    prompt = f"""Compare the following {len(papers)} academic papers across these aspects: {', '.join(request.aspects)}.

{papers_text}

Respond in JSON format:
{{
  "comparison_table": [
    {{
      "aspect": "aspect name",
      "papers": {{
        "Paper 1 title": "description for paper 1",
        "Paper 2 title": "description for paper 2"
      }}
    }}
  ],
  "narrative": "A comprehensive comparison narrative (2-3 paragraphs)"
}}"""

    try:
        result = client.chat_json(prompt)
    except Exception as e:
        result = {"comparison_table": [], "narrative": f"Comparison failed: {str(e)}"}

    return ComparisonResult(
        comparison_id=str(uuid.uuid4()),
        papers=papers_info,
        comparison_table=result.get("comparison_table", []),
        narrative=result.get("narrative", ""),
    )
