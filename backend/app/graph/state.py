import operator
from typing import TypedDict, List, Dict, Any, Optional
from typing_extensions import Annotated
from backend.app.agents.schemas import FindingSchema


class ReviewState(TypedDict):
    """
    State object passed between nodes in the LangGraph review execution graph.
    Uses Annotated with operator.add for thread-safe list concatenation across parallel nodes.
    """
    # Inputs
    review_id: str
    original_code: str
    language: str
    mode: str  # 'quick' | 'deep'
    
    # RAG Context
    rag_context: List[str]
    
    # Agent Outputs (Accumulated via list concatenation reducer)
    findings: Annotated[List[Dict[str, Any]], operator.add]
    code_overview: str
    complexity_score: float
    readability_score: float
    maintainability_index: str
    cyclomatic_complexity_est: str
    
    # Refactoring & Validation State
    refactored_code: Optional[str]
    diff_summary: Optional[str]
    validation_status: str  # 'pending' | 'passed' | 'retried_passed' | 'fallback_original'
    retry_count: int
    validation_errors: Annotated[List[str], operator.add]
    
    # Final Output & Telemetry
    final_output: Optional[Dict[str, Any]]
    error: Optional[str]
