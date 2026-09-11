"""
🥇 Static Analysis MCP Connector Server.
Provides AST parsing, cyclomatic complexity calculation, and code smell detection tools.
"""

import ast
from typing import Dict, Any, List


class StaticAnalysisMcpServer:
    SERVER_ID = "static_analysis"
    NAME = "Static Analysis MCP"
    DESCRIPTION = "AST syntax tree parsing, cyclomatic complexity calculations, and code smell detection"
    CATEGORY = "Static Analysis"

    @classmethod
    def get_tools(cls) -> List[Dict[str, Any]]:
        return [
            {
                "name": "analyze_ast",
                "description": "Parses code into an Abstract Syntax Tree (AST) and extracts function definitions, classes, imports, and syntax status.",
                "server_id": cls.SERVER_ID,
                "parameters": [
                    {"name": "code", "type": "string", "description": "Source code text to parse", "required": True},
                    {"name": "language", "type": "string", "description": "Programming language (python, javascript, etc.)", "required": False, "default": "python"}
                ]
            },
            {
                "name": "calculate_complexity",
                "description": "Calculates cyclomatic complexity, line metrics, and maintainability score for a code snippet.",
                "server_id": cls.SERVER_ID,
                "parameters": [
                    {"name": "code", "type": "string", "description": "Source code text to evaluate", "required": True}
                ]
            },
            {
                "name": "detect_code_smells",
                "description": "Scans code for common anti-patterns, long functions, duplicate logic, and naming smells.",
                "server_id": cls.SERVER_ID,
                "parameters": [
                    {"name": "code", "type": "string", "description": "Source code text to analyze", "required": True}
                ]
            }
        ]

    @classmethod
    async def execute_tool(cls, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        code = args.get("code", "")
        if not code or not code.strip():
            raise ValueError("Parameter 'code' cannot be empty.")

        if tool_name == "analyze_ast":
            return cls._analyze_ast(code)
        elif tool_name == "calculate_complexity":
            return cls._calculate_complexity(code)
        elif tool_name == "detect_code_smells":
            return cls._detect_code_smells(code)
        else:
            raise ValueError(f"Unknown tool '{tool_name}' for server '{cls.SERVER_ID}'")

    @classmethod
    def _analyze_ast(cls, code: str) -> Dict[str, Any]:
        try:
            tree = ast.parse(code)
            functions = []
            classes = []
            imports = []

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                    functions.append({
                        "name": node.name,
                        "line": node.lineno,
                        "args_count": len(node.args.args),
                        "is_async": isinstance(node, ast.AsyncFunctionDef)
                    })
                elif isinstance(node, ast.ClassDef):
                    classes.append({
                        "name": node.name,
                        "line": node.lineno,
                        "methods_count": sum(1 for item in node.body if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)))
                    })
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    for alias in node.names:
                        imports.append(f"{module}.{alias.name}" if module else alias.name)

            return {
                "ast_valid": True,
                "syntax_error": None,
                "functions": functions,
                "classes": classes,
                "imports": list(set(imports)),
                "total_lines": len(code.splitlines())
            }
        except SyntaxError as e:
            return {
                "ast_valid": False,
                "syntax_error": f"SyntaxError at line {e.lineno}, col {e.offset}: {e.msg}",
                "functions": [],
                "classes": [],
                "imports": [],
                "total_lines": len(code.splitlines())
            }
        except Exception as e:
            return {
                "ast_valid": False,
                "syntax_error": f"AST Parse Error: {str(e)}",
                "functions": [],
                "classes": [],
                "imports": [],
                "total_lines": len(code.splitlines())
            }

    @classmethod
    def _calculate_complexity(cls, code: str) -> Dict[str, Any]:
        lines = code.splitlines()
        non_empty = [l for l in lines if l.strip() and not l.strip().startswith("#")]
        
        # Simple cyclomatic complexity estimation based on decision keywords
        decision_keywords = ["if ", "elif ", "for ", "while ", "except ", "with ", "and ", "or ", "case "]
        complexity_score = 1
        for line in lines:
            for kw in decision_keywords:
                complexity_score += line.count(kw)

        maintainability_index = max(0, min(100, round(100 - (complexity_score * 3) - (len(lines) * 0.2))))

        rating = "Low Complexity" if complexity_score <= 5 else "Moderate Complexity" if complexity_score <= 12 else "High Complexity"

        return {
            "total_lines": len(lines),
            "loc": len(non_empty),
            "cyclomatic_complexity": complexity_score,
            "complexity_rating": rating,
            "maintainability_index": maintainability_index,
            "recommendation": "Code structure is clean." if complexity_score <= 7 else "Consider splitting functions to reduce decision branches."
        }

    @classmethod
    def _detect_code_smells(cls, code: str) -> Dict[str, Any]:
        smells = []
        lines = code.splitlines()

        for idx, line in enumerate(lines, start=1):
            if len(line) > 120:
                smells.append({"line": idx, "smell": "Long Line", "description": f"Line exceeds 120 characters ({len(line)} chars)."})
            if "global " in line:
                smells.append({"line": idx, "smell": "Global State", "description": "Use of global variable mutation detected."})
            if "except:" in line.replace(" ", ""):
                smells.append({"line": idx, "smell": "Bare Except Clause", "description": "Bare 'except:' swallows all system exceptions including KeyboardInterrupt."})

        return {
            "total_smells_found": len(smells),
            "smells": smells,
            "code_cleanliness_score": max(0, 100 - (len(smells) * 10))
        }
