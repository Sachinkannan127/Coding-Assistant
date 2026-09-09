# AI Code Review & Refactoring Platform

[![Phase 7 Complete](https://img.shields.io/badge/Phase-7%20LangGraph%20Orchestration%20Complete-green.svg)](#phase-status)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Frontend-Next.js%2014-000000.svg)](https://nextjs.org/)
[![LangGraph](https://img.shields.io/badge/Orchestration-LangGraph-FF6F61.svg)](https://langchain-ai.github.io/langgraph/)

An enterprise-grade, multi-agent AI system that analyzes code, detects bugs and security vulnerabilities, assesses complexity/readability metrics, generates AST-validated refactorings, and provides interactive side-by-side comparisons with Markdown export.

---

## 🏗 System Architecture Overview

- **Frontend**: Next.js 14 App Router, TypeScript, Vanilla CSS (Dark mode + Glassmorphism UI), Side-by-side Diff Viewer.
- **Backend Gateway**: FastAPI, Pydantic v2, CORS middleware, OpenAPI specification.
- **Workflow Controller**: Stateful LangGraph graph engine with parallel execution branches and validation retry loops.
- **AI Framework**: LangChain with primary provider **Google Gemini** (`gemini-2.5-flash`, `gemini-2.5-pro`) and secondary fallback provider **Mistral AI** (`codestral-latest`, `mistral-large-latest`).
- **Embedding & RAG**: Google Gemini Embeddings (`text-embedding-004`) + MongoDB Atlas Vector Search.
- **Persistence**: MongoDB Atlas (Collections: `code_reviews`, `review_findings`, `agent_runs`, `rag_documents`).
- **Observability**: LangSmith end-to-end multi-agent tracing.

---

## 📁 Repository Structure

```
.
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── config.py         # Pydantic settings & env loader
│   │   ├── main.py           # FastAPI app entrypoint & /health route
│   │   ├── db/               # Async MongoDB client & database manager
│   │   │   ├── mongodb.py
│   │   │   └── repositories/ # ReviewRepository & RAGRepository
│   │   ├── models/           # Pydantic v2 schemas for collections
│   │   └── services/         # LLM Provider Layer (Gemini + Mistral Router & Embeddings)
│   │       └── llm/
│   │           ├── router.py
│   │           └── embeddings.py
│   └── requirements.txt      # Backend dependencies
├── docs/
│   ├── requirements.md       # Detailed system & schema specs
│   ├── architecture.md       # High-level architecture & MongoDB schemas
│   └── agent-design.md       # 8 Agent roles & LangGraph ReviewState design
├── frontend/
│   ├── app/                  # Next.js 14 App Router UI
│   ├── package.json          # Node dependencies
│   └── tsconfig.json         # TypeScript configuration
├── tests/
│   ├── __init__.py
│   ├── test_health.py        # Pytest health check tests
│   ├── test_mongodb.py       # Pytest MongoDB schema & model tests
│   ├── test_llm_router.py   # Pytest LLM Router primary & fallback tests
│   └── test_embeddings.py   # Pytest Gemini text-embedding-004 tests
├── .env.example              # Environment variables template
└── README.md
```

---

## ⚡ Quick Start Guide

### 1. Prerequisites
- Python 3.11+
- Node.js 18+ & npm
- MongoDB Atlas cluster (or local MongoDB)

### 2. Backend Setup
```bash
# Navigate to repository root
cd d:/pro/Codepilot

# Install Python dependencies
pip install -r backend/requirements.txt

# Copy environment template
cp .env.example .env

# Run FastAPI backend
python -m uvicorn backend.app.main:app --reload --port 8000
```
FastAPI documentation will be accessible at:
- **Landing Page Endpoint**: `http://localhost:8000/`
- **Interactive Swagger Docs**: `http://localhost:8000/docs`
- **Health Check Endpoint**: `http://localhost:8000/health`

### 3. Running Backend Tests
```bash
python -m pytest tests/
```

### 4. Frontend Setup
```bash
# Navigate to frontend folder
cd frontend

# Install Node dependencies
npm install

# Start Next.js development server
npm run dev
```
Next.js web application will be accessible at `http://localhost:3000`.

---

## 📍 Implementation Roadmap

- [x] **Phase 0**: Requirements & Architecture Validation (`docs/`)
- [x] **Phase 1**: Full-Stack Project Foundation (FastAPI + Next.js + Health API)
- [x] **Phase 2**: MongoDB Persistence Layer
- [x] **Phase 3**: Gemini & Mistral Provider Layer
- [x] **Phase 4**: Code Validation & Language Detection
- [x] **Phase 5**: LangChain Foundation
- [x] **Phase 6**: Multi-Agent Review System
- [x] **Phase 7**: LangGraph Orchestration
- [ ] **Phase 8**: RAG Knowledge System
- [ ] **Phase 9**: Quick Scan & Deep Review Workflows
- [ ] **Phase 10**: Refactoring & Validation Loop
- [ ] **Phase 11**: Review Synthesis & Persistence
- [ ] **Phase 12**: LangSmith Tracing & Evaluation
- [ ] **Phase 13**: FastAPI Review API
- [ ] **Phase 14**: Next.js Frontend Review Experience
- [ ] **Phase 15**: Original vs Refactored Side-by-Side Comparison
- [ ] **Phase 16**: Markdown Export
- [ ] **Phase 17**: Graceful Errors & Edge Cases
- [ ] **Phase 18**: End-to-End Testing & AI Evaluation
- [ ] **Phase 19**: Security Hardening
- [ ] **Phase 20**: Performance Optimization
- [ ] **Phase 21**: Production Deployment
- [ ] **Phase 22**: Documentation & v1.0 Release
