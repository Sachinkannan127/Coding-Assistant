import asyncio
import os
import sys
import time
import tempfile
import shutil
import subprocess
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Maximum character size allowed for sandbox execution code
MAX_CODE_SIZE = 50000


def _run_subprocess_sync(cmd: list, stdin_data: str, cwd: str, timeout: int) -> Dict[str, Any]:
    """
    Synchronous helper function to run subprocess safely with timeout and stream capture.
    Executes inside asyncio.to_thread thread pool worker to ensure event loop compatibility
    across Windows, Linux, and macOS without raising asyncio NotImplementedError.
    """
    start_time = time.perf_counter()
    env = {
        **os.environ,
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONIOENCODING": "utf-8",
        "PYTHONUTF8": "1"
    }

    try:
        proc = subprocess.run(
            cmd,
            input=stdin_data if stdin_data else None,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            cwd=cwd,
            env=env
        )
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        return {
            "stdout": proc.stdout or "",
            "stderr": proc.stderr or "",
            "exit_code": proc.returncode,
            "status": "success" if proc.returncode == 0 else "error",
            "execution_time_ms": round(elapsed_ms, 2)
        }

    except subprocess.TimeoutExpired as te:
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        stdout_str = te.stdout if isinstance(te.stdout, str) else (te.stdout.decode('utf-8', errors='replace') if te.stdout else "")
        stderr_str = te.stderr if isinstance(te.stderr, str) else (te.stderr.decode('utf-8', errors='replace') if te.stderr else "")

        return {
            "stdout": stdout_str,
            "stderr": f"⏱️ Execution Timed Out: Process exceeded runtime limit of {timeout} seconds.\n{stderr_str}".strip(),
            "exit_code": 124, # Standard timeout exit code
            "status": "timeout",
            "execution_time_ms": round(elapsed_ms, 2)
        }

    except Exception as e:
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        return {
            "stdout": "",
            "stderr": f"Execution Failure: {str(e)}",
            "exit_code": 1,
            "status": "error",
            "execution_time_ms": round(elapsed_ms, 2)
        }


