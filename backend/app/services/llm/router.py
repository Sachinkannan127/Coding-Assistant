import time
import logging
from typing import Any, Dict, List, Optional, Type, Union
from pydantic import BaseModel, Field
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_mistralai import ChatMistralAI
from backend.app.config import settings

logger = logging.getLogger(__name__)


class LLMResponse(BaseModel):
    """Unified response object returned by LLM Router."""
    content: Any = Field(..., description="Raw text output or parsed structured object")
    provider_used: str = Field(..., description="Provider that produced response ('gemini' or 'mistral')")
    model_name: str = Field(..., description="Specific model name used")
    fallback_triggered: bool = Field(default=False, description="Whether fallback provider was executed")
    duration_ms: int = Field(default=0, description="Response generation duration in milliseconds")
    error_message: Optional[str] = Field(default=None, description="Diagnostic error details if fallback occurred")


class LLMRouter:
    """
    LLM Router Service.
    Orchestrates primary Google Gemini LLM calls and automatic fallback to Mistral AI
    on connection timeouts (>15s), HTTP errors (429, 500, 503), or provider exceptions.
    """

    PRIMARY_PROVIDER = "gemini"
    FALLBACK_PROVIDER = "mistral"

    MODEL_MAP = {
        "gemini": {
            "flash": "gemini-2.5-flash",
            "pro": "gemini-2.5-pro",
        },
        "mistral": {
            "flash": "codestral-latest",
            "pro": "mistral-large-latest",
        }
    }

    def _init_gemini(self, tier: str, temperature: float) -> BaseChatModel:
        model_name = self.MODEL_MAP["gemini"].get(tier, "gemini-2.5-flash")
        api_key = settings.GEMINI_API_KEY.strip()
        if not api_key:
            raise ValueError("GEMINI_API_KEY is missing or empty.")
        return ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=api_key,
            temperature=temperature,
            timeout=15.0,
            max_retries=1
        )

    def _init_mistral(self, tier: str, temperature: float) -> BaseChatModel:
        model_name = self.MODEL_MAP["mistral"].get(tier, "codestral-latest")
        api_key = settings.MISTRAL_API_KEY.strip()
        if not api_key:
            raise ValueError("MISTRAL_API_KEY is missing or empty.")
        return ChatMistralAI(
            model=model_name,
            mistral_api_key=api_key,
            temperature=temperature,
            timeout=15.0,
            max_retries=1
        )

    def _format_messages(self, messages: Union[str, List[Any]]) -> List[BaseMessage]:
        if isinstance(messages, str):
            return [HumanMessage(content=messages)]
        
        formatted = []
        for msg in messages:
            if isinstance(msg, BaseMessage):
                formatted.append(msg)
            elif isinstance(msg, dict):
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if role == "system":
                    formatted.append(SystemMessage(content=content))
                elif role == "assistant":
                    formatted.append(AIMessage(content=content))
                else:
                    formatted.append(HumanMessage(content=content))
            else:
                formatted.append(HumanMessage(content=str(msg)))
        return formatted

    async def generate(
        self,
        messages: Union[str, List[Any]],
        tier: str = "flash",
        temperature: float = 0.2,
        response_schema: Optional[Type[BaseModel]] = None
    ) -> LLMResponse:
        """
        Execute LLM generation with primary Gemini model and fallback to Mistral.
        
        Args:
            messages: Prompt string or list of LangChain/dictionary messages.
            tier: Execution tier ('flash' for rapid speed, 'pro' for deep reasoning).
            temperature: LLM sampling temperature.
            response_schema: Optional Pydantic model for structured output parsing.

        Returns:
            LLMResponse object containing generated output and telemetry metadata.
        """
        formatted_messages = self._format_messages(messages)
        start_time = time.perf_counter()
        primary_error_msg: Optional[str] = None

        # 1. Attempt Primary Provider: Google Gemini
        try:
            logger.info(f"Invoking primary LLM provider (Gemini - tier: '{tier}')...")
            gemini_model = self._init_gemini(tier=tier, temperature=temperature)
            
            if response_schema:
                runnable = gemini_model.with_structured_output(response_schema)
                raw_response = await runnable.ainvoke(formatted_messages)
                content = raw_response
            else:
                raw_response = await gemini_model.ainvoke(formatted_messages)
                content = raw_response.content

            elapsed_ms = int((time.perf_counter() - start_time) * 1000)
            model_name = self.MODEL_MAP["gemini"].get(tier, "gemini-2.5-flash")
            
            return LLMResponse(
                content=content,
                provider_used="gemini",
                model_name=model_name,
                fallback_triggered=False,
                duration_ms=elapsed_ms
            )

        except Exception as primary_error:
            primary_error_msg = str(primary_error)
            logger.warning(f"Primary Gemini provider failed ({primary_error_msg}). Initiating Mistral fallback...")

        # 2. Attempt Fallback Provider: Mistral AI
        try:
            logger.info(f"Invoking fallback LLM provider (Mistral - tier: '{tier}')...")
            mistral_model = self._init_mistral(tier=tier, temperature=temperature)

            if response_schema:
                runnable = mistral_model.with_structured_output(response_schema)
                raw_response = await runnable.ainvoke(formatted_messages)
                content = raw_response
            else:
                raw_response = await mistral_model.ainvoke(formatted_messages)
                content = raw_response.content

            elapsed_ms = int((time.perf_counter() - start_time) * 1000)
            model_name = self.MODEL_MAP["mistral"].get(tier, "codestral-latest")

            return LLMResponse(
                content=content,
                provider_used="mistral",
                model_name=model_name,
                fallback_triggered=True,
                duration_ms=elapsed_ms,
                error_message=primary_error_msg
            )

        except Exception as fallback_error:
            elapsed_ms = int((time.perf_counter() - start_time) * 1000)
            fallback_error_msg = str(fallback_error)
            logger.error(f"Both primary (Gemini) and fallback (Mistral) LLM providers failed: {fallback_error_msg}")
            raise RuntimeError(
                f"LLM Router generation failed. Primary (Gemini): {primary_error_msg} | Fallback (Mistral): {fallback_error_msg}"
            ) from fallback_error


llm_router = LLMRouter()
