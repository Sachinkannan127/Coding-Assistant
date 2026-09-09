import logging
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, status
from backend.app.api.schemas import ReviewRequest, ReviewListResponse
from backend.app.services.review_service import review_service
from backend.app.services.code_validator import CodeValidationError

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/review",
    status_code=status.HTTP_200_OK,
    summary="Submit Code for AI Review & Refactoring",
    description="Analyzes code, detects bugs & security risks, calculates metrics, generates refactorings, and returns unified review schema."
)
async def submit_review(payload: ReviewRequest) -> Dict[str, Any]:
    """POST /api/review endpoint handler."""
    try:
        review_result = await review_service.run_review(
            code=payload.code,
            language=payload.language,
            mode=payload.mode
        )
        return review_result
    except CodeValidationError as val_err:
        raise val_err
    except Exception as exc:
        logger.error(f"Unexpected error executing review API: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute code review: {str(exc)}"
        )


@router.get(
    "/review/{review_id}",
    status_code=status.HTTP_200_OK,
    summary="Get Code Review by ID",
    description="Retrieves a completed review record and findings by its review_id."
)
async def get_review(review_id: str) -> Dict[str, Any]:
    """GET /api/review/{review_id} endpoint handler."""
    result = await review_service.get_review_by_id(review_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Code review '{review_id}' not found."
        )
    return result


@router.get(
    "/reviews",
    status_code=status.HTTP_200_OK,
    response_model=ReviewListResponse,
    summary="List Recent Code Reviews",
    description="Returns recent code reviews sorted descending by creation time."
)
async def list_reviews(limit: int = 20) -> ReviewListResponse:
    """GET /api/reviews endpoint handler."""
    reviews = await review_service.list_recent_reviews(limit=limit)
    return ReviewListResponse(reviews=reviews, count=len(reviews))
