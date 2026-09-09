from datetime import datetime, timezone
from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class InputMetadata(BaseModel):
    """Metadata regarding submitted code input."""
    language: str = Field(..., description="Detected or specified programming language")
    line_count: int = Field(..., description="Number of lines in original code")
    char_count: int = Field(..., description="Total character count in original code")
    hash: str = Field(..., description="SHA-256 hash of original code")


class Summary(BaseModel):
    """High-level review summary and verdict."""
    overview: str = Field(..., description="Plain-English description of code functionality")
    verdict: Literal["clean", "minor_issues", "major_issues", "critical_vulnerabilities"] = Field(
        ..., description="Overall assessment verdict"
    )
    key_takeaways: List[str] = Field(default_factory=list, description="Key bullet points summarizing findings")


class Metrics(BaseModel):
    """Quantitative code metrics."""
    complexity_score: float = Field(..., ge=0.0, le=10.0, description="Complexity score from 0 to 10")
    readability_score: float = Field(..., ge=0.0, le=10.0, description="Readability score from 0 to 10")
    maintainability_index: Optional[str] = Field(default="B", description="Maintainability grade (e.g. A, B, C, D, F)")
    cyclomatic_complexity_est: Optional[str] = Field(default="Moderate", description="Qualitative complexity rating")


class Finding(BaseModel):
    """Individual code finding or issue."""
    id: str = Field(..., description="Unique finding ID (e.g. find-001)")
    category: Literal["bug", "security", "quality", "complexity"] = Field(..., description="Category of finding")
    severity: Literal["critical", "high", "medium", "low", "info"] = Field(..., description="Severity level")
    title: str = Field(..., description="Short finding title")
    description: str = Field(..., description="Detailed issue description")
    line_start: Optional[int] = Field(default=None, description="Starting line number (1-indexed)")
    line_end: Optional[int] = Field(default=None, description="Ending line number (1-indexed)")
    code_snippet: Optional[str] = Field(default=None, description="Relevant code snippet")
    suggestion: Optional[str] = Field(default=None, description="Recommended remediation or fix")
    cwe_or_rule_id: Optional[str] = Field(default=None, description="Associated CWE identifier or rule ID")


class Refactoring(BaseModel):
    """Refactored code result and validation state."""
    has_refactored_code: bool = Field(default=False, description="Whether refactored code is available")
    refactored_code: Optional[str] = Field(default=None, description="Generated refactored code block")
    diff_summary: Optional[str] = Field(default=None, description="High-level summary of code changes")
    validation_status: Literal["passed", "retried_passed", "fallback_original"] = Field(
        default="passed", description="Status of AST syntax validation loop"
    )
    validation_notes: Optional[str] = Field(default=None, description="Detailed notes on validation checks")


class ExecutionMetadata(BaseModel):
    """Execution telemetry and runtime metadata."""
    total_duration_ms: int = Field(default=0, description="Total review duration in milliseconds")
    llm_provider_used: str = Field(default="gemini", description="Primary LLM provider used (e.g. gemini, mistral)")
    fallback_triggered: bool = Field(default=False, description="Whether fallback provider was triggered")
    rag_context_used: bool = Field(default=False, description="Whether RAG knowledge search was utilized")
    rag_sources: List[str] = Field(default_factory=list, description="List of RAG source document titles/IDs")


class CodeReviewDocument(BaseModel):
    """MongoDB Document Schema for 'code_reviews' collection."""
    review_id: str = Field(..., description="Unique review identifier")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="UTC timestamp of creation")
    mode: Literal["quick", "deep"] = Field(..., description="Review depth mode")
    original_code: str = Field(..., description="Raw original code submitted by user")
    input_metadata: InputMetadata = Field(..., description="Input file statistics")
    summary: Summary = Field(..., description="Executive summary and verdict")
    metrics: Metrics = Field(..., description="Evaluated code metrics")
    findings: List[Finding] = Field(default_factory=list, description="Array of findings")
    refactoring: Refactoring = Field(default_factory=Refactoring, description="Refactoring outputs")
    execution_metadata: ExecutionMetadata = Field(default_factory=ExecutionMetadata, description="Telemetry metadata")
    status: Literal["pending", "processing", "completed", "failed"] = Field(default="completed", description="Review workflow status")


class AgentRunDocument(BaseModel):
    """MongoDB Document Schema for 'agent_runs' audit collection."""
    run_id: str = Field(..., description="Unique agent run identifier")
    review_id: str = Field(..., description="Associated review ID")
    agent_name: str = Field(..., description="Name of agent (e.g. SecurityAgent)")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="UTC execution timestamp")
    prompt_input: Optional[str] = Field(default=None, description="Formatted prompt sent to LLM")
    raw_llm_output: Optional[str] = Field(default=None, description="Raw response output from LLM")
    duration_ms: int = Field(default=0, description="Execution duration in milliseconds")
    model_used: str = Field(..., description="LLM model identifier used")
    status: Literal["success", "failed", "retried"] = Field(default="success", description="Agent execution status")


class RAGDocument(BaseModel):
    """MongoDB Document Schema for 'rag_documents' vector collection."""
    doc_id: str = Field(..., description="Unique document ID (e.g. rag_cwe_476)")
    title: str = Field(..., description="Document title or standard name")
    category: Literal["security", "clean_code", "best_practices"] = Field(..., description="Document domain category")
    language: str = Field(default="general", description="Target programming language or 'general'")
    content: str = Field(..., description="Document body text")
    embedding: Optional[List[float]] = Field(default=None, description="768-dimensional vector embedding")
