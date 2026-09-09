from typing import Any, Dict, List, Optional
from backend.app.agents.base import BaseAgent, AgentResult
from backend.app.agents.prompts import SECURITY_PROMPT
from backend.app.agents.schemas import SecurityOutput


class SecurityAgent(BaseAgent):
    """Audits code against OWASP Top 10, CWE rules, injection risks, and insecure crypto."""

    def __init__(self):
        super().__init__(
            name="SecurityAgent",
            prompt_template=SECURITY_PROMPT,
            response_schema=SecurityOutput,
            default_tier="flash"
        )

    async def audit_security(
        self,
        code: str,
        language: str = "python",
        rag_context: Optional[List[str]] = None
    ) -> AgentResult:
        """Helper method to run security audit."""
        context_str = "\n".join(rag_context) if rag_context else "None"
        return await self.invoke(inputs={
            "code": code,
            "language": language,
            "rag_context": context_str
        })


security_agent = SecurityAgent()
