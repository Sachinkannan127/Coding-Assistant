import json
import logging
from typing import Dict, Any, List
from backend.app.config import settings

logger = logging.getLogger(__name__)


class ExplainService:
    """
    Code Explanation Engine.
    Translates source code snippets into detailed plain English explanations tailored for:
    - 'simple': Kids & Complete Beginners (fun real-world analogies, zero technical jargon)
    - 'beginner': Students & Learners (step-by-step logic breakdown, variable tracking)
    - 'developer': Developers (technical architecture, patterns, efficiency)
    """

    @classmethod
    async def explain_code(
        cls,
        code: str,
        language: str = "auto",
        audience: str = "simple"
    ) -> Dict[str, Any]:
        """
        Generates structured plain English explanation for the given code snippet.
        """
        audience_mode = (audience or "simple").lower().strip()
        if audience_mode not in ["simple", "beginner", "developer"]:
            audience_mode = "simple"

        # Attempt to generate via LLM (Gemini) if API key is present
        if settings.GEMINI_API_KEY and settings.GEMINI_API_KEY.strip():
            try:
                from google import genai
                from google.genai import types

                client = genai.Client(api_key=settings.GEMINI_API_KEY)
                
                system_instruction = (
                    "You are a friendly, master programming educator. Your mission is to provide an IN-DEPTH, "
                    "LINE-BY-LINE explanation of source code in simple, clear, engaging English.\n"
                    "CRITICAL REQUIREMENT: You MUST analyze and explain EVERY SINGLE LINE of code individually in the line_by_line array. "
                    "Do NOT group lines together or skip any lines. Each line must have a thorough 2-3 sentence plain English explanation.\n"
                )

                if audience_mode == "simple":
                    system_instruction += (
                        "Target Audience: KIDS, TEENS & COMPLETE BEGINNERS.\n"
                        "Rules:\n"
                        "1. Use simple English words (zero confusing jargon).\n"
                        "2. Provide a creative real-world analogy (e.g. comparing variables to labeled toy boxes, "
                        "loops to repeating a fun game action, functions to a magical recipe).\n"
                        "3. For every single line, explain in simple terms what it does and why it is needed.\n"
                    )
                elif audience_mode == "beginner":
                    system_instruction += (
                        "Target Audience: COMPUTER SCIENCE STUDENTS & LEARNERS.\n"
                        "Rules:\n"
                        "1. Explain step-by-step how variables change, memory values mutate, and control flow progresses.\n"
                        "2. Connect code syntax to fundamental computer science principles.\n"
                        "3. For every line, describe what is stored, computed, or evaluated.\n"
                    )
                else: # developer
                    system_instruction += (
                        "Target Audience: EXPERIENCED DEVELOPERS.\n"
                        "Rules:\n"
                        "1. Focus on algorithmic intent, complexity (Big-O), design patterns, type safety, and memory characteristics.\n"
                        "2. Highlight potential edge cases or optimization opportunities per line/block.\n"
                    )

                prompt = f"""
Analyze the following {language} code snippet line-by-line:

```
{code}
```

Return ONLY valid JSON strictly matching this structure (no markdown code blocks, no trailing text):
{{
  "summary": "Comprehensive 2-3 sentence summary of what this program accomplishes",
  "real_world_analogy": "A clear, fun real-world metaphor explaining the logic",
  "line_by_line": [
    {{
      "line_range": "Line 1",
      "snippet": "exact line code",
      "explanation": "Detailed 2-3 sentence explanation of what this line does, why it exists, and what values are created or changed."
    }}
  ],
  "key_concepts": ["Concept 1", "Concept 2"]
}}
"""

                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=0.2,
                        response_mime_type="application/json"
                    )
                )

                if response.text:
                    parsed = json.loads(response.text)
                    parsed["audience"] = audience_mode
                    return parsed

            except Exception as err:
                logger.warning(f"LLM code explanation failed, falling back to rich rule-based explainer: {err}")

        # Fallback Rule-Based Explainer
        return cls._rule_based_explanation(code, language, audience_mode)

    @classmethod
    def _rule_based_explanation(cls, code: str, language: str, audience: str) -> Dict[str, Any]:
        """
        In-depth rule-based fallback explainer for line-by-line code analysis.
        """
        lines = code.split("\n")
        line_by_line = []
        concepts = set()

        for idx, line in enumerate(lines, 1):
            line_str = line.strip()
            if not line_str:
                continue

            if line_str.startswith("#") or line_str.startswith("//") or line_str.startswith("/*") or line_str.startswith("*"):
                concepts.add("Documentation & Comments")
                explanation = f"Line {idx} is a developer comment. It provides notes to help human readers understand the code without affecting execution."
            elif line_str.startswith("import ") or line_str.startswith("from ") or line_str.startswith("#include") or line_str.startswith("require("):
                concepts.add("Modules & Libraries")
                mod = line_str.split("import")[-1].split("from")[0].strip() or line_str
                explanation = f"Line {idx} imports external tools/libraries ({mod}). This brings pre-written helper functions into our program."
            elif line_str.startswith("def ") or line_str.startswith("function ") or line_str.startswith("async def "):
                concepts.add("Functions (Reusable Actions)")
                fn_name = line_str.split("(")[0].replace("def", "").replace("function", "").replace("async", "").strip()
                explanation = f"Line {idx} defines a reusable action/recipe named '{fn_name}'. This group of steps can be called whenever needed."
            elif line_str.startswith("if ") or line_str.startswith("elif ") or line_str.startswith("else if "):
                concepts.add("Conditionals (Decision Making)")
                explanation = f"Line {idx} is a decision check. It tests whether a condition is true before running the code inside it."
            elif line_str.startswith("else:") or line_str == "else":
                concepts.add("Conditionals (Decision Making)")
                explanation = f"Line {idx} handles the default fallback path. If none of the previous checks were true, this code runs instead."
            elif line_str.startswith("for ") or line_str.startswith("while "):
                concepts.add("Loops (Repeated Execution)")
                explanation = f"Line {idx} starts a loop. It tells the computer to repeat a set of actions automatically until finished."
            elif line_str.startswith("return "):
                concepts.add("Return Values")
                expr = line_str.replace("return", "").strip()
                explanation = f"Line {idx} finishes the function and outputs the calculated result ('{expr}') back to the caller."
            elif "=" in line_str and not any(op in line_str for op in ["==", "!=", "<=", ">="]):
                concepts.add("Variables (Data Storage)")
                parts = line_str.split("=", 1)
                var_name = parts[0].strip()
                val_expr = parts[1].strip()
                explanation = f"Line {idx} creates or updates a variable container named '{var_name}' and assigns it the calculated value of '{val_expr}'."
            elif any(line_str.startswith(kw) for kw in ["print(", "console.log(", "printf(", "System.out"]):
                concepts.add("Console Output")
                explanation = f"Line {idx} outputs information to the terminal screen so users or developers can view the current values."
            else:
                explanation = f"Line {idx} executes a statement ('{line_str}'). It evaluates expressions, calls functions, or modifies state."

            line_by_line.append({
                "line_range": f"Line {idx}",
                "snippet": line_str,
                "explanation": explanation
            })

        if not concepts:
            concepts.add("Basic Program Logic")

        analogy = (
            "Think of this code like a step-by-step recipe! Each line is an individual instruction: "
            "variables are labeled containers storing ingredients, loops repeat steps like stirring, "
            "and functions are master recipes you can reuse anytime."
        )

        summary = f"This program consists of {len(line_by_line)} distinct instructions operating in sequence to process data and control program execution."

        return {
            "summary": summary,
            "real_world_analogy": analogy,
            "line_by_line": line_by_line,
            "key_concepts": list(concepts),
            "audience": audience
        }
