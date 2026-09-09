import logging
from typing import Dict, Any, List
from langgraph.graph import StateGraph, START, END
from backend.app.graph.state import ReviewState
from backend.app.graph.nodes import (
    entrypoint_node,
    rag_retrieval_node,
    code_analysis_node,
    bug_detection_node,
    security_node,
    quality_node,
    complexity_node,
    refactoring_node,
    validation_node,
    synthesizer_node
)

logger = logging.getLogger(__name__)


def route_by_depth(state: ReviewState) -> List[str]:
    """Conditional edge router for Quick vs Deep review modes."""
    mode = state.get("mode", "quick").lower()
    if mode == "deep":
        return ["rag_retrieval"]
    return ["code_analysis", "bug_detection"]


def route_after_rag(state: ReviewState) -> List[str]:
    """Routes to parallel deep analysis nodes after RAG context retrieval."""
    return ["code_analysis", "bug_detection", "security", "quality", "complexity"]


def route_after_validation(state: ReviewState) -> str:
    """Conditional router for refactoring validation retry loop vs synthesis."""
    status = state.get("validation_status", "pending")
    retry_count = state.get("retry_count", 0)

    if status in ["passed", "retried_passed", "fallback_original"]:
        return "synthesizer"
    elif retry_count < 2:
        return "refactoring"
    return "synthesizer"


def route_after_quick_analysis(state: ReviewState) -> str:
    """Routes after quick mode analysis nodes complete."""
    return "synthesizer"


def route_after_deep_analysis(state: ReviewState) -> str:
    """Routes after deep mode analysis nodes complete."""
    return "refactoring"


def build_review_graph() -> StateGraph:
    """Constructs and compiles the stateful multi-agent review execution graph."""
    builder = StateGraph(ReviewState)

    # 1. Add All Nodes
    builder.add_node("entrypoint", entrypoint_node)
    builder.add_node("rag_retrieval", rag_retrieval_node)
    builder.add_node("code_analysis", code_analysis_node)
    builder.add_node("bug_detection", bug_detection_node)
    builder.add_node("security", security_node)
    builder.add_node("quality", quality_node)
    builder.add_node("complexity", complexity_node)
    builder.add_node("refactoring", refactoring_node)
    builder.add_node("validation", validation_node)
    builder.add_node("synthesizer", synthesizer_node)

    # 2. Add Start & Entrypoint Edges
    builder.add_edge(START, "entrypoint")

    builder.add_conditional_edges(
        "entrypoint",
        route_by_depth,
        {
            "rag_retrieval": "rag_retrieval",
            "code_analysis": "code_analysis",
            "bug_detection": "bug_detection"
        }
    )

    builder.add_conditional_edges(
        "rag_retrieval",
        route_after_rag,
        [
            "code_analysis",
            "bug_detection",
            "security",
            "quality",
            "complexity"
        ]
    )

    # 3. Add Quick vs Deep Joining Edges
    # In Quick Mode: code_analysis and bug_detection join to synthesizer
    builder.add_edge("code_analysis", "synthesizer")
    builder.add_edge("bug_detection", "synthesizer")

    # In Deep Mode: security, quality, complexity join to refactoring (along with analysis & bugs if deep)
    builder.add_edge("security", "refactoring")
    builder.add_edge("quality", "refactoring")
    builder.add_edge("complexity", "refactoring")

    builder.add_edge("refactoring", "validation")

    builder.add_conditional_edges(
        "validation",
        route_after_validation,
        {
            "synthesizer": "synthesizer",
            "refactoring": "refactoring"
        }
    )

    builder.add_edge("synthesizer", END)

    return builder.compile()


review_graph = build_review_graph()


async def run_review_workflow(
    review_id: str,
    original_code: str,
    language: str = "auto",
    mode: str = "quick",
    rag_context: list = None
) -> Dict[str, Any]:
    """Helper entrypoint to invoke compiled review_graph workflow."""
    initial_state = {
        "review_id": review_id,
        "original_code": original_code,
        "language": language,
        "mode": mode,
        "rag_context": rag_context or [],
        "findings": [],
        "validation_errors": [],
        "retry_count": 0,
        "validation_status": "pending"
    }

    final_state = await review_graph.ainvoke(initial_state)
    return final_state.get("final_output", {})
