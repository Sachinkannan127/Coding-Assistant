from typing import Any, Dict
from backend.app.agents.base import BaseAgent, AgentResult
from backend.app.agents.prompts import COMPLEXITY_PROMPT
from backend.app.agents.schemas import ComplexityOutput


class ComplexityAgent(BaseAgent):
    """Calculates estimated cyclomatic complexity, cognitive load, and maintainability index."""

    def __init__(self):
        super().__init__(
            name="ComplexityAgent",
            prompt_template=COMPLEXITY_PROMPT,
            response_schema=ComplexityOutput,
            default_tier="flash"
        )

    async def analyze_complexity(self, code: str, language: str = "python") -> AgentResult:
        """Helper method to run complexity analysis."""
        return await self.invoke(inputs={"code": code, "language": language})


complexity_agent = ComplexityAgent()
