from typing import Any, Dict, List, Optional
from backend.app.agents.base import BaseAgent, AgentResult
from backend.app.agents.prompts import BUG_DETECTION_PROMPT
from backend.app.agents.schemas import BugOutput


class BugDetectionAgent(BaseAgent):
    """Scans code for logic bugs, null pointer dereferences, resource leaks, and boundary failures."""

    def __init__(self):
        super().__init__(
            name="BugDetectionAgent",
            prompt_template=BUG_DETECTION_PROMPT,
            response_schema=BugOutput,
            default_tier="flash"
        )

    async def detect_bugs(
        self,
        code: str,
        language: str = "python",
        rag_context: Optional[List[str]] = None
    ) -> AgentResult:
        """Helper method to run bug detection."""
        context_str = "\n".join(rag_context) if rag_context else "None"
        return await self.invoke(inputs={
            "code": code,
            "language": language,
            "rag_context": context_str
        })


bug_detection_agent = BugDetectionAgent()
