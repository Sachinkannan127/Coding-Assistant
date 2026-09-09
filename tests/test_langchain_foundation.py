import sys
from pathlib import Path
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from backend.app.agents import (
    FindingSchema,
    AnalysisOutput,
    BugOutput,
    SecurityOutput,
    QualityOutput,
    ComplexityOutput,
    RefactoringOutput,
    SynthesisOutput,
    CODE_ANALYSIS_PROMPT,
    BUG_DETECTION_PROMPT,
    BaseAgent,
    AgentResult,
)
from backend.app.services.llm.router import LLMResponse


def test_finding_schema_validation():
    """Verify FindingSchema instantiation and defaults."""
    finding = FindingSchema(
        id="find-101",
        category="bug",
        severity="high",
        title="Null Pointer Dereference",
        description="Accessing user object before null check on line 12",
        line_start=12,
        line_end=14,
        code_snippet="user.getProfile().name",
        suggestion="Add null check before accessing getProfile()",
        cwe_or_rule_id="CWE-476"
    )
    assert finding.id == "find-101"
    assert finding.category == "bug"
    assert finding.cwe_or_rule_id == "CWE-476"


def test_agent_output_schemas():
    """Verify instantiation of all agent output schemas."""
    analysis = AnalysisOutput(overview="Data processing code", key_takeaways=["Takes dict", "Returns list"])
    assert len(analysis.key_takeaways) == 2

    quality = QualityOutput(findings=[], readability_score=8.5)
    assert quality.readability_score == 8.5

    complexity = ComplexityOutput(findings=[], complexity_score=4.2, maintainability_index="A", cyclomatic_complexity_est="Low")
    assert complexity.maintainability_index == "A"

    refactoring = RefactoringOutput(refactored_code="def clean(): pass", diff_summary="Simplified loop")
    assert refactoring.refactored_code == "def clean(): pass"


def test_prompt_template_formatting():
    """Verify formatting of ChatPromptTemplate instances."""
    messages = CODE_ANALYSIS_PROMPT.format_messages(language="python", code="x = 10")
    assert len(messages) == 2
    assert "x = 10" in messages[0].content


@pytest.mark.asyncio
async def test_base_agent_invoke():
    """Verify BaseAgent execution with LLMRouter mock."""
    mock_output = AnalysisOutput(overview="Mock overview", key_takeaways=["Point 1"])
    mock_llm_response = LLMResponse(
        content=mock_output,
        provider_used="gemini",
        model_name="gemini-2.5-flash",
        fallback_triggered=False,
        duration_ms=120
    )

    agent = BaseAgent(
        name="CodeAnalysisAgent",
        prompt_template=CODE_ANALYSIS_PROMPT,
        response_schema=AnalysisOutput,
        default_tier="flash"
    )

    with patch("backend.app.agents.base.llm_router.generate", new_callable=AsyncMock) as mock_generate:
        mock_generate.return_value = mock_llm_response

        res: AgentResult = await agent.invoke(inputs={"language": "python", "code": "def test(): pass"})

        assert res.agent_name == "CodeAnalysisAgent"
        assert res.provider_used == "gemini"
        assert res.model_name == "gemini-2.5-flash"
        assert res.output.overview == "Mock overview"
        assert res.fallback_triggered is False
        mock_generate.assert_called_once()
