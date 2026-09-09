from typing import Any, Dict
from backend.app.agents.base import BaseAgent, AgentResult
from backend.app.agents.prompts import CODE_ANALYSIS_PROMPT
from backend.app.agents.schemas import AnalysisOutput


class CodeAnalysisAgent(BaseAgent):
    """Parses code structural semantics, identifies primary function goals, and extracts modules."""

    def __init__(self):
        super().__init__(
            name="CodeAnalysisAgent",
            prompt_template=CODE_ANALYSIS_PROMPT,
            response_schema=AnalysisOutput,
            default_tier="flash"
        )

    async def analyze(self, code: str, language: str = "python") -> AgentResult:
        """Helper method to run code analysis."""
        return await self.invoke(inputs={"code": code, "language": language})


code_analysis_agent = CodeAnalysisAgent()
