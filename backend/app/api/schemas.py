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


class ExecutionRequest(BaseModel):
    """Payload for code sandbox execution request."""
    code: str = Field(..., description="Source code snippet to execute in sandbox")
    language: str = Field(default="python", description="Programming language (python, javascript, typescript, nodejs, c, cpp)")
    stdin_data: Optional[str] = Field(default="", description="Optional standard input string to pass to the process")
    timeout_seconds: Optional[int] = Field(default=5, description="Timeout ceiling in seconds (1 to 10)")


class ExecutionResponse(BaseModel):
    """Response returned from code sandbox execution."""
    stdout: str = Field(default="", description="Standard output captured from the process")
    stderr: str = Field(default="", description="Standard error captured from the process")
    exit_code: int = Field(default=0, description="Process exit code (0 indicates clean execution)")
    status: str = Field(..., description="Execution status: 'success', 'error', or 'timeout'")
    execution_time_ms: float = Field(..., description="Process execution duration in milliseconds")
    language_used: str = Field(..., description="Resolved programming language execution engine")


class ExplainRequest(BaseModel):
    """Payload for Explain Code request."""
    code: str = Field(..., description="Source code snippet to explain")
    language: str = Field(default="auto", description="Programming language identifier")
    audience: str = Field(default="simple", description="Target audience mode: 'simple' (kids/beginners), 'beginner' (students), 'developer' (experienced devs)")


class LineExplanation(BaseModel):
    """Line or block explanation step."""
    line_range: str = Field(..., description="Line number or line range string (e.g. 'Line 1' or 'Lines 3-5')")
    snippet: str = Field(..., description="Code snippet for this line range")
    explanation: str = Field(..., description="Plain English simple explanation for this line range")


class ExplainResponse(BaseModel):
    """Response payload for Explain Code request."""
    summary: str = Field(..., description="High-level plain English summary of what the code does")
    real_world_analogy: str = Field(..., description="Fun real-world metaphor explaining the code logic")
    line_by_line: List[LineExplanation] = Field(default_factory=list, description="Step-by-step line explanations")
    key_concepts: List[str] = Field(default_factory=list, description="Key concepts used in the code (e.g. Variables, Loops, If/Else)")
    audience: str = Field(default="simple", description="Audience mode used for explanation")


class TestCaseItem(BaseModel):
    """Individual test case definition."""
    id: int = Field(..., description="Test case unique ID")
    name: Optional[str] = Field(default="", description="Optional test case label or title")
    input_data: str = Field(default="", description="Input string fed to stdin")
    expected_output: str = Field(..., description="Expected output string to match against stdout")


class TestCaseRunRequest(BaseModel):
    """Payload to run a test suite against code."""
    code: str = Field(..., description="Source code snippet")
    language: str = Field(default="python", description="Programming language")
    test_cases: List[TestCaseItem] = Field(..., description="Array of test cases to evaluate")


class TestCaseRunResult(BaseModel):
    """Execution result for a single test case."""
    id: int = Field(..., description="Test case ID")
    name: str = Field(default="", description="Test case name")
    input_data: str = Field(default="", description="Input string provided")
    expected_output: str = Field(..., description="Expected output string")
    actual_output: str = Field(..., description="Actual stdout captured")
    passed: bool = Field(..., description="True if actual output matches expected output")
    execution_time_ms: float = Field(..., description="Execution duration in ms")
    status: str = Field(..., description="Status string ('PASSED', 'FAILED', 'TIMEOUT', 'ERROR')")


class TestCaseSuiteResponse(BaseModel):
    """Test suite execution summary response."""
    results: List[TestCaseRunResult] = Field(..., description="Results for each evaluated test case")
    total_tests: int = Field(..., description="Total count of test cases")
    passed_tests: int = Field(..., description="Number of passed test cases")
    success_rate: float = Field(..., description="Percentage of passed test cases (0.0 to 100.0)")


class GenerateTestCasesRequest(BaseModel):
    """Payload to request AI test case generation for a code snippet."""
    code: str = Field(..., description="Source code snippet to analyze")
    language: str = Field(default="python", description="Programming language")
    max_cases: int = Field(default=4, description="Maximum number of test cases to generate")


class GenerateTestCasesResponse(BaseModel):
    """Payload returned when test cases are generated with AI."""
    test_cases: List[TestCaseItem] = Field(..., description="List of generated test case items")
    reasoning: str = Field(default="", description="Explanation of detected inputs and edge case strategy")
    detected_inputs: List[str] = Field(default_factory=list, description="List of detected input variables or prompt patterns")




