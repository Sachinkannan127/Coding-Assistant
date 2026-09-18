import logging
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, status, Query, BackgroundTasks
from pydantic import BaseModel

from backend.app.services.eval_service import eval_service, BENCHMARK_DATASET, EvaluationSummary
from backend.app.services.review_service import review_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/eval", tags=["AI Quality Evaluation Benchmark"])


class RunEvalRequest(BaseModel):
    use_mock: bool = True
    sample_ids: Optional[List[str]] = None


@router.get(
    "/benchmark",
    status_code=status.HTTP_200_OK,
    summary="Get Labeled AI Benchmark Dataset Samples",
    response_description="List of benchmark dataset samples with expected findings and SLA targets"
)
async def get_benchmark_samples():
    """
    Returns ground truth dataset samples covering multi-language vulnerabilities used for AI evaluation.
    """
    samples = []
    for s in BENCHMARK_DATASET:
        samples.append({
            "sample_id": s.sample_id,
            "language": s.language,
            "expected_mode": s.expected_mode,
            "expected_findings_count": len(s.expected_findings),
            "target_max_latency_ms": s.target_max_latency_ms,
            "code_snippet": s.code[:80]
        })
    return {
        "total_samples": len(samples),
        "samples": samples
    }


@router.post(
    "/run",
    status_code=status.HTTP_200_OK,
    summary="Execute AI System Quality & Performance Benchmark",
    response_description="Evaluation summary containing Precision, Recall, F1 score, AST pass rate, and SLA metrics"
)
async def run_evaluation_benchmark(body: RunEvalRequest):
    """
    Executes AI system evaluation benchmark across labeled dataset samples and computes precision/recall/F1 metrics.
    """
    from scripts.run_ai_evaluation import run_benchmark
    try:
        summary = await run_benchmark(use_mock=body.use_mock)
        return {
            "status": "completed",
            "mode": "mock" if body.use_mock else "live",
            "summary": summary.model_dump()
        }
    except Exception as err:
        logger.error(f"Evaluation benchmark execution failed: {err}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute evaluation benchmark: {str(err)}"
        )
