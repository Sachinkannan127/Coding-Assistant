# System Requirements Specification

**Project**: AI Code Review & Refactoring Platform  
**Phase**: Phase 0 — Requirements & Architecture Validation  
**Status**: Frozen & Approved  

---

## 1. Executive Summary & Objective

The **AI Code Review & Refactoring Platform** is a full-stack, multi-agent AI system designed to analyze code pasted by users, detect bugs, identify security vulnerabilities, evaluate complexity and readability, generate validated refactored code, and provide side-by-side comparisons with export capabilities.

The system supports two execution tiers:
1. **Quick Scan**: Rapid, low-latency analysis focusing on core syntax, primary bugs, and high-level summary.
2. **Deep Review**: Comprehensive analysis using a stateful multi-agent LangGraph workflow, RAG-enhanced knowledge retrieval, formal refactoring generation with structural validation, and detailed metrics.

---

## 2. Review Modes Specification

| Attribute | Quick Scan Mode | Deep Review Mode |
| :--- | :--- | :--- |
| **Primary Goal** | Fast, immediate feedback on pasted code | Thorough audit, security check, refactoring & RAG |
| **Target Latency** | $< 5-10$ seconds | $< 25-45$ seconds |
| **Participating Agents** | Code Analysis, Bug Detection, Synthesizer | Code Analysis, Bug Detection, Security, Quality & Readability, Complexity, Refactoring, Validation, Synthesizer |
| **RAG Knowledge Retrieval** | Disabled | Enabled (queries security standards, clean code patterns) |
| **Refactoring Loop** | Basic refactoring hint (no iteration) | Full refactoring generator + multi-pass validation & retry loop |
| **Metrics Generated** | Basic bug list & summary | Full findings, line references, complexity score (1-10), readability score (1-10), AST validation |
| **Primary Model** | Gemini 2.5 Flash | Gemini 2.5 Flash (agents) + Gemini 2.5 Pro (refactoring & synthesis) |

---

## 3. Unified Output Schema

All reviews—regardless of mode—return data conforming strictly to the following JSON structure (mapped to Pydantic models in backend):

```json
{
  "review_id": "string (UUID or ObjectId)",
  "created_at": "ISO-8601 Timestamp",
  "mode": "quick | deep",
  "input_metadata": {
    "language": "python | typescript | javascript | java | cpp | go | rust | auto",
    "line_count": 42,
    "char_count": 1250,
    "hash": "sha256_hash_of_original_code"
  },
  "summary": {
    "overview": "Plain-English explanation of what the code does.",
    "verdict": "clean | minor_issues | major_issues | critical_vulnerabilities",
    "key_takeaways": ["Point 1", "Point 2"]
  },
  "metrics": {
    "complexity_score": 7.5,
    "readability_score": 8.0,
    "maintainability_index": "B",
    "cyclomatic_complexity_est": "Moderate"
  },
  "findings": [
    {
      "id": "find-001",
      "category": "bug | security | quality | complexity",
      "severity": "critical | high | medium | low | info",
      "title": "Potential Null Pointer Dereference",
      "description": "Variable `user` is accessed before null check on line 14.",
      "line_start": 14,
      "line_end": 16,
      "code_snippet": "user.getProfile().name",
      "suggestion": "Check if `user` and `user.getProfile()` are non-null before dereferencing.",
      "cwe_or_rule_id": "CWE-476"
    }
  ],
  "refactoring": {
    "has_refactored_code": true,
    "refactored_code": "def updated_function(): ...",
    "diff_summary": "Extracted helper function, added null checks, simplified loop.",
    "validation_status": "passed | retried_passed | fallback_original",
    "validation_notes": "Syntax check passed. Function signatures preserved."
  },
  "execution_metadata": {
    "total_duration_ms": 3420,
    "llm_provider_used": "gemini",
    "fallback_triggered": false,
    "rag_context_used": true,
    "rag_sources": ["OWASP Top 10 API Security", "Clean Code Refactoring Patterns"]
  }
}
```

---

## 4. Input Validation & Edge Cases

1. **Empty / White-space Input**: Rejected at API boundary with HTTP 400 (`Code input cannot be empty`).
2. **Non-Code / Natural Language Input**: Validator checks for code structural markers (indentation, operators, keywords). Rejects non-code input with friendly HTTP 420/400.
3. **Payload Size Limit**: Hard ceiling of **50 KB** (approx. 1,500 lines of code) per request to prevent token overflow and excessive latency.
4. **Unknown / Ambiguous Language**: Language detector falls back to heuristic token matching or generic syntax parser.
5. **Exact Line Number Preservation**: Normalizer strips carriage returns while maintaining exact 1-indexed line counts so findings directly align with the user's input editor.

---

## 5. Non-Functional Requirements

1. **Resilience & Fallback**:
   - Primary LLM: **Google Gemini** (`gemini-2.5-flash` / `gemini-2.5-pro`).
   - Secondary LLM: **Mistral AI** (`codestral-latest` / `mistral-large-latest`).
   - Automatic failover if Gemini returns HTTP 429/500 or times out ($>15$s per agent call).
2. **Graceful RAG Failure**: If MongoDB Atlas Vector Search is unreachable or yields zero results, the agents proceed with LLM-native knowledge without failing the request.
3. **Observability**: Every state transition and LLM call is traced via **LangSmith**.
4. **Persistence**: Every completed review and individual agent outputs are stored in **MongoDB Atlas**.
