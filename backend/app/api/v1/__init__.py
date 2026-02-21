from fastapi import APIRouter

from app.api.v1.papers import router as papers_router
from app.api.v1.parsing import router as parsing_router
from app.api.v1.analysis import router as analysis_router
from app.api.v1.review import router as review_router
from app.api.v1.visualization import router as visualization_router
from app.api.v1.comparison import router as comparison_router
from app.api.v1.tasks import router as tasks_router
from app.api.v1.chat import router as chat_router
from app.api.v1.tables import router as tables_router
from app.api.v1.recommendation import router as recommendation_router
from app.api.v1.arxiv import router as arxiv_router

router = APIRouter()

router.include_router(papers_router, prefix="/papers", tags=["Papers"])
router.include_router(parsing_router, prefix="/parsing", tags=["Parsing"])
router.include_router(analysis_router, prefix="/analysis", tags=["Analysis"])
router.include_router(review_router, prefix="/review", tags=["Review"])
router.include_router(visualization_router, prefix="/visualization", tags=["Visualization"])
router.include_router(comparison_router, prefix="/comparison", tags=["Comparison"])
router.include_router(tasks_router, prefix="/tasks", tags=["Tasks"])
router.include_router(chat_router, prefix="/chat", tags=["Chat"])
router.include_router(tables_router, prefix="/tables", tags=["Tables"])
router.include_router(recommendation_router, prefix="/recommendations", tags=["Recommendations"])
router.include_router(arxiv_router, prefix="/arxiv", tags=["arXiv"])
