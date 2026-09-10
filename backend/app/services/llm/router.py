import time
import logging
from typing import Any, Dict, List, Optional, Type, Union
from pydantic import BaseModel, Field
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_mistralai import ChatMistralAI
from backend.app.config import settings, sanitize_credentials

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
            "flash": "gemini-3.6-flash",
            "pro": "gemini-3.6-flash",
        },
        "mistral": {
            "flash": "codestral-latest",
            "pro": "codestral-latest",
        }
    }

    def _init_gemini(self, tier: str, temperature: float) -> BaseChatModel:
        model_name = self.MODEL_MAP["gemini"].get(tier, "gemini-3.6-flash")
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

    def _init_provider(self, provider: str, tier: str, temperature: float) -> BaseChatModel:
        if provider == "gemini":
            return self._init_gemini(tier=tier, temperature=temperature)
        else:
            return self._init_mistral(tier=tier, temperature=temperature)

    async def generate(
        self,
        messages: Union[str, List[Any]],
        tier: str = "flash",
        temperature: float = 0.2,
        response_schema: Optional[Type[BaseModel]] = None
    ) -> LLMResponse:
        """
        Execute LLM generation with dynamic primary and fallback provider routing based on execution tier:
        - Tier 'flash' / 'mini': Primary is Google Gemini (gemini-2.5-flash) with Mistral fallback.
        - Tier 'pro' / 'deep': Primary is Mistral AI (mistral-large-latest) with Gemini fallback.
        """
        formatted_messages = self._format_messages(messages)
        start_time = time.perf_counter()
        primary_error_msg: Optional[str] = None

        # Determine primary and fallback providers based on tier selection
        clean_tier = tier.lower().strip() if tier else "flash"
        if clean_tier == "pro":
            primary_provider = "mistral"
            fallback_provider = "gemini"
        else:
            primary_provider = "gemini"
            fallback_provider = "mistral"

        # 1. Attempt Primary Provider
        try:
            logger.info(f"Invoking primary LLM provider ('{primary_provider}' - tier: '{clean_tier}')...")
            primary_model = self._init_provider(provider=primary_provider, tier=clean_tier, temperature=temperature)
            
            if response_schema:
                runnable = primary_model.with_structured_output(response_schema)
                raw_response = await runnable.ainvoke(formatted_messages)
                content = raw_response
            else:
                raw_response = await primary_model.ainvoke(formatted_messages)
                content = raw_response.content

            elapsed_ms = int((time.perf_counter() - start_time) * 1000)
            model_name = self.MODEL_MAP[primary_provider].get(clean_tier, self.MODEL_MAP[primary_provider]["flash"])
            
            return LLMResponse(
                content=content,
                provider_used=primary_provider,
                model_name=model_name,
                fallback_triggered=False,
                duration_ms=elapsed_ms
            )

        except Exception as primary_error:
            primary_error_msg = sanitize_credentials(str(primary_error))
            logger.warning(f"Primary '{primary_provider}' provider failed ({primary_error_msg}). Initiating '{fallback_provider}' fallback...")

        # 2. Attempt Fallback Provider
        try:
            logger.info(f"Invoking fallback LLM provider ('{fallback_provider}' - tier: '{clean_tier}')...")
            fallback_model = self._init_provider(provider=fallback_provider, tier=clean_tier, temperature=temperature)

            if response_schema:
                runnable = fallback_model.with_structured_output(response_schema)
                raw_response = await runnable.ainvoke(formatted_messages)
                content = raw_response
            else:
                raw_response = await fallback_model.ainvoke(formatted_messages)
                content = raw_response.content

            elapsed_ms = int((time.perf_counter() - start_time) * 1000)
            model_name = self.MODEL_MAP[fallback_provider].get(clean_tier, self.MODEL_MAP[fallback_provider]["flash"])

            return LLMResponse(
                content=content,
                provider_used=fallback_provider,
                model_name=model_name,
                fallback_triggered=True,
                duration_ms=elapsed_ms,
                error_message=primary_error_msg
            )

        except Exception as fallback_error:
            elapsed_ms = int((time.perf_counter() - start_time) * 1000)
            fallback_error_msg = sanitize_credentials(str(fallback_error))
            logger.error(f"Both primary ('{primary_provider}') and fallback ('{fallback_provider}') LLM providers failed: {fallback_error_msg}")
            raise RuntimeError(
                f"LLM Router generation failed. Primary ({primary_provider}): {primary_error_msg} | Fallback ({fallback_provider}): {fallback_error_msg}"
            ) from fallback_error


llm_router = LLMRouter()
