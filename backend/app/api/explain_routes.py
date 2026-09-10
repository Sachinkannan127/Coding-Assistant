from fastapi import APIRouter, HTTPException, status
from backend.app.api.schemas import ExplainRequest, ExplainResponse
from backend.app.services.explain_service import ExplainService

explain_router = APIRouter()


@explain_router.post(
    "/explain",
    response_model=ExplainResponse,
    status_code=status.HTTP_200_OK,
    summary="Explain Code in Simple English",
    description="Generates an easy-to-understand, audience-tailored code explanation with real-world analogies and line-by-line breakdowns."
)
async def explain_code_endpoint(payload: ExplainRequest):
    """
    Explains source code snippet in plain English for Kids, Beginners, or Developers.
    """
    if not payload.code or not payload.code.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Code payload cannot be empty."
        )

    result = await ExplainService.explain_code(
        code=payload.code,
        language=payload.language,
        audience=payload.audience
    )

    return ExplainResponse(**result)
