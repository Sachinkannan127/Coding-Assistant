import pytest
from backend.app.services.sandbox_service import SandboxService


@pytest.mark.asyncio
async def test_python_sandbox_execution_success():
    code = "print('Hello CodePilot Sandbox!')\nx = 10 + 20\nprint(f'Result={x}')"
    result = await SandboxService.execute_code(code=code, language="python", timeout_seconds=5)

    assert result["status"] == "success"
    assert result["exit_code"] == 0
    assert "Hello CodePilot Sandbox!" in result["stdout"]
    assert "Result=30" in result["stdout"]
    assert result["execution_time_ms"] > 0


@pytest.mark.asyncio
async def test_python_sandbox_syntax_error():
    code = "def invalid_syntax(: \n    print('error')"
    result = await SandboxService.execute_code(code=code, language="python", timeout_seconds=5)

    assert result["status"] == "error"
    assert result["exit_code"] != 0
    assert "SyntaxError" in result["stderr"]


@pytest.mark.asyncio
async def test_sandbox_timeout_handling():
    code = "import time\ntime.sleep(10)"
    result = await SandboxService.execute_code(code=code, language="python", timeout_seconds=1)

    assert result["status"] == "timeout"
    assert result["exit_code"] == 124
    assert "Execution Timed Out" in result["stderr"]
