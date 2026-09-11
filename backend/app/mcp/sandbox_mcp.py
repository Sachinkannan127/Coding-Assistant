"""
🧪 Sandbox / Execution MCP Connector Server.
Exposes isolated subprocess code execution and automated test suite execution tools.
"""

from typing import Dict, Any, List
from backend.app.services.sandbox_service import SandboxService


class SandboxMcpServer:
    SERVER_ID = "sandbox"
    NAME = "Sandbox Execution MCP"
    DESCRIPTION = "Isolated subprocess sandbox runner for Python, Node.js, C, C++, Java, Go, Rust code and automated test synthesis"
    CATEGORY = "Execution & Testing"

    @classmethod
    def get_tools(cls) -> List[Dict[str, Any]]:
        return [
            {
                "name": "run_code_sandbox",
                "description": "Executes code in isolated subprocess sandbox across 7 supported languages with standard input stream support.",
                "server_id": cls.SERVER_ID,
                "parameters": [
                    {"name": "code", "type": "string", "description": "Source code snippet to execute", "required": True},
                    {"name": "language", "type": "string", "description": "Programming language (python, javascript, c, cpp, java, go, rust)", "required": False, "default": "python"},
                    {"name": "stdin_data", "type": "string", "description": "Standard input data stream", "required": False, "default": ""},
                    {"name": "timeout_seconds", "type": "integer", "description": "Execution timeout ceiling", "required": False, "default": 5}
                ]
            },
            {
                "name": "generate_and_run_testcases",
                "description": "Synthesizes automated edge case test suite and runs them in parallel inside the execution sandbox.",
                "server_id": cls.SERVER_ID,
                "parameters": [
                    {"name": "code", "type": "string", "description": "Function source code to synthesize test cases for", "required": True},
                    {"name": "language", "type": "string", "description": "Target language", "required": False, "default": "python"},
                    {"name": "max_cases", "type": "integer", "description": "Maximum number of test cases to generate", "required": False, "default": 4}
                ]
            }
        ]

    @classmethod
    async def execute_tool(cls, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        code = args.get("code", "")
        if not code or not code.strip():
            raise ValueError("Parameter 'code' cannot be empty.")

        if tool_name == "run_code_sandbox":
            return await cls._run_code_sandbox(
                code=code,
                language=args.get("language", "python"),
                stdin_data=args.get("stdin_data", ""),
                timeout=int(args.get("timeout_seconds", 5))
            )
        elif tool_name == "generate_and_run_testcases":
            return await cls._generate_and_run_testcases(
                code=code,
                language=args.get("language", "python"),
                max_cases=int(args.get("max_cases", 4))
            )
        else:
            raise ValueError(f"Unknown tool '{tool_name}' for server '{cls.SERVER_ID}'")

    @classmethod
    async def _run_code_sandbox(cls, code: str, language: str = "python", stdin_data: str = "", timeout: int = 5) -> Dict[str, Any]:
        res = await SandboxService.execute_code(
            code=code,
            language=language,
            stdin_data=stdin_data,
            timeout_seconds=timeout
        )
        return res

    @classmethod
    async def _generate_and_run_testcases(cls, code: str, language: str = "python", max_cases: int = 4) -> Dict[str, Any]:
        from backend.app.services.testcase_gen_service import TestCaseGenService
        result = await TestCaseGenService.generate_and_run_tests(
            code_text=code,
            language=language,
            max_cases=max_cases
        )
        return result
