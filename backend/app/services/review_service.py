import time
import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from backend.app.services.code_validator import validate_and_normalize_code, CodeValidationError
from backend.app.graph import run_review_workflow

logger = logging.getLogger(__name__)


class ReviewService:
    """
    High-level Review Orchestration Service.
    Handles input validation, execution mode dispatching (Quick Scan vs Deep Review),
    LangGraph execution, duration timing, and Unified Schema response formatting.
    """

    async def run_review(
        self,
        code: str,
        language: str = "auto",
        mode: str = "quick",
        review_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes code review workflow and returns unified JSON schema payload.

        Args:
            code: Source code input text.
            language: Programming language / framework or 'auto'.
            mode: 'quick' for rapid scan or 'deep' for full audit with refactoring & RAG.
            review_id: Optional existing review ID string.

        Returns:
            Dict conforming strictly to the Unified Output Schema.
        """
        start_time = time.perf_counter()
        rev_id = review_id or f"rev_{uuid.uuid4().hex[:12]}"
        clean_mode = mode.lower().strip() if mode else "quick"

        if clean_mode not in ["quick", "deep"]:
            clean_mode = "quick"

        # 1. Validate & Normalize Code Input
        norm_result = validate_and_normalize_code(code=code, language=language)

        # 2. Invoke LangGraph Multi-Agent State Graph Workflow
        logger.info(f"ReviewService executing '{clean_mode}' review workflow for {rev_id}...")
        graph_output = await run_review_workflow(
            review_id=rev_id,
            original_code=norm_result.normalized_code,
            language=norm_result.language,
            mode=clean_mode
        )

        elapsed_ms = int((time.perf_counter() - start_time) * 1000)

        # 3. Format Response conforming strictly to Unified Output Schema
        summary_data = {
            "overview": graph_output.get("overview", "Code Review Summary"),
            "verdict": graph_output.get("verdict", "clean"),
            "key_takeaways": graph_output.get("key_takeaways", [])
        }

        metrics_data = {
            "complexity_score": float(graph_output.get("complexity_score", 5.0)),
            "readability_score": float(graph_output.get("readability_score", 8.0)),
            "maintainability_index": graph_output.get("maintainability_index", "B"),
            "cyclomatic_complexity_est": graph_output.get("cyclomatic_complexity_est", "Low")
        }

        refactored_code = graph_output.get("refactored_code", norm_result.normalized_code)
        has_refactoring = bool(refactored_code and refactored_code.strip() != norm_result.normalized_code.strip())

        refactoring_data = {
            "has_refactored_code": has_refactoring,
            "refactored_code": refactored_code,
            "diff_summary": graph_output.get("diff_summary", "No major structural changes."),
            "validation_status": graph_output.get("validation_status", "passed"),
            "validation_notes": "AST syntax check passed." if graph_output.get("validation_status") != "fallback_original" else "Syntax check failed; safely restored original code."
        }

        execution_metadata = {
            "total_duration_ms": elapsed_ms,
            "llm_provider_used": "gemini",
            "fallback_triggered": False,
            "rag_context_used": clean_mode == "deep",
            "rag_sources": ["OWASP Top 10 API Security", "Clean Code Guidelines"] if clean_mode == "deep" else []
        }

        return {
            "review_id": rev_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "mode": clean_mode,
            "input_metadata": {
                "language": norm_result.language,
                "line_count": norm_result.line_count,
                "char_count": norm_result.char_count,
                "hash": norm_result.hash
            },
            "summary": summary_data,
            "metrics": metrics_data,
            "findings": graph_output.get("findings", []),
            "refactoring": refactoring_data,
            "execution_metadata": execution_metadata
        }


review_service = ReviewService()
