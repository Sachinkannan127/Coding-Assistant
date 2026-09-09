import json
from typing import Any, Dict, List, Optional
from backend.app.agents.base import BaseAgent, AgentResult
from backend.app.agents.prompts import REFACTORING_PROMPT
from backend.app.agents.schemas import RefactoringOutput, FindingSchema


class RefactoringAgent(BaseAgent):
    """Consolidates findings and RAG context to generate clean, idiomatic refactored code."""

    def __init__(self):
        super().__init__(
            name="RefactoringAgent",
            prompt_template=REFACTORING_PROMPT,
            response_schema=RefactoringOutput,
            default_tier="pro",
            temperature=0.1
        )

    async def generate_refactoring(
        self,
        code: str,
        language: str = "python",
        findings: Optional[List[FindingSchema]] = None,
        rag_context: Optional[List[str]] = None
    ) -> AgentResult:
        """Helper method to run refactoring generator."""
        findings_summary = json.dumps([f.model_dump() for f in findings], indent=2) if findings else "None"
        context_str = "\n".join(rag_context) if rag_context else "None"

        return await self.invoke(inputs={
            "code": code,
            "language": language,
            "findings_summary": findings_summary,
            "rag_context": context_str
        })


refactoring_agent = RefactoringAgent()
