
from fastapi import APIRouter, HTTPException

from app.modules.tabular.service import TabularService
from app.schemas import TabularReviewRequest, TabularReviewResponse

router = APIRouter()
tabular_service = TabularService()

@router.post("/review", response_model=TabularReviewResponse)
async def review_tabular_data(request: TabularReviewRequest) -> TabularReviewResponse:
    """Review tabular data against control requirements."""
    try:
        return await tabular_service.review_data(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/review/batch", response_model=list[TabularReviewResponse])
async def batch_review_tabular_data(requests: list[TabularReviewRequest]) -> list[TabularReviewResponse]:
    """Review multiple tabular data sets in parallel."""
    try:
        return await tabular_service.review_multiple_data(requests)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
