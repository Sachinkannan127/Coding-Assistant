import time
import logging
from typing import Any, Dict, Optional, Type
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from backend.app.services.llm.router import llm_router, LLMResponse

logger = logging.getLogger(__name__)


class AgentResult(BaseModel):
    """Execution telemetry & result returned by BaseAgent.invoke()."""
    agent_name: str = Field(..., description="Name of agent that executed")
    output: Any = Field(..., description="Parsed Pydantic output model instance")
    provider_used: str = Field(..., description="LLM provider used ('gemini' or 'mistral')")
    model_name: str = Field(..., description="Specific model name used")
    duration_ms: int = Field(..., description="Total execution time in milliseconds")
    fallback_triggered: bool = Field(default=False, description="Whether fallback model was executed")
    error_message: Optional[str] = Field(default=None, description="Diagnostic message if fallback occurred")


class BaseAgent:
    """
    Base Agent class integrating ChatPromptTemplate, Pydantic response schema,
    and LLMRouter for dual-provider (Gemini + Mistral fallback) execution.
    """

    def __init__(
        self,
        name: str,
        prompt_template: ChatPromptTemplate,
        response_schema: Type[BaseModel],
        default_tier: str = "flash",
        temperature: float = 0.2
    ):
        self.name = name
        self.prompt_template = prompt_template
        self.response_schema = response_schema
        self.default_tier = default_tier
        self.temperature = temperature

    async def invoke(
        self,
        inputs: Dict[str, Any],
        tier: Optional[str] = None,
        temperature: Optional[float] = None
    ) -> AgentResult:
        """
        Formats prompt template with inputs and invokes LLM Router.

        Args:
            inputs: Variable values passed to prompt template.
            tier: Execution tier override ('flash' or 'pro'). Defaults to self.default_tier.
            temperature: Sampling temperature override. Defaults to self.temperature.

        Returns:
            AgentResult containing validated structured output model and telemetry.
        """
        selected_tier = tier or self.default_tier
        selected_temp = temperature if temperature is not None else self.temperature
        
        start_time = time.perf_counter()
        logger.info(f"Agent '{self.name}' starting execution (tier: '{selected_tier}')...")

        # 1. Format prompt template into LangChain messages
        formatted_prompt = self.prompt_template.format_messages(**inputs)

        # 2. Invoke LLMRouter with structured output response_schema
        llm_response: LLMResponse = await llm_router.generate(
            messages=formatted_prompt,
            tier=selected_tier,
            temperature=selected_temp,
            response_schema=self.response_schema
        )

        elapsed_ms = int((time.perf_counter() - start_time) * 1000)
        logger.info(
            f"Agent '{self.name}' finished in {elapsed_ms}ms using {llm_response.provider_used} ({llm_response.model_name})."
        )

        return AgentResult(
            agent_name=self.name,
            output=llm_response.content,
            provider_used=llm_response.provider_used,
            model_name=llm_response.model_name,
            duration_ms=elapsed_ms,
            fallback_triggered=llm_response.fallback_triggered,
            error_message=llm_response.error_message
        )
