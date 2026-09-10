import pytest
import pytest_asyncio
from backend.app.services.testcase_gen_service import TestCaseGenService


@pytest.mark.asyncio
async def test_generate_test_cases_interactive_python():
    """Verify test case generation for Python code with input()."""
    code = """
name = input("Enter name: ")
age = int(input("Enter age: "))
print(f"Hello {name}, in 5 years you will be {age + 5}")
"""
    result = await TestCaseGenService.generate_test_cases(code=code, language="python")
    
    assert result is not None
    assert len(result.test_cases) > 0
    assert len(result.detected_inputs) > 0
    assert result.reasoning != ""

    # Verify structure of test cases
    for case in result.test_cases:
        assert case.id > 0
        assert case.name != ""
        assert case.expected_output != ""


@pytest.mark.asyncio
async def test_generate_test_cases_script_without_inputs():
    """Verify test case generation for standalone script without stdin."""
    code = """
def fib(n):
    return n if n <= 1 else fib(n-1) + fib(n-2)

print("Fibonacci(10):", fib(10))
"""
    result = await TestCaseGenService.generate_test_cases(code=code, language="python")

    assert result is not None
    assert len(result.test_cases) >= 1
    # Standard script should verify clean execution
    assert result.test_cases[0].expected_output == "Fibonacci(10): 55"
