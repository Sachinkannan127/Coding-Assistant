import ast
import logging
from typing import Dict, Any, List
from backend.app.graph.state import ReviewState
from backend.app.services.code_validator import validate_and_normalize_code
from backend.app.services.rag_service import rag_service
from backend.app.services.code_refactor_validator import validate_refactored_code
from backend.app.agents import (
    code_analysis_agent,
    bug_detection_agent,
    security_agent,
    quality_agent,
    complexity_agent,
    refactoring_agent,
    synthesizer_agent,
    FindingSchema
)

logger = logging.getLogger(__name__)


async def entrypoint_node(state: ReviewState) -> Dict[str, Any]:
    """Validates input, normalizes line breaks, and initializes ReviewState."""
    logger.info(f"Executing Entrypoint Node for review_id: {state.get('review_id')}")
    original_code = state.get("original_code", "")
    language = state.get("language", "auto")

    norm_res = validate_and_normalize_code(code=original_code, language=language)

    return {
        "original_code": norm_res.normalized_code,
        "language": norm_res.language,
        "findings": [],
        "rag_context": state.get("rag_context") or [],
        "retry_count": 0,
        "validation_errors": [],
        "validation_status": "pending"
    }


async def rag_retrieval_node(state: ReviewState) -> Dict[str, Any]:
    """Retrieves relevant knowledge base context for Deep Review mode."""
    logger.info("Executing RAG Retrieval Node...")
    original_code = state.get("original_code", "")
    language = state.get("language", "python")

    retrieved_context = await rag_service.retrieve_knowledge(
        query_code=original_code,
        language=language
    )
    return {"rag_context": retrieved_context}


async def code_analysis_node(state: ReviewState) -> Dict[str, Any]:
    """Executes CodeAnalysisAgent pass."""
    logger.info("Executing Code Analysis Node...")
    res = await code_analysis_agent.analyze(
        code=state["original_code"],
        language=state["language"]
    )
    return {"code_overview": res.output.overview}


async def bug_detection_node(state: ReviewState) -> Dict[str, Any]:
    """Executes BugDetectionAgent pass."""
    logger.info("Executing Bug Detection Node...")
    res = await bug_detection_agent.detect_bugs(
        code=state["original_code"],
        language=state["language"],
        rag_context=state.get("rag_context")
    )
    findings_dicts = [f.model_dump() for f in res.output.findings]
    return {"findings": findings_dicts}


async def security_node(state: ReviewState) -> Dict[str, Any]:
    """Executes SecurityAgent pass."""
    logger.info("Executing Security Node...")
    res = await security_agent.audit_security(
        code=state["original_code"],
        language=state["language"],
        rag_context=state.get("rag_context")
    )
    findings_dicts = [f.model_dump() for f in res.output.findings]
    return {"findings": findings_dicts}


async def quality_node(state: ReviewState) -> Dict[str, Any]:
    """Executes QualityReadabilityAgent pass."""
    logger.info("Executing Quality & Readability Node...")
    res = await quality_agent.evaluate_quality(
        code=state["original_code"],
        language=state["language"],
        rag_context=state.get("rag_context")
    )
    findings_dicts = [f.model_dump() for f in res.output.findings]
    return {
        "findings": findings_dicts,
        "readability_score": res.output.readability_score
    }


async def complexity_node(state: ReviewState) -> Dict[str, Any]:
    """Executes ComplexityAgent pass."""
    logger.info("Executing Complexity Node...")
    res = await complexity_agent.analyze_complexity(
        code=state["original_code"],
        language=state["language"]
    )
    findings_dicts = [f.model_dump() for f in res.output.findings]
    return {
        "findings": findings_dicts,
        "complexity_score": res.output.complexity_score,
        "maintainability_index": res.output.maintainability_index,
        "cyclomatic_complexity_est": res.output.cyclomatic_complexity_est
    }


async def refactoring_node(state: ReviewState) -> Dict[str, Any]:
    """Executes RefactoringAgent pass."""
    logger.info("Executing Refactoring Node...")
    findings_objs = [FindingSchema(**f) for f in state.get("findings", [])]

    res = await refactoring_agent.generate_refactoring(
        code=state["original_code"],
        language=state["language"],
        findings=findings_objs,
        rag_context=state.get("rag_context")
    )
    return {
        "refactored_code": res.output.refactored_code,
        "diff_summary": res.output.diff_summary
    }


async def validation_node(state: ReviewState) -> Dict[str, Any]:
    """
    Validates generated refactored code via AST syntax parsing and signature preservation checks.
    Increments retry_count and logs errors if validation fails.
    """
    logger.info("Executing Validation Node...")
    orig_code = state.get("original_code", "")
    refac_code = state.get("refactored_code", orig_code)
    lang = state.get("language", "python")
    retry_count = state.get("retry_count", 0)

    val_result = validate_refactored_code(
        original_code=orig_code,
        refactored_code=refac_code,
        language=lang,
        retry_count=retry_count
    )

    if val_result.is_valid:
        return {"validation_status": val_result.status}
    else:
        logger.warning(f"Validation failed (retry {retry_count}): {val_result.errors}")
        if val_result.status == "fallback_original":
            return {
                "validation_status": "fallback_original",
                "refactored_code": orig_code,
                "validation_errors": val_result.errors
            }
        return {
            "retry_count": retry_count + 1,
            "validation_errors": val_result.errors
        }


async def synthesizer_node(state: ReviewState) -> Dict[str, Any]:
    """Executes SynthesizerAgent pass to aggregate findings and format final response."""
    logger.info("Executing Synthesizer Node...")
    findings_objs = [FindingSchema(**f) for f in state.get("findings", [])]

    res = await synthesizer_agent.synthesize(
        code_overview=state.get("code_overview", "Code Review Summary"),
        all_findings=findings_objs,
        readability_score=state.get("readability_score", 8.0),
        complexity_score=state.get("complexity_score", 5.0),
        language=state.get("language", "python")
    )

    final_payload = res.output.model_dump()
    final_payload["refactored_code"] = state.get("refactored_code", state.get("original_code"))
    final_payload["diff_summary"] = state.get("diff_summary", "")
    final_payload["validation_status"] = state.get("validation_status", "passed")

    return {"final_output": final_payload}
