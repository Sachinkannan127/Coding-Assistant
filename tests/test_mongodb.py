import sys
from pathlib import Path
import pytest
from datetime import datetime, timezone

# Ensure root directory is in sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from backend.app.models import (
    CodeReviewDocument,
    InputMetadata,
    Summary,
    Metrics,
    Finding,
    Refactoring,
    ExecutionMetadata,
    AgentRunDocument,
    RAGDocument
)


def test_code_review_document_schema():
    """Verify CodeReviewDocument instantiation and serialization."""
    doc = CodeReviewDocument(
        review_id="rev_123456",
        mode="quick",
        original_code="def hello(): return 'world'",
        input_metadata=InputMetadata(
            language="python",
            line_count=1,
            char_count=26,
            hash="abc123hash"
        ),
        summary=Summary(
            overview="Simple greeting function",
            verdict="clean",
            key_takeaways=["No bugs found", "Good code style"]
        ),
        metrics=Metrics(
            complexity_score=1.0,
            readability_score=9.5,
            maintainability_index="A",
            cyclomatic_complexity_est="Low"
        ),
        findings=[
            Finding(
                id="find-001",
                category="quality",
                severity="info",
                title="Code Style",
                description="Function return statement is concise."
            )
        ],
        refactoring=Refactoring(
            has_refactored_code=False,
            validation_status="passed"
        ),
        execution_metadata=ExecutionMetadata(
            total_duration_ms=450,
            llm_provider_used="gemini"
        )
    )

    assert doc.review_id == "rev_123456"
    assert doc.mode == "quick"
    assert doc.summary.verdict == "clean"
    assert len(doc.findings) == 1
    assert doc.findings[0].id == "find-001"
    
    data = doc.model_dump()
    assert data["review_id"] == "rev_123456"
    assert data["input_metadata"]["language"] == "python"


def test_agent_run_document_schema():
    """Verify AgentRunDocument instantiation."""
    agent_run = AgentRunDocument(
        run_id="run_999",
        review_id="rev_123456",
        agent_name="SecurityAgent",
        model_used="gemini-2.5-flash",
        duration_ms=120,
        status="success"
    )

    assert agent_run.run_id == "run_999"
    assert agent_run.agent_name == "SecurityAgent"
    assert agent_run.status == "success"


def test_rag_document_schema():
    """Verify RAGDocument schema instantiation and field validation."""
    rag_doc = RAGDocument(
        doc_id="rag_cwe_476",
        title="CWE-476: NULL Pointer Dereference",
        category="security",
        language="general",
        content="Validate pointers before dereferencing.",
        embedding=[0.1, 0.2, 0.3]
    )

    assert rag_doc.doc_id == "rag_cwe_476"
    assert rag_doc.category == "security"
    assert len(rag_doc.embedding) == 3
