import hashlib
import re
from typing import Dict, Any, List, Optional
from fastapi import HTTPException, status
from pydantic import BaseModel, Field


MAX_PAYLOAD_BYTES = 51200  # 50 KB limit


class NormalizedCodeResult(BaseModel):
    """Normalized code submission output schema."""
    normalized_code: str = Field(..., description="Normalized code string with CR stripped")
    language: str = Field(..., description="Detected or validated programming language / framework")
    line_count: int = Field(..., description="Total line count")
    char_count: int = Field(..., description="Total character count")
    hash: str = Field(..., description="SHA-256 hash of original code")
    line_mapping: Dict[int, str] = Field(..., description="1-indexed line number mapping")


class CodeValidationError(HTTPException):
    """Custom HTTP exception for code validation errors."""
    def __init__(self, detail: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        super().__init__(status_code=status_code, detail=detail)


SUPPORTED_LANGUAGES = [
    "python", "django",
    "javascript", "typescript", "react", "nextjs", "nodejs",
    "java", "c", "cpp", "go", "rust"
]


def detect_language(code: str, requested_language: str = "auto") -> str:
    """
    Detects programming language or framework from code snippet using heuristic patterns.
    Supports C, C++, Python, Django, JavaScript, TypeScript, React, Next.js, Node.js, Java, Go, Rust.
    """
    cleaned_lang = requested_language.strip().lower() if requested_language else "auto"
    if cleaned_lang != "auto" and cleaned_lang in SUPPORTED_LANGUAGES:
        return cleaned_lang

    lines = code.splitlines()
    code_text = code[:5000]  # Sample first 5KB for speed

    # 1. Framework Specific Signals (High Precision)
    # Next.js
    if re.search(r"('use client'|'use server'|GetServerSideProps|GetStaticProps|next/router|next/navigation|next/image|next/link)", code_text):
        return "nextjs"

    # React (JSX/TSX, React Hooks)
    if re.search(r"(import\s+.*React|useState|useEffect|useContext|useReducer|useCallback|useMemo|<[A-Z][a-zA-Z0-9]*\s*|\/>|className=)", code_text):
        return "react"

    # Node.js
    if re.search(r"(require\(|module\.exports|exports\.|process\.env|process\.on|__dirname|__filename|express\(\))", code_text):
        return "nodejs"

    # Django
    if re.search(r"(from\s+django\.|models\.Model|models\.CharField|django\.shortcuts|urlpatterns\s*=|django\.http)", code_text):
        return "django"

    # 2. Language Signals
    # Rust
    if re.search(r"(fn\s+\w+|let\s+mut\s+|impl\s+|pub\s+fn|println!|eprintln!|use\s+std::|match\s+\w+|Ok\(|Err\(|#\[derive\()", code_text):
        return "rust"

    # Go
    if re.search(r"(package\s+\w+|func\s+\w+|func\s+\(|fmt\.|import\s+\(|go\s+func|chan\s+|:=)", code_text):
        return "go"

    # Java
    if re.search(r"(public\s+class\s+|public\s+static\s+void\s+main|System\.out\.|import\s+java\.|import\s+javax\.|@Override|@SpringBootApplication)", code_text):
        return "java"

    # C++ vs C
    if re.search(r"(#include\s*<(iostream|vector|string|map|set|algorithm|memory|utility|sstream|fstream)>|std::|cout\s*<<|cin\s*>>|namespace\s+\w+|template\s*<|public:|private:|protected:|new\s+\w+\()", code_text):
        return "cpp"
    if re.search(r"(#include\s*<[a-zA-Z0-9_/]+\.h>|printf\(|scanf\(|malloc\(|free\(|struct\s+\w+\s*\{|typedef\s+struct|int\s+main\s*\()", code_text):
        return "c"

    # TypeScript
    if re.search(r"(interface\s+\w+|type\s+\w+\s*=|:\s*(string|number|boolean|any|void|unknown|never|object|Array)|as\s+\w+|enum\s+\w+)", code_text):
        return "typescript"

    # JavaScript
    if re.search(r"(const\s+|let\s+|var\s+|function\s+\w+|function\s*\(|console\.log|=>|async\s+function|export\s+default|document\.|window\.)", code_text):
        return "javascript"

    # Python
    if re.search(r"(def\s+\w+|class\s+\w+|import\s+\w+|from\s+\w+\s+import|elif\s+|self\.|__init__|print\(|if\s+__name__\s*==|raise\s+\w+|except\s+|with\s+open)", code_text):
        return "python"

    return "python" if cleaned_lang == "auto" else cleaned_lang


def validate_is_code(code: str) -> bool:
    """
    Validates whether input snippet contains program code structural indicators
    versus natural language prose. Rejects pure English paragraphs.
    """
    stripped = code.strip()
    if not stripped:
        return False

    # Check for strong structural markers (keywords, operators, punctuation)
    code_markers = [
        r"\b(def|function|fn|func|class|struct|interface|type|import|from|include|public|private|const|let|var|if|else|for|while|return|package)\b",
        r"[{}();=+\-*/%<>&|^!~\[\]]",
        r"(=>|->|==|!=|<=|>=|\+=|-=|\*=|\/=|:=|::)",
        r"(^\s*#|^\s*\/\/|^\s*\/\*)"
    ]

    total_matches = sum(len(re.findall(pattern, stripped, re.MULTILINE)) for pattern in code_markers)

    # Word count vs code marker count check
    words = re.findall(r"\b[a-zA-Z]{2,}\b", stripped)
    if not words:
        return total_matches > 0

    # Prose indicator: long sentences with regular punctuation without code syntax
    sentences = [s.strip() for s in re.split(r"[.!?]", stripped) if len(s.strip().split()) > 6]
    is_prose_structured = len(sentences) > 0 and total_matches < 3

    if is_prose_structured:
        return False

    # If code marker density relative to total words is sufficient
    return total_matches >= 2 or len(stripped.splitlines()) > 1 and any(line.startswith("  ") or line.startswith("\t") for line in stripped.splitlines())


def normalize_code(code: str) -> Dict[str, Any]:
    """
    Normalizes code string:
    - Strips carriage returns (\r\n -> \n)
    - Computes 1-indexed line mapping
    - Calculates SHA-256 hash
    """
    normalized = code.replace("\r\n", "\n").replace("\r", "\n")
    lines = normalized.split("\n")
    
    line_mapping = {idx + 1: line for idx, line in enumerate(lines)}
    sha256_hash = hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    return {
        "normalized_code": normalized,
        "line_count": len(lines),
        "char_count": len(normalized),
        "hash": sha256_hash,
        "line_mapping": line_mapping
    }


def validate_and_normalize_code(code: str, language: str = "auto") -> NormalizedCodeResult:
    """
    Main API boundary validation entrypoint:
    1. Rejects empty/whitespace input
    2. Enforces 50 KB maximum payload size
    3. Rejects natural language prose
    4. Auto-detects programming language / framework
    5. Normalizes lines and line numbers
    """
    if not code or not code.strip():
        raise CodeValidationError("Code input cannot be empty.")

    payload_size = len(code.encode("utf-8"))
    if payload_size > MAX_PAYLOAD_BYTES:
        raise CodeValidationError(
            f"Payload size ({payload_size} bytes) exceeds maximum limit of 50 KB (51,200 bytes)."
        )

    if not validate_is_code(code):
        raise CodeValidationError("Input does not appear to be valid program code.")

    detected_lang = detect_language(code, requested_language=language)
    norm_info = normalize_code(code)

    return NormalizedCodeResult(
        normalized_code=norm_info["normalized_code"],
        language=detected_lang,
        line_count=norm_info["line_count"],
        char_count=norm_info["char_count"],
        hash=norm_info["hash"],
        line_mapping=norm_info["line_mapping"]
    )
