from typing import Any, Dict, List, Optional
from backend.app.agents.base import BaseAgent, AgentResult
from backend.app.agents.prompts import QUALITY_PROMPT
from backend.app.agents.schemas import QualityOutput


class QualityReadabilityAgent(BaseAgent):
    """Evaluates code naming conventions, modularity, DRY principles, and readability rating."""

    def __init__(self):
        super().__init__(
            name="QualityReadabilityAgent",
            prompt_template=QUALITY_PROMPT,
            response_schema=QualityOutput,
            default_tier="flash"
        )

    async def evaluate_quality(
        self,
        code: str,
        language: str = "python",
        rag_context: Optional[List[str]] = None
    ) -> AgentResult:
        """Helper method to run code quality evaluation."""
        context_str = "\n".join(rag_context) if rag_context else "None"
        return await self.invoke(inputs={
            "code": code,
            "language": language,
            "rag_context": context_str
        })


quality_agent = QualityReadabilityAgent()
