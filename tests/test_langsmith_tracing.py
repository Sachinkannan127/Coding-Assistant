import os
import sys
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from backend.app.services.tracing import TracingService, CodeReviewTelemetryCallbackHandler


def test_tracing_service_setup_enabled():
    """Verify setup_tracing() configures environment variables when enabled."""
    service = TracingService()

    with patch("backend.app.services.tracing.tracer.settings.LANGCHAIN_TRACING_V2", True), \
         patch("backend.app.services.tracing.tracer.settings.LANGCHAIN_API_KEY", "test_api_key_123"), \
         patch("backend.app.services.tracing.tracer.settings.LANGCHAIN_PROJECT", "test-project"):

        enabled = service.setup_tracing()
        assert enabled is True
        assert os.environ.get("LANGCHAIN_TRACING_V2") == "true"
        assert os.environ.get("LANGCHAIN_API_KEY") == "test_api_key_123"
        assert os.environ.get("LANGCHAIN_PROJECT") == "test-project"


def test_tracing_service_setup_disabled():
    """Verify setup_tracing() operates silently when tracing is disabled."""
    service = TracingService()

    with patch("backend.app.services.tracing.tracer.settings.LANGCHAIN_TRACING_V2", False):
        enabled = service.setup_tracing()
        assert enabled is False
        assert os.environ.get("LANGCHAIN_TRACING_V2") == "false"


def test_get_run_config():
    """Verify get_run_config constructs RunnableConfig dictionary with metadata & tags."""
    service = TracingService()
    config = service.get_run_config(review_id="rev-trace-001", mode="deep", language="python")

    assert config["metadata"]["review_id"] == "rev-trace-001"
    assert config["metadata"]["mode"] == "deep"
    assert "mode:deep" in config["tags"]
    assert "lang:python" in config["tags"]
    assert len(config["callbacks"]) == 1
    assert isinstance(config["callbacks"][0], CodeReviewTelemetryCallbackHandler)


def test_telemetry_callback_handler():
    """Verify CodeReviewTelemetryCallbackHandler hooks run without error."""
    handler = CodeReviewTelemetryCallbackHandler(review_id="rev-1", mode="quick", language="python")

    # Should run cleanly without raising exceptions
    handler.on_llm_start(serialized={"name": "ChatGoogleGenerativeAI"}, prompts=["Hello"])

    mock_response = MagicMock()
    mock_response.llm_output = {"token_usage": {"total_tokens": 150}}
    handler.on_llm_end(response=mock_response)

    handler.on_llm_error(error=RuntimeError("Test error"))
