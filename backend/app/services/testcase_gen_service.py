import json
import re
import asyncio
import logging
from typing import Dict, Any, List, Tuple
from backend.app.config import settings
from backend.app.api.schemas import TestCaseItem, GenerateTestCasesResponse
from backend.app.services.sandbox_service import SandboxService

logger = logging.getLogger(__name__)


class TestCaseGenService:
    """
    AI-powered Test Case Generation Engine.
    Analyzes code structure, detects input streams (stdin / interactive prompts),
    synthesizes edge cases & boundary conditions, and verifies outputs concurrently using the sandbox.
    """

    @classmethod
    async def generate_test_cases(
        cls,
        code: str,
        language: str = "python",
        max_cases: int = 4
    ) -> GenerateTestCasesResponse:
        """
        Generates AI test cases tailored to the given user source code snippet.
        """
        if not code or not code.strip():
            return GenerateTestCasesResponse(
                test_cases=[],
                reasoning="Empty code provided.",
                detected_inputs=[]
            )

        code_text = code.strip()
        lang = (language or "python").lower().strip()

        # Step 1: Detect input usage in code (e.g. input(), cin >>, scanf, readline)
        detected_inputs = cls._detect_inputs(code_text, lang)

        # Step 2: Attempt LLM (Gemini) test case generation
        candidate_cases: List[Dict[str, str]] = []
        reasoning = ""

        if settings.GEMINI_API_KEY and settings.GEMINI_API_KEY.strip():
            try:
                candidate_cases, reasoning = await cls._generate_llm_test_cases(code_text, lang, max_cases)
            except Exception as e:
                logger.warning(f"Gemini test case generation failed: {e}. Falling back to heuristic generator.")

        # Step 3: Fallback heuristic generator if LLM was skipped or returned empty
        if not candidate_cases:
            candidate_cases, reasoning = cls._generate_heuristic_test_cases(code_text, lang, detected_inputs, max_cases)

        # Step 4: Concurrent Sandbox Execution & Output Verification
        # Run all candidate test cases in parallel using asyncio.gather for maximum performance
        async def verify_single_case(idx: int, item: Dict[str, str]) -> TestCaseItem:
            name = item.get("name", f"Test Case {idx}")
            inp_data = item.get("input_data", "")
            exp_out = item.get("expected_output", "")

            try:
                exec_res = await SandboxService.execute_code(
                    code=code_text,
                    language=lang,
                    stdin_data=inp_data,
                    timeout_seconds=5
                )

                if exec_res.get("status") == "success" and exec_res.get("stdout"):
                    exp_out = exec_res.get("stdout", "").strip()
                elif exec_res.get("stderr") and not exp_out:
                    exp_out = exec_res.get("stderr", "").strip().split("\n")[-1]
            except Exception as ex:
                logger.debug(f"Sandbox verification error for case {idx}: {ex}")

            return TestCaseItem(
                id=idx,
                name=name,
                input_data=inp_data,
                expected_output=exp_out or "Clean Execution (Exit Code 0)"
            )

        verification_tasks = [
            verify_single_case(idx, item)
            for idx, item in enumerate(candidate_cases[:max_cases], start=1)
        ]
        
        verified_test_cases = await asyncio.gather(*verification_tasks)

        return GenerateTestCasesResponse(
            test_cases=list(verified_test_cases),
            reasoning=reasoning or f"Generated {len(verified_test_cases)} tailored test cases based on code analysis.",
            detected_inputs=detected_inputs
        )

    @classmethod
    def _detect_inputs(cls, code: str, lang: str) -> List[str]:
        """Detect input calls and variable prompts in user code."""
        detected = []
        
        # Python input patterns
        if "input(" in code or "sys.stdin" in code:
            matches = re.findall(r'(\w+)\s*=\s*(?:int|float|str)?\s*\(\s*input\(', code)
            if matches:
                detected.extend([f"stdin -> {m}" for m in matches])
            else:
                input_count = len(re.findall(r'input\(', code))
                detected.append(f"stdin (Python input() x{input_count or 1})")

        # JavaScript / TypeScript / Node patterns
        if "readline" in code or "process.stdin" in code or "prompt(" in code:
            detected.append("stdin (Node readline/prompt)")

        # C / C++ patterns
        if "scanf(" in code or "cin" in code or "fgets(" in code:
            matches = re.findall(r'cin\s*>>\s*(\w+)|scanf\([^,]+,\s*&(\w+)\)', code)
            if matches:
                detected.extend([f"stdin -> {m[0] or m[1]}" for m in matches])
            else:
                detected.append("stdin (C/C++ scanf/cin)")

        # Java patterns
        if "Scanner" in code or "BufferedReader" in code:
            detected.append("stdin (Java Scanner/Reader)")

        return list(set(detected))

    @classmethod
    async def _generate_llm_test_cases(
        cls,
        code: str,
        lang: str,
        max_cases: int
    ) -> Tuple[List[Dict[str, str]], str]:
        """Use Gemini LLM to analyze code logic and synthesize input/output test pairs."""
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=settings.GEMINI_API_KEY)

        system_instruction = (
            "You are an expert software QA engineer and compiler test synthesizer.\n"
            "Your task is to inspect the user's source code, detect its exact input expectations (`stdin`), "
            "and generate up to 4 DISTINCT and DIVERSE test cases.\n\n"
            "MUST INCLUDE A DIVERSE VARIETY OF TEST CASES:\n"
            "1. Standard / Typical Positive Case (normal operational inputs)\n"
            "2. Zero / Boundary Limit Case (0, empty string, boundary thresholds)\n"
            "3. Negative / Inverse Case (negative values, inverted flags, unexpected formats)\n"
            "4. Large / Complex Payload Case (large numeric inputs, multi-word text, combined data)\n\n"
            "CRITICAL stdin FORMATTING RULE:\n"
            "If the code makes N separate input calls (e.g. `a = int(input())` then `b = int(input())`), "
            "your `input_data` MUST contain exactly N lines separated by newline `\\n` (e.g. `10\\n20\\n`).\n\n"
            "Output MUST be valid JSON adhering strictly to this schema:\n"
            "{\n"
            '  "reasoning": "Detailed explanation of detected input structure and diverse test strategy",\n'
            '  "test_cases": [\n'
            '    {\n'
            '      "name": "Standard Positive Input",\n'
            '      "input_data": "10\\n20\\n",\n'
            '      "expected_output": "30"\n'
            '    }\n'
            '  ]\n'
            "}\n"
        )

        prompt = f"Language: {lang}\n\nSource Code:\n```\n{code}\n```"

        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.7,
            response_mime_type="application/json",
            response_schema=GenerateTestCasesResponse
        )

        model_name = settings.LLM_MODEL or "gemini-2.5-flash"
        response = await client.aio.models.generate_content(
            model=model_name,
            contents=prompt,
            config=config
        )

        # Support both parsed object and raw JSON string
        if hasattr(response, "parsed") and response.parsed:
            parsed_data = response.parsed
            if isinstance(parsed_data, GenerateTestCasesResponse):
                cases = [
                    {"name": tc.name, "input_data": tc.input_data, "expected_output": tc.expected_output}
                    for tc in parsed_data.test_cases
                ]
                return cases[:max_cases], parsed_data.reasoning

        text = response.text or ""
        data = json.loads(text)

        raw_cases = data.get("test_cases", [])
        cases = [
            {
                "name": item.get("name", f"Test Case {i}"),
                "input_data": item.get("input_data", ""),
                "expected_output": item.get("expected_output", "")
            }
            for i, item in enumerate(raw_cases, start=1)
        ]
        reasoning = data.get("reasoning", "")

        return cases[:max_cases], reasoning

    @classmethod
    def _generate_heuristic_test_cases(
        cls,
        code: str,
        lang: str,
        detected_inputs: List[str],
        max_cases: int
    ) -> Tuple[List[Dict[str, str]], str]:
        """Fall back to intelligent heuristic rule synthesis when LLM is unavailable."""
        cases = []
        
        # Count number of input prompts in Python / C / C++ / Java
        input_count = max(
            len(re.findall(r'input\(', code)),
            len(re.findall(r'cin\s*>>', code)),
            len(re.findall(r'scanf\(', code)),
            1 if detected_inputs else 0
        )

        if input_count > 0:
            # Generate multi-line payloads tailored to the number of input calls
            tc1_lines = ["10", "20", "30", "40", "50"][:input_count]
            tc2_lines = ["0", "0", "0", "0", "0"][:input_count]
            tc3_lines = ["-5", "-15", "-25", "-35", "-45"][:input_count]
            tc4_lines = ["1000", "2500", "5000", "7500", "10000"][:input_count]

            cases.append({
                "name": "Test Case 1: Typical Positive Payload",
                "input_data": "\n".join(tc1_lines) + "\n",
                "expected_output": ""
            })
            cases.append({
                "name": "Test Case 2: Zero / Boundary Condition",
                "input_data": "\n".join(tc2_lines) + "\n",
                "expected_output": ""
            })
            cases.append({
                "name": "Test Case 3: Negative / Edge Input",
                "input_data": "\n".join(tc3_lines) + "\n",
                "expected_output": ""
            })
            cases.append({
                "name": "Test Case 4: Large Scale Dataset",
                "input_data": "\n".join(tc4_lines) + "\n",
                "expected_output": ""
            })
            reasoning = f"Detected {input_count} distinct stdin input prompt(s). Synthesized diverse payloads: positive numbers, zero boundaries, negative values, and large scale data."
        else:
            # Code does not use interactive stdin (e.g. self-contained script or benchmark)
            cases.append({
                "name": "Test Case 1: Baseline Execution Test",
                "input_data": "",
                "expected_output": ""
            })
            cases.append({
                "name": "Test Case 2: Benchmark Verification",
                "input_data": "",
                "expected_output": ""
            })
            reasoning = "Program operates without stdin stream inputs. Generated baseline execution test cases to verify stdout return codes and runtime output."

        return cases[:max_cases], reasoning
