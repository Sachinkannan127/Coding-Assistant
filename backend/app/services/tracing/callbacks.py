import logging
from typing import Any, Dict, List, Optional
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult

logger = logging.getLogger(__name__)


class CodeReviewTelemetryCallbackHandler(BaseCallbackHandler):
    """
    Custom LangChain / LangSmith Callback Handler for monitoring prompt inputs,
    LLM outputs, token usage, latency, and provider failovers.
    """

    def __init__(self, review_id: str, mode: str, language: str):
        super().__init__()
        self.review_id = review_id
        self.mode = mode
        self.language = language

    def on_llm_start(
        self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any
    ) -> None:
        """Fires when LLM starts execution."""
        name = serialized.get("name", "LLM")
        logger.debug(f"[{self.review_id}] LLM '{name}' started execution for language: '{self.language}'...")

    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        """Fires when LLM finishes execution."""
        llm_output = response.llm_output or {}
        token_usage = llm_output.get("token_usage", {})
        logger.debug(f"[{self.review_id}] LLM finished execution. Tokens: {token_usage}")

    def on_llm_error(self, error: BaseException, **kwargs: Any) -> None:
        """Fires when LLM encounters an exception."""
        logger.warning(f"[{self.review_id}] LLM execution error: {error}")