class SandboxService:
    """
    Subprocess Code Execution Sandbox Service.
    Executes submitted source code snippets in isolated temporary workspace directories
    with process timeout enforcement, resource controls, and stream capture.
    """

    @classmethod
    def resolve_executable(cls, language: str) -> Dict[str, Any]:
        """
        Maps requested language identifier to runtime command, file extension, and mode.
        """
        lang = (language or "python").lower().strip()

        if lang in ["python", "python3", "py", "auto"]:
            return {
                "runner": sys.executable, # Use active python environment
                "ext": ".py",
                "mode": "script",
                "lang_name": "python"
            }
        elif lang in ["javascript", "js", "node", "nodejs", "react", "nextjs"]:
            node_path = shutil.which("node")
            if node_path:
                return {
                    "runner": node_path,
                    "ext": ".js",
                    "mode": "script",
                    "lang_name": "javascript"
                }
            else:
                return {
                    "runner": sys.executable,
                    "ext": ".py",
                    "mode": "script",
                    "lang_name": "python (fallback)"
                }
        elif lang in ["typescript", "ts"]:
            ts_node_path = shutil.which("ts-node")
            node_path = shutil.which("node")
            if ts_node_path:
                return {
                    "runner": ts_node_path,
                    "ext": ".ts",
                    "mode": "script",
                    "lang_name": "typescript"
                }
            elif node_path:
                return {
                    "runner": node_path,
                    "ext": ".js",
                    "mode": "script",
                    "lang_name": "javascript (node)"
                }
            else:
                return {
                    "runner": sys.executable,
                    "ext": ".py",
                    "mode": "script",
                    "lang_name": "python (fallback)"
                }
        elif lang in ["c", "cpp", "c++"]:
            gcc_path = shutil.which("gcc") or shutil.which("g++") or shutil.which("clang")
            if gcc_path:
                return {
                    "runner": gcc_path,
                    "ext": ".c" if lang == "c" else ".cpp",
                    "mode": "compile_c",
                    "lang_name": lang
                }
            else:
                return {
                    "runner": sys.executable,
                    "ext": ".py",
                    "mode": "script",
                    "lang_name": "python (fallback)"
                }
        elif lang in ["java"]:
            javac_path = shutil.which("javac")
            java_path = shutil.which("java")
            if javac_path and java_path:
                return {
                    "runner": javac_path,
                    "ext": ".java",
                    "mode": "compile_java",
                    "lang_name": "java"
                }
            else:
                return {
                    "runner": sys.executable,
                    "ext": ".py",
                    "mode": "script",
                    "lang_name": "python (fallback)"
                }
        elif lang in ["go", "golang"]:
            go_path = shutil.which("go")
            if go_path:
                return {
                    "runner": go_path,
                    "ext": ".go",
                    "mode": "go_run",
                    "lang_name": "go"
                }
            else:
                return {
                    "runner": sys.executable,
                    "ext": ".py",
                    "mode": "script",
                    "lang_name": "python (fallback)"
                }
        elif lang in ["rust", "rs"]:
            rustc_path = shutil.which("rustc")
            if rustc_path:
                return {
                    "runner": rustc_path,
                    "ext": ".rs",
                    "mode": "compile_rust",
                    "lang_name": "rust"
                }
            else:
                return {
                    "runner": sys.executable,
                    "ext": ".py",
                    "mode": "script",
                    "lang_name": "python (fallback)"
                }
        else:
            return {
                "runner": sys.executable,
                "ext": ".py",
                "mode": "script",
                "lang_name": "python"
            }

    @classmethod
    async def execute_code(
        cls,
        code: str,
        language: str = "python",
        stdin_data: str = "",
        timeout_seconds: int = 5
    ) -> Dict[str, Any]:
        """
        Executes code snippet asynchronously in an isolated sandbox environment.
        """
        # Clamp timeout between 1 and 10 seconds
        timeout = max(1, min(int(timeout_seconds or 5), 10))

        if not code or not code.strip():
            return {
                "stdout": "",
                "stderr": "Error: Empty code payload provided.",
                "exit_code": 1,
                "status": "error",
                "execution_time_ms": 0.0,
                "language_used": language
            }

        if len(code) > MAX_CODE_SIZE:
            return {
                "stdout": "",
                "stderr": f"Error: Code payload exceeds sandbox limit ({len(code)} > {MAX_CODE_SIZE} chars).",
                "exit_code": 1,
                "status": "error",
                "execution_time_ms": 0.0,
                "language_used": language
            }

        exec_config = cls.resolve_executable(language)
        runner = exec_config["runner"]
        ext = exec_config["ext"]
        mode = exec_config["mode"]
        lang_name = exec_config["lang_name"]

        # Create isolated temporary workspace
        with tempfile.TemporaryDirectory(prefix="codepilot_sandbox_") as tmp_dir:
            filename = "Main.java" if mode == "compile_java" else f"main{ext}"
            file_path = os.path.join(tmp_dir, filename)

            # If code is Python and contains function definitions without print statements, append auto-driver invocation
            code_to_run = code
            if ext == ".py" and "print(" not in code and "print (" not in code:
                code_to_run += """

# Auto-generated Sandbox Driver for function execution
if __name__ == '__main__':
    g_vars = list(globals().items())
    for name, func in g_vars:
        if callable(func) and not name.startswith('_'):
            try:
                import inspect
                sig = inspect.signature(func)
                params = sig.parameters
                if len(params) == 0:
                    val = func()
                    print(f"Executed {name}() ->", val)
                elif len(params) == 2:
                    sample_user = {"role": "VIP", "username": "admin", "config": "{}"}
                    sample_cart = [{"price": 100, "quantity": 2}, {"price": 50, "quantity": 1}]
                    val = func(sample_user, sample_cart)
                    print(f"Executed {name}(user, cart_items) ->", val)
            except Exception as _e:
                pass
"""

            # Write code payload to temporary file
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(code_to_run)

            if mode == "compile_c":
                bin_path = os.path.join(tmp_dir, "main.exe" if sys.platform == "win32" else "main")
                compile_cmd = [runner, file_path, "-o", bin_path]
                compile_res = await asyncio.to_thread(_run_subprocess_sync, compile_cmd, "", tmp_dir, timeout)
                if compile_res["exit_code"] != 0:
                    return {
                        "stdout": compile_res["stdout"],
                        "stderr": f"Compilation Error:\n{compile_res['stderr']}",
                        "exit_code": compile_res["exit_code"],
                        "status": "error",
                        "execution_time_ms": compile_res["execution_time_ms"],
                        "language_used": lang_name
                    }
                cmd = [bin_path]
            elif mode == "compile_rust":
                bin_path = os.path.join(tmp_dir, "main.exe" if sys.platform == "win32" else "main")
                compile_cmd = [runner, file_path, "-o", bin_path]
                compile_res = await asyncio.to_thread(_run_subprocess_sync, compile_cmd, "", tmp_dir, timeout)
                if compile_res["exit_code"] != 0:
                    return {
                        "stdout": compile_res["stdout"],
                        "stderr": f"Rust Compilation Error:\n{compile_res['stderr']}",
                        "exit_code": compile_res["exit_code"],
                        "status": "error",
                        "execution_time_ms": compile_res["execution_time_ms"],
                        "language_used": lang_name
                    }
                cmd = [bin_path]
            elif mode == "compile_java":
                compile_cmd = [runner, file_path]
                compile_res = await asyncio.to_thread(_run_subprocess_sync, compile_cmd, "", tmp_dir, timeout)
                if compile_res["exit_code"] != 0:
                    return {
                        "stdout": compile_res["stdout"],
                        "stderr": f"Java Compilation Error:\n{compile_res['stderr']}",
                        "exit_code": compile_res["exit_code"],
                        "status": "error",
                        "execution_time_ms": compile_res["execution_time_ms"],
                        "language_used": lang_name
                    }
                java_bin = shutil.which("java") or "java"
                cmd = [java_bin, "-cp", tmp_dir, "Main"]
            elif mode == "go_run":
                cmd = [runner, "run", file_path]
            elif ext == ".py":
                cmd = [runner, "-u", file_path]
            else:
                cmd = [runner, file_path]

            exec_res = await asyncio.to_thread(_run_subprocess_sync, cmd, stdin_data, tmp_dir, timeout)
            exec_res["language_used"] = lang_name

            if exec_res["exit_code"] == 0 and not exec_res["stdout"].strip() and not exec_res["stderr"].strip():
                exec_res["stdout"] = "✓ Code executed cleanly (Exit Code 0).\n(Note: Code produced no output. Add print() statements or return values to inspect output in the terminal.)"

            return exec_res

    @classmethod
    async def run_test_cases(
        cls,
        code: str,
        language: str,
        test_cases: List[Any]
    ) -> Dict[str, Any]:
        """
        Executes code snippet against multiple test cases and evaluates actual vs expected output.
        """
        results = []
        passed_count = 0
        total_count = len(test_cases)

        for tc in test_cases:
            tc_id = getattr(tc, "id", 0)
            tc_name = getattr(tc, "name", "") or f"Test Case #{tc_id}"
            tc_input = getattr(tc, "input_data", "") or ""
            tc_expected = (getattr(tc, "expected_output", "") or "").strip()

            exec_res = await cls.execute_code(
                code=code,
                language=language,
                stdin_data=tc_input,
                timeout_seconds=5
            )

            actual_out = (exec_res.get("stdout") or "").strip()
            # Compare output ignoring trailing whitespace
            is_passed = (actual_out == tc_expected) or (actual_out.rstrip() == tc_expected.rstrip())

            if is_passed:
                passed_count += 1
                status = "PASSED"
            elif exec_res.get("status") == "timeout":
                status = "TIMEOUT"
            elif exec_res.get("exit_code") != 0:
                status = "ERROR"
            else:
                status = "FAILED"

            results.append({
                "id": tc_id,
                "name": tc_name,
                "input_data": tc_input,
                "expected_output": tc_expected,
                "actual_output": actual_out or (exec_res.get("stderr") or "(No output)"),
                "passed": is_passed,
                "execution_time_ms": exec_res.get("execution_time_ms", 0.0),
                "status": status
            })

        success_rate = round((passed_count / total_count * 100.0), 1) if total_count > 0 else 0.0

        return {
            "results": results,
            "total_tests": total_count,
            "passed_tests": passed_count,
            "success_rate": success_rate
        }
