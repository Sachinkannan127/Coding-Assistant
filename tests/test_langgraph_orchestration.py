import sys
from pathlib import Path
import pytest
from unittest.mock import AsyncMock, patch

root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from backend.app.graph import ReviewState, review_graph, run_review_workflow
from backend.app.agents.schemas import (
    AnalysisOutput, BugOutput, SecurityOutput, QualityOutput, ComplexityOutput, RefactoringOutput, SynthesisOutput, FindingSchema
)
from backend.app.services.llm.router import LLMResponse


@pytest.mark.asyncio
async def test_quick_mode_graph_execution():
    """Verify Quick Scan graph execution flow."""
    mock_analysis = LLMResponse(
        content=AnalysisOutput(overview="Quick overview", key_takeaways=["Takeaway 1"]),
        provider_used="gemini",
        model_name="gemini-2.5-flash"
    )
    mock_bugs = LLMResponse(
        content=BugOutput(findings=[]),
        provider_used="gemini",
        model_name="gemini-2.5-flash"
    )
    mock_synthesis = LLMResponse(
        content=SynthesisOutput(
            overview="Quick verdict", verdict="clean", key_takeaways=[],
            complexity_score=3.0, readability_score=9.0, maintainability_index="A",
            cyclomatic_complexity_est="Low", findings=[]
        ),
        provider_used="gemini",
        model_name="gemini-2.5-pro"
    )
    mock_refactor = LLMResponse(
        content=RefactoringOutput(refactored_code="x = 1\n", diff_summary="None"),
        provider_used="gemini",
        model_name="gemini-2.5-pro"
    )

    with patch("backend.app.agents.base.llm_router.generate", new_callable=AsyncMock) as mock_gen:
        def side_effect(*args, **kwargs):
            schema = kwargs.get("response_schema")
            if schema == AnalysisOutput:
                return mock_analysis
            elif schema == BugOutput:
                return mock_bugs
            elif schema == RefactoringOutput:
                return mock_refactor
            elif schema == SynthesisOutput:
                return mock_synthesis
            return mock_analysis

        mock_gen.side_effect = side_effect

        output = await run_review_workflow(
            review_id="rev-quick-001",
            original_code="x = 1\n",
            language="python",
            mode="quick"
        )

        assert output["verdict"] == "clean"
        assert output["refactored_code"] == "x = 1\n"


@pytest.mark.asyncio
async def test_deep_mode_graph_execution():
    """Verify Deep Review graph execution with parallel nodes & refactoring."""
    mock_analysis = LLMResponse(content=AnalysisOutput(overview="Deep overview", key_takeaways=[]), provider_used="gemini", model_name="gemini-2.5-flash")
    mock_bugs = LLMResponse(content=BugOutput(findings=[]), provider_used="gemini", model_name="gemini-2.5-flash")
    mock_security = LLMResponse(content=SecurityOutput(findings=[]), provider_used="gemini", model_name="gemini-2.5-flash")
    mock_quality = LLMResponse(content=QualityOutput(findings=[], readability_score=8.5), provider_used="gemini", model_name="gemini-2.5-flash")
    mock_complexity = LLMResponse(content=ComplexityOutput(findings=[], complexity_score=4.0, maintainability_index="A", cyclomatic_complexity_est="Low"), provider_used="gemini", model_name="gemini-2.5-flash")
    mock_refactor = LLMResponse(content=RefactoringOutput(refactored_code="def process():\n    return True\n", diff_summary="Refactored"), provider_used="gemini", model_name="gemini-2.5-pro")
    mock_synthesis = LLMResponse(content=SynthesisOutput(overview="Deep synthesis", verdict="clean", key_takeaways=[], complexity_score=4.0, readability_score=8.5, maintainability_index="A", cyclomatic_complexity_est="Low", findings=[]), provider_used="gemini", model_name="gemini-2.5-pro")

    with patch("backend.app.agents.base.llm_router.generate", new_callable=AsyncMock) as mock_gen:
        def side_effect(*args, **kwargs):
            schema = kwargs.get("response_schema")
            if schema == AnalysisOutput:
                return mock_analysis
            elif schema == BugOutput:
                return mock_bugs
            elif schema == SecurityOutput:
                return mock_security
            elif schema == QualityOutput:
                return mock_quality
            elif schema == ComplexityOutput:
                return mock_complexity
            elif schema == RefactoringOutput:
                return mock_refactor
            elif schema == SynthesisOutput:
                return mock_synthesis
            return mock_analysis

        mock_gen.side_effect = side_effect

        output = await run_review_workflow(
            review_id="rev-deep-001",
            original_code="def process():\n    return True\n",
            language="python",
            mode="deep"
        )

        assert output["verdict"] == "clean"
        assert output["validation_status"] in ["passed", "retried_passed"]


@pytest.mark.asyncio
async def test_validation_retry_loop_and_fallback():
    """Verify refactoring syntax error triggers retry and fallback to original code on max retries."""
    mock_analysis = LLMResponse(content=AnalysisOutput(overview="Overview", key_takeaways=[]), provider_used="gemini", model_name="gemini-2.5-flash")
    mock_bugs = LLMResponse(content=BugOutput(findings=[]), provider_used="gemini", model_name="gemini-2.5-flash")
    mock_security = LLMResponse(content=SecurityOutput(findings=[]), provider_used="gemini", model_name="gemini-2.5-flash")
    mock_quality = LLMResponse(content=QualityOutput(findings=[], readability_score=8.0), provider_used="gemini", model_name="gemini-2.5-flash")
    mock_complexity = LLMResponse(content=ComplexityOutput(findings=[], complexity_score=5.0, maintainability_index="B", cyclomatic_complexity_est="Low"), provider_used="gemini", model_name="gemini-2.5-flash")

    # Invalid Python syntax refactored code
    invalid_refactor = LLMResponse(content=RefactoringOutput(refactored_code="def broken_syntax(:\n    pass", diff_summary="Broken"), provider_used="gemini", model_name="gemini-2.5-pro")
    mock_synthesis = LLMResponse(content=SynthesisOutput(overview="Fallback overview", verdict="minor_issues", key_takeaways=[], complexity_score=5.0, readability_score=8.0, maintainability_index="B", cyclomatic_complexity_est="Low", findings=[]), provider_used="gemini", model_name="gemini-2.5-pro")

    with patch("backend.app.agents.base.llm_router.generate", new_callable=AsyncMock) as mock_gen:
        def side_effect(*args, **kwargs):
            schema = kwargs.get("response_schema")
            if schema == AnalysisOutput:
                return mock_analysis
            elif schema == BugOutput:
                return mock_bugs
            elif schema == SecurityOutput:
                return mock_security
            elif schema == QualityOutput:
                return mock_quality
            elif schema == ComplexityOutput:
                return mock_complexity
            elif schema == RefactoringOutput:
                return invalid_refactor
            elif schema == SynthesisOutput:
                return mock_synthesis
            return mock_analysis

        mock_gen.side_effect = side_effect

        output = await run_review_workflow(
            review_id="rev-fallback-001",
            original_code="def original():\n    pass\n",
            language="python",
            mode="deep"
        )

        assert output["validation_status"] == "fallback_original"
        assert output["refactored_code"] == "def original():\n    pass\n"
