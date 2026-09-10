import pytest
from backend.app.api.schemas import TestCaseItem
from backend.app.services.sandbox_service import SandboxService


@pytest.mark.asyncio
async def test_run_test_cases_suite():
    code = """
import sys
input_data = sys.stdin.read().strip()
if input_data == "PING":
    print("PONG")
elif input_data == "HELLO":
    print("WORLD")
else:
    print("UNKNOWN")
"""
    test_cases = [
        TestCaseItem(id=1, name="Test Ping", input_data="PING", expected_output="PONG"),
        TestCaseItem(id=2, name="Test Hello", input_data="HELLO", expected_output="WORLD"),
        TestCaseItem(id=3, name="Test Mismatch", input_data="FOO", expected_output="BAR")
    ]

    res = await SandboxService.run_test_cases(code=code, language="python", test_cases=test_cases)

    assert res["total_tests"] == 3
    assert res["passed_tests"] == 2
    assert res["success_rate"] == 66.7
    assert res["results"][0]["passed"] is True
    assert res["results"][1]["passed"] is True
    assert res["results"][2]["passed"] is False
