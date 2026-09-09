import json
from typing import Any, Dict, List, Optional
from backend.app.agents.base import BaseAgent, AgentResult
from backend.app.agents.prompts import SYNTHESIS_PROMPT
from backend.app.agents.schemas import SynthesisOutput, FindingSchema


class SynthesizerAgent(BaseAgent):
    """Aggregates, deduplicates findings, and computes unified risk score."""

    def __init__(self):
        super().__init__(
            name="SynthesizerAgent",
            prompt_template=SYNTHESIS_PROMPT,
            response_schema=SynthesisOutput,
            default_tier="pro",
            temperature=0.1
        )

    async def synthesize(
        self,
        code_overview: str,
        all_findings: List[FindingSchema],
        readability_score: float = 8.0,
        complexity_score: float = 5.0,
        language: str = "python"
    ) -> AgentResult:
        """Helper method to run synthesis."""
        findings_json = json.dumps([f.model_dump() for f in all_findings], indent=2)
        return await self.invoke(inputs={
            "language": language,
            "code_overview": code_overview,
            "all_findings": findings_json,
            "readability_score": readability_score,
            "complexity_score": complexity_score
        })


synthesizer_agent = SynthesizerAgent()
