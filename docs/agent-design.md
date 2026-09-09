# Multi-Agent System & LangGraph Design Specification

**Project**: AI Code Review & Refactoring Platform  
**Phase**: Phase 0 — Requirements & Architecture Validation  
**Status**: Frozen & Approved  

---

## 1. Multi-Agent System Overview

The platform uses a team of specialized AI agents built with **LangChain** and orchestrated via a stateful **LangGraph** state graph. Each agent has a single, well-defined responsibility, preventing context dilution and improving structured output reliability.

```
                    ┌─────────────────────────┐
                    │      ReviewState        │
                    └────────────┬────────────┘
                                 │
                         [ Depth Router ]
                          /            \
                (Quick)  /              \  (Deep)
                        v                v
       ┌────────────────────────┐    ┌──────────────────────────────────┐
       │ - CodeAnalysisAgent    │    │ - CodeAnalysisAgent              │
       │ - BugDetectionAgent    │    │ - BugDetectionAgent              │
       └───────────┬────────────┘    │ - SecurityAgent (RAG)            │
                   │                 │ - QualityReadabilityAgent (RAG)  │
                   │                 │ - ComplexityAgent                │
                   │                 └────────────────┬─────────────────┘
                   │                                  │
                   │                                  v
                   │                 ┌──────────────────────────────────┐
                   │                 │ - RefactoringAgent               │
                   │                 └────────────────┬─────────────────┘
                   │                                  │
                   │                                  v
                   │                 ┌──────────────────────────────────┐
                   │                 │ - ValidationAgent (AST / Intent) │
                   │                 └────────────────┬─────────────────┘
                   │                         │                │
                   │                  (Pass) │                │ (Fail < 2 retries)
                   │                         v                v
                   │                ┌────────────────┐   [ Retry Node ]
                   │                │ Synthesizer    │ ───────┘
                   │                └───────┬────────┘
                   v                        v
            ┌────────────────────────────────────────┐
            │       Unified Review Persistence       │
            └────────────────────────────────────────┘
```

---

## 2. Agent Roster & Detailed Responsibilities

| Agent Name | Scope & Responsibility | Output Contribution | RAG Enabled? |
| :--- | :--- | :--- | :--- |
| **`CodeAnalysisAgent`** | Parses code structural semantics, identifies primary function goals, extracts classes/methods, builds context baseline. | `summary.overview`, language validation | No |
| **`BugDetectionAgent`** | Scans for logic bugs, null pointer dereferences, resource leaks, race conditions, boundary failures, off-by-one errors. | `findings` (category: `bug`) | Yes |
| **`SecurityAgent`** | Audits code against OWASP Top 10, CWE rules, injection risks, hardcoded secrets, unsafe deserialization, insecure crypto. | `findings` (category: `security`) | Yes |
| **`QualityReadabilityAgent`** | Evaluates naming conventions, dead code, modularity, DRY principles, code layout, formatting, comment accuracy. | `findings` (category: `quality`), `readability_score` | Yes |
| **`ComplexityAgent`** | Calculates estimated cyclomatic complexity, nesting levels, cognitive load, time/space Big-O complexity. | `findings` (category: `complexity`), `complexity_score` | No |
| **`RefactoringAgent`** | Consolidates all agent findings and RAG context to generate idiomatic, clean, refactored code and diff explanation. | `refactored_code`, `diff_summary` | Yes |
| **`ValidationAgent`** | Verifies generated refactored code via AST parsing (syntax check) and LLM intent check. Enforces signature preservation. | `validation_status`, retry signal | No |
| **`SynthesizerAgent`** | Deduplicates overlapping findings across agents, computes unified risk score, formats final response schema. | Unified JSON Output Schema | No |

---

## 3. LangGraph State Schema (`ReviewState`)

The state object passed between nodes in the graph is defined as a Python `TypedDict` with annotated reducers:

```python
from typing import TypedDict, List, Dict, Any, Optional
from typing_extensions import Annotated
import operator

class Finding(TypedDict):
    id: str
    category: str  # bug, security, quality, complexity
    severity: str  # critical, high, medium, low, info
    title: str
    description: str
    line_start: int
    line_end: int
    code_snippet: str
    suggestion: str
    cwe_or_rule_id: Optional[str]

class ReviewState(TypedDict):
    # Inputs
    review_id: str
    original_code: str
    language: str
    mode: str  # quick | deep
    
    # RAG Context
    rag_context: List[str]
    
    # Agent Outputs (Accumulated via list concatenation)
    findings: Annotated[List[Finding], operator.add]
    code_overview: str
    complexity_score: float
    readability_score: float
    
    # Refactoring & Validation State
    refactored_code: Optional[str]
    diff_summary: Optional[str]
    validation_status: str  # pending | passed | retried_passed | fallback_original
    retry_count: int
    validation_errors: List[str]
    
    # Final Output & Telemetry
    final_output: Dict[str, Any]
    error: Optional[str]
```

---

## 4. Graph Execution & Routing Rules

1. **Start Node (`entrypoint`)**: Validates code, normalizes line breaks, initializes `ReviewState`.
2. **Depth Router (`depth_router`)**:
   - If `mode == 'quick'`: Routes in parallel to `[CodeAnalysisNode, BugDetectionNode]`.
   - If `mode == 'deep'`: Routes in parallel to `[CodeAnalysisNode, BugDetectionNode, SecurityNode, QualityNode, ComplexityNode]`.
3. **RAG Retrieval Node (`rag_retriever`)**: Triggered in Deep Mode before analysis agents execute. Computes embeddings using **Google Gemini `text-embedding-004`** and fetches relevant security/quality docs from MongoDB Atlas.
4. **Refactoring Branch (`refactoring_node`)**:
   - Executes after all analysis nodes complete.
   - Combines findings + original code + RAG guidelines to write refactored code.
5. **Validation & Retry Loop (`validation_node`)**:
   - Runs Python/JavaScript/generic AST parser on `refactored_code`.
   - If syntax check passes: proceeds to `synthesizer_node`.
   - If syntax check fails AND `retry_count < 2`: increments `retry_count`, appends syntax error to `validation_errors`, loops back to `refactoring_node`.
   - If syntax check fails AND `retry_count >= 2`: sets `validation_status = 'fallback_original'`, resets `refactored_code = original_code`, proceeds to `synthesizer_node`.
6. **Synthesizer Node (`synthesizer_node`)**: Merges findings, strips duplicate line references, formats JSON response, saves to MongoDB Atlas, and completes the workflow.
