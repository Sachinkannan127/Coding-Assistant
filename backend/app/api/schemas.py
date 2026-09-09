from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ReviewRequest(BaseModel):
    """Payload for code review submission."""
    code: str = Field(..., description="Source code snippet to analyze")
    language: str = Field(default="auto", description="Programming language / framework or 'auto'")
    mode: str = Field(default="quick", description="Review depth mode: 'quick' or 'deep'")


class ReviewListResponse(BaseModel):
    """Response list of recent code reviews."""
    reviews: List[Dict[str, Any]] = Field(default_factory=list, description="Array of review summaries")
    count: int = Field(..., description="Total number of returned reviews")
