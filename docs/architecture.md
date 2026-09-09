# System Architecture Specification

**Project**: AI Code Review & Refactoring Platform  
**Phase**: Phase 0 — Requirements & Architecture Validation  
**Status**: Frozen & Approved  

---

## 1. High-Level System Architecture

The system utilizes a modern, decoupled full-stack architecture with a Next.js web application, a FastAPI backend server, a stateful multi-agent LangGraph workflow engine, MongoDB Atlas for durable data storage and vector search, and dual LLM providers (Gemini + Mistral fallback).

```mermaid
graph TD
    Client["Client Browser<br/>(Next.js App)"] -->|HTTP / JSON API| API["FastAPI Gateway<br/>(backend/app/main.py)"]
    
    subgraph Backend Server
        API --> Validator["Code Validator &<br/>Language Detector"]
        Validator --> GraphController["LangGraph Workflow Controller<br/>(review_graph.py)"]
        
        subgraph LangGraph Multi-Agent Engine
            GraphController --> Router["Depth Router<br/>(Quick vs Deep)"]
            Router --> Agents["Specialized Agents<br/>(Analysis, Bugs, Security, Quality, Complexity)"]
            Agents --> RAG["RAG Knowledge Retriever<br/>(MongoDB Atlas Vector Search)"]
            Agents --> RefactorNode["Refactoring Generator &<br/>Validation Loop"]
            RefactorNode --> Synthesizer["Synthesizer Agent"]
        end
        
        LangGraph Multi-Agent Engine --> LLMRouter["LLM Router & Fallback Manager"]
    end
    
    LLMRouter -->|Primary| Gemini["Google Gemini API<br/>(gemini-2.5-flash / pro)"]
    LLMRouter -->|Fallback| Mistral["Mistral AI API<br/>(codestral / mistral-large)"]
    
    RAG -->|Gemini Embeddings<br/>text-embedding-004| VectorStore["MongoDB Atlas Vector Search"]
    
    Synthesizer --> Persistence["MongoDB Repository Layer"]
    Persistence --> MongoDB[("MongoDB Atlas Database")]
    
    LangGraph Multi-Agent Engine -.->|Tracing & Metrics| LangSmith["LangSmith Observability"]
```

---

## 2. Component Stack & Technology Choices

| Layer | Technology | Selection Rationale |
| :--- | :--- | :--- |
| **Frontend UI** | Next.js 14+ (App Router), TypeScript, Vanilla CSS | Modern UI, SSR/SSG, fast component rendering, responsive split-pane diff viewer |
| **API Gateway** | FastAPI, Uvicorn, Pydantic v2 | Asynchronous Python framework, native Pydantic validation, auto-generated OpenAPI docs |
| **Workflow Control** | LangGraph | Stateful multi-agent graph orchestration, conditional routing, retry nodes, parallel branches |
| **LLM Integration** | LangChain | Standardized prompt templates, structured output parsers, LLM provider switching |
| **Primary LLM** | Google Gemini (`gemini-2.5-flash`, `gemini-2.5-pro`) | High token limit, fast execution, state-of-the-art code reasoning |
| **Secondary LLM** | Mistral AI (`codestral-latest`, `mistral-large-latest`) | Independent secondary provider for high-availability fallback |
| **Embedding Model** | Google Gemini Embeddings (`text-embedding-004`) | Native integration with Gemini ecosystem, 768-dimensional embeddings |
| **Database & Vector Store** | MongoDB Atlas | Unified document storage for reviews/findings + MongoDB Atlas Vector Search for RAG embeddings |
| **Observability** | LangSmith | End-to-end tracing of multi-agent state execution, prompt evaluation, token usage analysis |

---

## 3. Data Flow & Execution Pipeline

1. **Submission**: User submits code snippet and selects mode (`quick` or `deep`) on Next.js frontend.
2. **Validation**: FastAPI receives `POST /api/review`, validates payload size ($<50$KB), detects code language, normalizes line endings, and builds line mapping.
3. **Graph Initialization**: FastAPI passes normalized input into LangGraph `ReviewState`.
4. **Agent Execution**:
   - **Quick Mode**: Invokes `CodeAnalysisAgent` and `BugDetectionAgent` in parallel, then branches directly to `SynthesizerAgent`.
   - **Deep Mode**:
     - Executes `CodeAnalysisAgent`, `BugDetectionAgent`, `SecurityAgent`, `QualityReadabilityAgent`, and `ComplexityAgent` in parallel.
     - Agents issue queries to RAG retriever (vector search over security/clean code docs using `text-embedding-004`).
     - State transitions to `RefactoringAgent` which produces refactored code.
     - State transitions to `ValidationAgent` (AST syntax check + intent check). If validation fails, retries refactoring up to 2 times before safe fallback.
5. **Synthesis & Storage**: `SynthesizerAgent` deduplicates findings, computes aggregate metrics, writes review record to MongoDB Atlas (`code_reviews`, `review_findings`, `agent_runs`).
6. **Response**: FastAPI returns unified output JSON to Next.js UI for display, side-by-side code diff, and Markdown export.

---

## 4. LLM Router & Fallback Strategy

The LLM Router (`backend/app/services/llm/router.py`) abstracts LLM calls behind a unified interface:

- **Primary Call**: `ChatGoogleGenerativeAI(model="gemini-2.5-flash")` or `gemini-2.5-pro`.
- **Trigger Conditions for Fallback**:
  - API Connection Timeout ($>15$ seconds)
  - HTTP status codes `429` (Rate limit), `500`, `502`, `503`
  - Repeated malformed structured output validation failures
- **Fallback Execution**: Switches to `ChatMistralAI(model="codestral-latest")` or `mistral-large-latest`.
- **Telemetry**: Records fallback events in `execution_metadata` and logs traces to LangSmith.

---

## 5. MongoDB Atlas Schema Design

### Collections Overview:
1. `code_reviews`: Primary document store for overall code review requests and summaries.
2. `review_findings`: Granular findings associated with a specific `review_id`.
3. `agent_runs`: Audit trail for agent executions, prompt inputs, raw LLM outputs, and latency metrics.
4. `rag_documents`: Vector-indexed knowledge base for security standards (OWASP, CWE) and language-specific clean code guidelines.

### Collection: `code_reviews`
```json
{
  "_id": "ObjectId",
  "review_id": "rev_987654321",
  "created_at": "2026-09-09T21:24:00Z",
  "mode": "deep",
  "language": "python",
  "original_code": "def process_data(d):\n    ...",
  "summary": {
    "overview": "Data processing script with security risks.",
    "verdict": "major_issues"
  },
  "metrics": {
    "complexity_score": 6.8,
    "readability_score": 7.2
  },
  "refactored_code": "def process_data(data: dict) -> list:\n    ...",
  "status": "completed"
}
```

### Collection: `rag_documents` (Vector Search Index)
```json
{
  "_id": "ObjectId",
  "doc_id": "rag_cwe_476",
  "title": "CWE-476: NULL Pointer Dereference Prevention",
  "category": "security",
  "language": "general",
  "content": "Always validate pointers or references before access...",
  "embedding": [0.012, -0.045, 0.089, "... (768 dimensions) ..."]
}
```

*Vector Index Configuration (MongoDB Atlas)*:
- Index Name: `vector_index`
- Metric: `cosine`
- Dimensions: `768` (matching Gemini `text-embedding-004`)
