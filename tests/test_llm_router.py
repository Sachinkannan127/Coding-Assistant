import sys
from pathlib import Path
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pydantic import BaseModel

# Ensure root directory is in sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from backend.app.services.llm.router import LLMRouter, LLMResponse


class SampleStructuredOutput(BaseModel):
    summary: str
    score: float


def test_llm_router_model_mapping():
    """Verify tier to model name mapping for both providers."""
    router = LLMRouter()
    assert router.MODEL_MAP["gemini"]["flash"] == "gemini-2.5-flash"
    assert router.MODEL_MAP["gemini"]["pro"] == "gemini-2.5-pro"
    assert router.MODEL_MAP["mistral"]["flash"] == "codestral-latest"
    assert router.MODEL_MAP["mistral"]["pro"] == "mistral-large-latest"


def test_format_messages():
    """Verify message normalization for strings, dicts, and BaseMessages."""
    router = LLMRouter()
    
    # Single string input
    msgs1 = router._format_messages("Hello LLM")
    assert len(msgs1) == 1
    assert msgs1[0].content == "Hello LLM"
    
    # Dict messages input
    dict_msgs = [
        {"role": "system", "content": "You are a code reviewer."},
        {"role": "user", "content": "Analyze code."}
    ]
    msgs2 = router._format_messages(dict_msgs)
    assert len(msgs2) == 2
    assert msgs2[0].content == "You are a code reviewer."
    assert msgs2[1].content == "Analyze code."


@pytest.mark.asyncio
async def test_generate_primary_gemini_success():
    """Verify successful generation using primary Gemini provider."""
    router = LLMRouter()

    mock_gemini_response = MagicMock()
    mock_gemini_response.content = "Gemini response text"
    
    mock_gemini_model = MagicMock()
    mock_gemini_model.ainvoke = AsyncMock(return_value=mock_gemini_response)

    with patch.object(router, "_init_gemini", return_value=mock_gemini_model):
        res = await router.generate(messages="Test prompt", tier="flash")
        
        assert res.provider_used == "gemini"
        assert res.model_name == "gemini-2.5-flash"
        assert res.fallback_triggered is False
        assert res.content == "Gemini response text"
        assert res.duration_ms >= 0


@pytest.mark.asyncio
async def test_generate_fallback_to_mistral():
    """Verify automatic fallback to Mistral when primary Gemini raises exception."""
    router = LLMRouter()

    mock_mistral_response = MagicMock()
    mock_mistral_response.content = "Mistral fallback response"

    mock_mistral_model = MagicMock()
    mock_mistral_model.ainvoke = AsyncMock(return_value=mock_mistral_response)

    # Gemini throws exception, Mistral succeeds
    with patch.object(router, "_init_gemini", side_effect=RuntimeError("Gemini Rate Limit 429")), \
         patch.object(router, "_init_mistral", return_value=mock_mistral_model):
        
        res = await router.generate(messages="Test prompt", tier="flash")

        assert res.provider_used == "mistral"
        assert res.model_name == "codestral-latest"
        assert res.fallback_triggered is True
        assert res.content == "Mistral fallback response"
        assert "Gemini Rate Limit 429" in res.error_message


@pytest.mark.asyncio
async def test_generate_both_providers_fail():
    """Verify RuntimeError is raised when both primary and fallback providers fail."""
    router = LLMRouter()

    with patch.object(router, "_init_gemini", side_effect=RuntimeError("Gemini Timeout")), \
         patch.object(router, "_init_mistral", side_effect=RuntimeError("Mistral 500 Server Error")):

        with pytest.raises(RuntimeError) as exc_info:
            await router.generate(messages="Test prompt", tier="pro")
        
        assert "LLM Router generation failed" in str(exc_info.value)
        assert "Gemini Timeout" in str(exc_info.value)
        assert "Mistral 500 Server Error" in str(exc_info.value)


@pytest.mark.asyncio
async def test_generate_structured_output():
    """Verify structured output parsing using response_schema."""
    router = LLMRouter()

    structured_data = SampleStructuredOutput(summary="Clean code", score=9.8)
    
    mock_runnable = MagicMock()
    mock_runnable.ainvoke = AsyncMock(return_value=structured_data)

    mock_gemini_model = MagicMock()
    mock_gemini_model.with_structured_output.return_value = mock_runnable

    with patch.object(router, "_init_gemini", return_value=mock_gemini_model):
        res = await router.generate(
            messages="Analyze complexity",
            tier="pro",
            response_schema=SampleStructuredOutput
        )

        assert res.provider_used == "gemini"
        assert res.content.summary == "Clean code"
        assert res.content.score == 9.8
