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
    "java", "c", "cpp", "csharp", "go", "rust",
    "php", "ruby", "kotlin", "swift", "shell",
    "sql", "nosql", "html", "css", "json", "yaml"
]

LANGUAGE_ALIASES = {
    "js": "javascript",
    "ts": "typescript",
    "py": "python",
    "golang": "go",
    "rs": "rust",
    "c++": "cpp",
    "c#": "csharp",
    "cs": "csharp",
    "sh": "shell",
    "bash": "shell",
    "zsh": "shell",
    "mongodb": "nosql",
    "mongo": "nosql",
    "redis": "nosql",
    "cassandra": "nosql",
    "cql": "nosql",
    "neo4j": "nosql",
    "cypher": "nosql",
    "postgres": "sql",
    "postgresql": "sql",
    "mysql": "sql",
    "sqlite": "sql",
    "mssql": "sql",
    "tsql": "sql",
    "plsql": "sql",
    "oracle": "sql",
    "mariadb": "sql",
    "snowflake": "sql"
}


def detect_language(code: str, requested_language: str = "auto") -> str:
    """
    Detects programming language, query dialect, or framework from code snippet using heuristic patterns.
    Supports SQL, NoSQL (MongoDB, Redis, CQL), Python, Django, JavaScript, TypeScript, React, Next.js,
    Node.js, Java, C, C++, C#, Go, Rust, PHP, Ruby, Kotlin, Swift, Shell, HTML, and CSS.
    """
    cleaned_lang = requested_language.strip().lower() if requested_language else "auto"
    cleaned_lang = LANGUAGE_ALIASES.get(cleaned_lang, cleaned_lang)
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

    # 2. Database & Query Languages (SQL & NoSQL)
    # SQL (DDL, DML, DQL statements, clauses, comments)
    sql_patterns = [
        r"\b(?:SELECT\s+[\s\S]+?\s+FROM|INSERT\s+INTO\s+[\w.`\"]+|UPDATE\s+[\w.`\"]+\s+SET|DELETE\s+FROM\s+[\w.`\"]+)\b",
        r"\b(?:CREATE\s+(?:OR\s+REPLACE\s+)?(?:TABLE|VIEW|INDEX|PROCEDURE|FUNCTION|DATABASE|SCHEMA|TRIGGER)|ALTER\s+TABLE|DROP\s+(?:TABLE|VIEW|INDEX|DATABASE)|TRUNCATE\s+TABLE)\b",
        r"\b(?:FROM\s+[\w.`\"]+\s+(?:WHERE|JOIN|GROUP\s+BY|ORDER\s+BY|LIMIT))\b",
        r"^\s*--\s+.*",  # SQL comment
        r"\b(?:PRIMARY\s+KEY|FOREIGN\s+KEY\s*\([^)]+\)\s*REFERENCES)\b"
    ]
    if any(re.search(pat, code_text, re.IGNORECASE | re.MULTILINE) for pat in sql_patterns):
        # Distinguish pure SQL from code containing SQL strings: check if not typical Python/JS/Go code
        is_embedded = re.search(r"\b(def\s+\w+|const\s+\w+\s*=|let\s+\w+\s*=|var\s+\w+\s*=|func\s+\w+|package\s+\w+)\b", code_text)
        if not is_embedded:
            return "sql"

    # NoSQL (MongoDB, Redis, Cassandra CQL, Cypher)
    nosql_patterns = [
        r"db\.[a-zA-Z0-9_]+\.(?:find|aggregate|insertOne|insertMany|updateOne|updateMany|deleteOne|deleteMany|countDocuments|distinct|bulkWrite|replaceOne|drop)\s*\(",
        r"(\$match|\$group|\$project|\$lookup|\$unwind|\$sort|\$limit|\$skip|\$set|\$unset|\$addFields|\$facet|\$bucket|\$in|\$nin|\$gte|\$lte|\$gt|\$lt|\$ne|\$regex|\$exists|\$expr|\$sum|\$push|\$pull|\$addToSet)\b",
        r"(?:new\s+mongoose\.Schema|mongoose\.model\(|ObjectId\([a-fA-F0-9'\"]+\))",
        r"^\s*(?:GET|SET|DEL|HGET|HSET|HDEL|HGETALL|LPUSH|RPUSH|LPOP|RPOP|SADD|SMEMBERS|ZADD|ZRANGE|SETEX|INCR|DECR|EXPIRE|TTL)\s+[a-zA-Z0-9_:]+",
        r"\b(?:KEYSPACE|CLUSTERING\s+ORDER\s+BY|ALLOW\s+FILTERING)\b",
        r"\bMATCH\s*\([a-zA-Z0-9_:]*\)\s*(?:WHERE\s+.*?|RETURN)\b"
    ]
    if any(re.search(pat, code_text, re.IGNORECASE | re.MULTILINE) for pat in nosql_patterns):
        return "nosql"

    # 3. Markup & Styles (HTML & CSS)
    if re.search(r"(<!DOCTYPE\s+html|<html\b|<head\b|<body\b|(?:\s*<(?:div|span|section|header|footer|table|form|input|button|h[1-6]|p|ul|ol|li)\b[^>]*>))", code_text, re.IGNORECASE):
        if not re.search(r"(className=|export\s+default|import\s+)", code_text):
            return "html"
    if re.search(r"(@media\s+|(?:\b|\.)[a-zA-Z0-9_-]+\s*\{\s*(?:color|background|margin|padding|display|flex|grid|font-|border-|width|height):)", code_text):
        return "css"

    # 4. Shell / Bash (High priority on shebang or shell idioms)
    if re.search(r"(^#!\/(?:usr\/)?bin\/(?:bash|sh|zsh)|^\s*export\s+[a-zA-Z_][a-zA-Z0-9_]*=|if\s+\[\[?\s+.*?\s+\]\]?;\s*then|chmod\s+[+0-9])", code_text, re.MULTILINE):
        return "shell"

    # 5. PHP (Distinct PHP opening tags, superglobals, or object arrows)
    if re.search(r"(<\?php|<\?=|\$this->|\$(?:_GET|_POST|_SESSION|_SERVER|_REQUEST)\b|\$[a-zA-Z_\x80-\xff]\w*\s*->)", code_text):
        return "php"

    # 6. C++ vs C
    if re.search(r"(#include\s*<(?:iostream|vector|string|map|set|algorithm|memory|utility|sstream|fstream)>|std::|cout\s*<<|cin\s*>>|using\s+namespace\s+\w+;|template\s*<|public:|private:|protected:|new\s+\w+\()", code_text):
        return "cpp"
    if re.search(r"(#include\s*<[a-zA-Z0-9_/]+\.h>|printf\(|scanf\(|malloc\(|free\(|struct\s+\w+\s*\{|typedef\s+struct|int\s+main\s*\()", code_text):
        return "c"

    # 7. Java vs C#
    if re.search(r"(public\s+class\s+.*public\s+static\s+void\s+main|System\.out\.|import\s+java\.|import\s+javax\.|@Override|@SpringBootApplication)", code_text, re.DOTALL):
        return "java"
    if re.search(r"(using\s+System(?:\.\w+)*;|namespace\s+[A-Za-z0-9_.]+\s*\{|Console\.(?:WriteLine|Write)|Task<\w+>|\[(?:HttpGet|HttpPost|Route|Authorize|Key|Required)\])", code_text):
        return "csharp"

    # 8. Ruby
    if re.search(r"(def\s+[a-zA-Z_]\w*(\s*\(.*?\))?\s*(?:#.*)?\n[\s\S]*?\bend\b|attr_accessor|require\s+['\"][^'\"]+['\"]|puts\s+['\"]|class\s+[A-Z]\w*\s*<|\b(?:elsif|unless)\b)", code_text):
        return "ruby"

    # 9. Rust & Go
    if re.search(r"(fn\s+\w+|let\s+mut\s+|impl\s+|pub\s+fn|println!|eprintln!|use\s+std::|match\s+\w+|Ok\(|Err\(|#\[derive\()", code_text):
        return "rust"
    if re.search(r"(package\s+\w+|func\s+\w+|func\s+\(|fmt\.|import\s+[\"\(]|go\s+func|chan\s+|:=)", code_text):
        return "go"

    # 10. Kotlin & Swift
    if re.search(r"(fun\s+[a-zA-Z_]\w*\s*\(|val\s+\w+\s*:\s*\w+|var\s+\w+\s*:\s*\w+|companion\s+object|import\s+kotlin\b)", code_text):
        return "kotlin"
    if re.search(r"(import\s+(?:UIKit|SwiftUI|Foundation)|func\s+[a-zA-Z_]\w*\s*\(.*?->|@State\s+private|guard\s+let\b)", code_text):
        return "swift"

    # 11. Java fallback
    if re.search(r"(public\s+class\s+|public\s+static\s+void\s+main|System\.out\.|import\s+java\.|import\s+javax\.|@Override|@SpringBootApplication)", code_text):
        return "java"

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

    # Check for strong structural markers across all supported programming & database languages
    code_markers = [
        r"\b(def|function|fn|func|class|struct|interface|type|import|from|include|public|private|const|let|var|if|else|for|while|return|package)\b",
        r"\b(SELECT|INSERT|UPDATE|DELETE|CREATE|ALTER|DROP|TABLE|FROM|WHERE|JOIN|GROUP\s+BY|ORDER\s+BY|HAVING|LIMIT|OFFSET|VALUES|SET|INDEX|DATABASE|TRIGGER|PROCEDURE)\b",
        r"\b(db\.\w+|aggregate|find|insertOne|updateOne|deleteOne|\$match|\$group|\$project|\$lookup|\$set|\$in|\$gte|\$lte)\b",
        r"\b(GET|SET|HSET|HGET|LPUSH|RPUSH|ZADD|SADD|EXPIRE|KEYSPACE|ALLOW\s+FILTERING)\b",
        r"\b(using|namespace|echo|puts|val|companion|guard|export|chmod)\b",
        r"[{}();=+\-*/%<>&|^!~\[\]]",
        r"(=>|->|==|!=|<=|>=|\+=|-=|\*=|\/=|:=|::)",
        r"(^\s*#|^\s*\/\/|^\s*\/\*|^\s*--)"
    ]

    total_matches = sum(len(re.findall(pattern, stripped, re.MULTILINE | re.IGNORECASE)) for pattern in code_markers)

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
