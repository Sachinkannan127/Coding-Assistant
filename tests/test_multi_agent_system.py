import sys
from pathlib import Path
import pytest
from unittest.mock import AsyncMock, patch

root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from backend.app.agents import (
    code_analysis_agent,
    bug_detection_agent,
    security_agent,
    quality_agent,
    complexity_agent,
    refactoring_agent,
    synthesizer_agent,
    FindingSchema,
    AnalysisOutput,
    BugOutput,
    SecurityOutput,
    QualityOutput,
    ComplexityOutput,
    RefactoringOutput,
    SynthesisOutput,
)
from backend.app.services.llm.router import LLMResponse


@pytest.mark.asyncio
async def test_code_analysis_agent():
    """Verify CodeAnalysisAgent invocation and output model."""
    mock_res = LLMResponse(
        content=AnalysisOutput(overview="Test overview", key_takeaways=["Key 1"]),
        provider_used="gemini",
        model_name="gemini-2.5-flash"
    )
    with patch("backend.app.agents.base.llm_router.generate", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = mock_res
        res = await code_analysis_agent.analyze("def foo(): pass", language="python")
        assert res.agent_name == "CodeAnalysisAgent"
        assert res.output.overview == "Test overview"


@pytest.mark.asyncio
async def test_bug_detection_agent():
    """Verify BugDetectionAgent invocation and finding list."""
    finding = FindingSchema(
        id="bug-1", category="bug", severity="high", title="Null deref",
        description="Null pointer", line_start=5, line_end=5,
        code_snippet="x.y", suggestion="check null"
    )
    mock_res = LLMResponse(
        content=BugOutput(findings=[finding]),
        provider_used="gemini",
        model_name="gemini-2.5-flash"
    )
    with patch("backend.app.agents.base.llm_router.generate", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = mock_res
        res = await bug_detection_agent.detect_bugs("x.y", language="python")
        assert res.agent_name == "BugDetectionAgent"
        assert len(res.output.findings) == 1
        assert res.output.findings[0].cwe_or_rule_id is None


@pytest.mark.asyncio
async def test_security_agent():
    """Verify SecurityAgent invocation with CWE rule ID."""
    finding = FindingSchema(
        id="sec-1", category="security", severity="critical", title="SQL Injection",
        description="Unsanitized query", line_start=10, line_end=10,
        code_snippet="SELECT * FROM users", suggestion="Use parameterized query", cwe_or_rule_id="CWE-89"
    )
    mock_res = LLMResponse(
        content=SecurityOutput(findings=[finding]),
        provider_used="gemini",
        model_name="gemini-2.5-flash"
    )
    with patch("backend.app.agents.base.llm_router.generate", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = mock_res
        res = await security_agent.audit_security("query", language="python")
        assert res.agent_name == "SecurityAgent"
        assert res.output.findings[0].cwe_or_rule_id == "CWE-89"


@pytest.mark.asyncio
async def test_quality_and_complexity_agents():
    """Verify QualityReadabilityAgent and ComplexityAgent execution."""
    mock_quality = LLMResponse(
        content=QualityOutput(findings=[], readability_score=9.0),
        provider_used="gemini",
        model_name="gemini-2.5-flash"
    )
    mock_complexity = LLMResponse(
        content=ComplexityOutput(findings=[], complexity_score=3.5, maintainability_index="A", cyclomatic_complexity_est="Low"),
        provider_used="gemini",
        model_name="gemini-2.5-flash"
    )

    with patch("backend.app.agents.base.llm_router.generate", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = mock_quality
        q_res = await quality_agent.evaluate_quality("code", language="python")
        assert q_res.output.readability_score == 9.0

        mock_gen.return_value = mock_complexity
        c_res = await complexity_agent.analyze_complexity("code", language="python")
        assert c_res.output.complexity_score == 3.5
        assert c_res.output.maintainability_index == "A"


@pytest.mark.asyncio
async def test_refactoring_and_synthesizer_agents():
    """Verify RefactoringAgent and SynthesizerAgent (pro tier execution)."""
    mock_refactor = LLMResponse(
        content=RefactoringOutput(refactored_code="def bar(): return 42", diff_summary="Extracted constant"),
        provider_used="gemini",
        model_name="gemini-2.5-pro"
    )
    mock_synthesis = LLMResponse(
        content=SynthesisOutput(
            overview="Overall clean code", verdict="clean", key_takeaways=["Good code"],
            complexity_score=3.0, readability_score=9.0, maintainability_index="A",
            cyclomatic_complexity_est="Low", findings=[]
        ),
        provider_used="gemini",
        model_name="gemini-2.5-pro"
    )

    with patch("backend.app.agents.base.llm_router.generate", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = mock_refactor
        ref_res = await refactoring_agent.generate_refactoring("def bar(): return 42")
        assert ref_res.agent_name == "RefactoringAgent"
        assert ref_res.output.diff_summary == "Extracted constant"

        mock_gen.return_value = mock_synthesis
        syn_res = await synthesizer_agent.synthesize(code_overview="Overview", all_findings=[])
        assert syn_res.agent_name == "SynthesizerAgent"
        assert syn_res.output.verdict == "clean"
