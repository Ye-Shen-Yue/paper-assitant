"""Table generation API endpoints using Kimi AI."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict

from app.database import get_db
from app.models.paper import Paper
from app.services.table_generation_service import TableGenerationService

router = APIRouter()


@router.post("/generate/{paper_id}")
async def generate_tables(
    paper_id: str,
    db: Session = Depends(get_db),
):
    """Generate LaTeX tables from paper content using Kimi AI."""
    try:
        paper = db.query(Paper).filter(Paper.id == paper_id).first()
        if not paper:
            raise HTTPException(status_code=404, detail="Paper not found")

        service = TableGenerationService(db)
        tables = service.generate_tables(paper)

        return {"tables": tables}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate tables: {str(e)}")


@router.post("/explain")
async def explain_table(
    table_data: Dict,
    db: Session = Depends(get_db),
):
    """Generate explanation for a LaTeX table."""
    try:
        service = TableGenerationService(db)
        explanation = service.explain_table(table_data)
        return {"explanation": explanation}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate explanation: {str(e)}")
