import logging
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, status, Response, Depends
from backend.app.api.schemas import ReviewRequest, ReviewListResponse
from backend.app.services.review_service import review_service
from backend.app.services.code_validator import CodeValidationError
from backend.app.auth import get_current_user, get_optional_user


logger = logging.getLogger(__name__)

router = APIRouter()


def format_review_markdown(review: dict) -> str:
    """Formats a review document into GitHub-Flavored Markdown report."""
    review_id = review.get("review_id", "UNKNOWN")
    verdict = review.get("verdict", "N/A")
    score = review.get("rating_score", 0)
    summary = review.get("executive_summary", "")
    mode = review.get("review_mode", "quick")
    exec_time = review.get("execution_time_seconds", 0)
    lang = review.get("language_detected") or review.get("input_metadata", {}).get("language", "auto")
    model = review.get("model_used", "gemini-2.5-flash")

    metrics = review.get("metrics", {})
    findings = review.get("findings", [])
    refactored_code = review.get("refactored_code", "")
    refactoring_explanation = review.get("refactoring_explanation", "")
    rag_docs = review.get("rag_documents_cited", [])

    lines = [
        f"# ⚡ AI Code Review & Refactoring Audit Report",
        f"",
        f"**Review ID**: `{review_id}`  ",
        f"**Analysis Mode**: `{mode.upper()}`  ",
        f"**Language**: `{lang}`  ",
        f"**AI Model**: `{model}`  ",
        f"**Execution Duration**: `{exec_time:.2f}s`  ",
        f"",
        f"---",
        f"",
        f"## 📊 Executive Summary",
        f"",
        f"- **Verdict**: **{verdict}**",
        f"- **Overall Code Health Rating**: **{score} / 100**",
        f"",
        f"### Synthesized Evaluation",
        f"{summary}",
        f"",
        f"---",
        f"",
        f"## 📈 Metrics Breakdown",
        f"",
        f"| Metric | Score |",
        f"| :--- | :--- |",
        f"| Security Rating | {metrics.get('security', 85)}% |",
        f"| Readability Score | {metrics.get('readability', 85)}% |",
        f"| Maintainability Index | {metrics.get('maintainability', 80)}% |",
        f"| Complexity Rating | {metrics.get('complexity', 75)}% |",
        f"| Code Quality Rating | {metrics.get('quality', 88)}% |",
        f"",
        f"---",
        f"",
        f"## 🔍 Detailed Findings ({len(findings)})",
        f""
    ]

    if not findings:
        lines.append("No critical vulnerabilities or anti-patterns detected.\n")
    else:
        for idx, f in enumerate(findings, 1):
            line_refs = f", ".join(map(str, f.get("line_numbers", []))) if f.get("line_numbers") else "N/A"
            lines.extend([
                f"### {idx}. [{f.get('severity', 'INFO')}] {f.get('title', 'Finding')}",
                f"- **Category**: `{f.get('category', 'quality')}`",
                f"- **Line Reference(s)**: {line_refs}",
                f"- **Description**: {f.get('description', '')}",
            ])
            if f.get("impact"):
                lines.append(f"- **Impact**: {f.get('impact')}")
            if f.get("recommendation"):
                lines.extend([
                    f"",
                    f"```",
                    f"{f.get('recommendation')}",
                    f"```"
                ])
            lines.append("")

    if refactored_code:
        lines.extend([
            f"---",
            f"",
            f"## 🛠️ Automated Code Refactoring",
            f""
        ])
        if refactoring_explanation:
            lines.extend([
                f"### Refactoring Rationale",
                f"{refactoring_explanation}",
                f""
            ])
        lines.extend([
            f"```",
            f"{refactored_code}",
            f"```",
            f""
        ])

    if rag_docs:
        lines.extend([
            f"---",
            f"",
            f"## 📚 RAG Vector Knowledge Base Context",
            f""
        ])
        for doc in rag_docs:
            title = doc.get("title", "Reference")
            cat = doc.get("category", "General")
            content = doc.get("content", "")
            lines.extend([
                f"### 📖 {title} (`{cat}`)",
                f"{content}",
                f""
            ])

    return "\n".join(lines)


@router.post(
    "/review",
    status_code=status.HTTP_200_OK,
    summary="Submit Code for AI Review & Refactoring",
    description="Analyzes code, detects bugs & security risks, calculates metrics, generates refactorings, and returns unified review schema."
)
async def submit_review(
    payload: ReviewRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:

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


@router.post(
    "/review/stream",
    summary="Submit Code for Streaming AI Review",
    description="Streams real-time progress events and chunked review outputs via Server-Sent Events (SSE)."
)
async def stream_review_endpoint(payload: ReviewRequest):
    """POST /api/review/stream SSE endpoint handler."""
    from fastapi.responses import StreamingResponse
    try:
        return StreamingResponse(
            review_service.stream_review(
                code=payload.code,
                language=payload.language,
                mode=payload.mode
            ),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
    except CodeValidationError as val_err:
        raise val_err
    except Exception as exc:
        logger.error(f"Unexpected error executing streaming review API: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute streaming code review: {str(exc)}"
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
    "/review/{review_id}/export",
    status_code=status.HTTP_200_OK,
    summary="Export Code Review as Markdown Report",
    description="Generates a formatted Markdown report file for download."
)
async def export_review_markdown(review_id: str) -> Response:
    """GET /api/review/{review_id}/export endpoint handler."""
    result = await review_service.get_review_by_id(review_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Code review '{review_id}' not found."
        )
    
    md_content = format_review_markdown(result)
    filename = f"review_report_{review_id[:8]}.md"
    
    return Response(
        content=md_content,
        media_type="text/markdown",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )


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
