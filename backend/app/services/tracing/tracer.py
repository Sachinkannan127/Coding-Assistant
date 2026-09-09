import os
import logging
from typing import Dict, Any, Optional
from backend.app.config import settings
from backend.app.services.tracing.callbacks import CodeReviewTelemetryCallbackHandler

logger = logging.getLogger(__name__)


class TracingService:
    """
    LangSmith Observability & Tracing Service.
    Configures environment variables, project tags, and runnable execution configs.
    """

    def __init__(self):
        self._is_setup = False

    def setup_tracing(self) -> bool:
        """
        Configures LangSmith environment variables if LANGCHAIN_TRACING_V2 is enabled.
        Operates silently if disabled or API key is absent.
        """
        if settings.LANGCHAIN_TRACING_V2 and settings.LANGCHAIN_API_KEY.strip():
            os.environ["LANGCHAIN_TRACING_V2"] = "true"
            os.environ["LANGCHAIN_API_KEY"] = settings.LANGCHAIN_API_KEY.strip()
            os.environ["LANGCHAIN_PROJECT"] = settings.LANGCHAIN_PROJECT
            logger.info(f"LangSmith Tracing enabled for project: '{settings.LANGCHAIN_PROJECT}'")
            self._is_setup = True
            return True
        else:
            os.environ["LANGCHAIN_TRACING_V2"] = "false"
            self._is_setup = False
            return False

    def get_run_config(
        self,
        review_id: str,
        mode: str = "quick",
        language: str = "python"
    ) -> Dict[str, Any]:
        """
        Constructs RunnableConfig dictionary containing callbacks, metadata, and tags.
        """
        cb = CodeReviewTelemetryCallbackHandler(review_id=review_id, mode=mode, language=language)
        return {
            "configurable": {
                "thread_id": review_id,
            },
            "tags": [f"mode:{mode}", f"lang:{language}", f"env:{settings.ENVIRONMENT}"],
            "metadata": {
                "review_id": review_id,
                "mode": mode,
                "language": language,
                "environment": settings.ENVIRONMENT,
            },
            "callbacks": [cb]
        }


tracing_service = TracingService()
