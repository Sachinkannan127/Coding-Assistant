from fastapi import APIRouter, HTTPException, status
from backend.app.api.schemas import (
    ExecutionRequest,
    ExecutionResponse,
    TestCaseRunRequest,
    TestCaseSuiteResponse,
    GenerateTestCasesRequest,
    GenerateTestCasesResponse
)
from backend.app.services.sandbox_service import SandboxService

sandbox_router = APIRouter()


@sandbox_router.post(
    "/sandbox/execute",
    response_model=ExecutionResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute Code in Isolated Sandbox",
    description="Asynchronously executes a source code snippet in an isolated subprocess environment with timeout bounds."
)
async def execute_code_in_sandbox(payload: ExecutionRequest):
    """
    Executes code snippet and returns stdout, stderr, execution time, and exit status.
    """
    if not payload.code or not payload.code.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Code snippet cannot be empty."
        )

    result = await SandboxService.execute_code(
        code=payload.code,
        language=payload.language,
        stdin_data=payload.stdin_data or "",
        timeout_seconds=payload.timeout_seconds or 5
    )

    return ExecutionResponse(**result)


@sandbox_router.post(
    "/sandbox/testcases",
    response_model=TestCaseSuiteResponse,
    status_code=status.HTTP_200_OK,
    summary="Run Test Cases Suite against Code",
    description="Executes source code against multiple test cases and evaluates actual vs expected output."
)
async def run_test_cases_endpoint(payload: TestCaseRunRequest):
    """
    Evaluates array of test cases against code snippet and returns test suite metrics.
    """
    if not payload.code or not payload.code.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Code snippet cannot be empty."
        )

    if not payload.test_cases:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Test cases list cannot be empty."
        )

    result = await SandboxService.run_test_cases(
        code=payload.code,
        language=payload.language,
        test_cases=payload.test_cases
    )

    return TestCaseSuiteResponse(**result)


@sandbox_router.post(
    "/sandbox/generate-testcases",
    response_model=GenerateTestCasesResponse,
    status_code=status.HTTP_200_OK,
    summary="Auto-Generate AI Test Cases for Code",
    description="Analyzes user source code, detects input parameters/streams, and generates tailored test cases with verified expected outputs."
)
async def generate_test_cases_endpoint(payload: GenerateTestCasesRequest):
    """
    Detects input logic in code and synthesizes tailored test cases.
    """
    if not payload.code or not payload.code.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Code snippet cannot be empty."
        )

    from backend.app.services.testcase_gen_service import TestCaseGenService

    return await TestCaseGenService.generate_test_cases(
        code=payload.code,
        language=payload.language,
        max_cases=payload.max_cases or 4
    )


