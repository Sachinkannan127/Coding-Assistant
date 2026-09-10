# AI Code Review & Refactoring Platform

[![Phase 20 Complete](https://img.shields.io/badge/Phase-20%20Performance%20Optimization%20%26%20Streaming%20Complete-green.svg)](#phase-status)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Frontend-Next.js%2014-000000.svg)](https://nextjs.org/)
[![LangGraph](https://img.shields.io/badge/Orchestration-LangGraph-FF6F61.svg)](https://langchain-ai.github.io/langgraph/)

An enterprise-grade, multi-agent AI system that analyzes code, detects bugs and security vulnerabilities, assesses complexity/readability metrics, generates AST-validated refactorings, and provides interactive side-by-side comparisons with Markdown export.

---

## 🏗 System Architecture Overview

- **Frontend**: Next.js 14 App Router, TypeScript, Glassmorphic HSL Theme, Code Input Workspace, Interactive Findings Explorer, Metrics Dashboard, Refactoring Diff View, Markdown Report Exporter, and AbortController request timeout safeguards.
- **Backend Gateway**: FastAPI, Pydantic v2, CORS middleware, OpenAPI specification, `GET /api/review/{id}/export` Markdown download endpoint, and CodeValidationError boundaries.
- **Workflow Controller**: Stateful LangGraph graph engine with parallel execution branches and validation retry loops.
- **AI Framework**: LangChain with primary provider **Google Gemini** (`gemini-2.5-flash`, `gemini-2.5-pro`) and secondary fallback provider **Mistral AI** (`codestral-latest`, `mistral-large-latest`).
- **Embedding & RAG**: Google Gemini Embeddings (`text-embedding-004`) + MongoDB Atlas Vector Search.
- **Persistence**: MongoDB Atlas (Collections: `code_reviews`, `review_findings`, `agent_runs`, `rag_documents`) with graceful offline fallback.
- **Observability**: LangSmith end-to-end multi-agent tracing isolated in `backend/app/services/tracing/`.

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
│   │   ├── models/           # Pydantic v2 schemas for collections
│   │   ├── graph/            # LangGraph workflow state & orchestration
│   │   ├── agents/           # 8 specialized agent roles
│   │   └── services/         # LLM Router, Embeddings, RAG, Code Validator, Tracing
│   └── requirements.txt      # Backend dependencies
├── docs/
│   ├── requirements.md       # Detailed system & schema specs
│   ├── architecture.md       # High-level architecture & MongoDB schemas
│   └── agent-design.md       # 8 Agent roles & LangGraph ReviewState design
├── frontend/
│   ├── app/
│   │   ├── components/       # Header, CodeEditor, ReviewSummary, MetricsDashboard, FindingsExplorer, RefactoringDiff, DiffUtils, ExportUtils
│   │   ├── globals.css       # HSL Dark Glassmorphism CSS system
│   │   ├── layout.tsx        # Next.js App Router root layout
│   │   └── page.tsx          # Full-stack AI review studio dashboard
│   ├── package.json          # Node dependencies
│   └── tsconfig.json         # TypeScript configuration
├── tests/                    # 18 pytest test modules (84 test cases)
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
- **Review API Endpoint**: `POST http://localhost:8000/api/review`
- **Streaming Review API Endpoint**: `POST http://localhost:8000/api/review/stream`
- **Report Export Endpoint**: `GET http://localhost:8000/api/review/{id}/export`

### 3. Running Backend Tests & AI Evaluation
```bash
# Run full pytest test suite (84 test cases)
python -m pytest tests/

# Run AI System Evaluation Benchmark Tool
python scripts/run_ai_evaluation.py
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
- [x] **Phase 8**: RAG Knowledge System
- [x] **Phase 9**: Quick Scan & Deep Review Workflows
- [x] **Phase 10**: Refactoring & Validation Loop
- [x] **Phase 11**: Review Synthesis & Persistence
- [x] **Phase 12**: LangSmith Tracing & Evaluation
- [x] **Phase 13**: FastAPI Review API
- [x] **Phase 14**: Next.js Frontend Review Experience
- [x] **Phase 15**: Original vs Refactored Side-by-Side Comparison
- [x] **Phase 16**: Markdown Export
- [x] **Phase 17**: Graceful Errors & Edge Cases
- [x] **Phase 18**: End-to-End Testing & AI Evaluation
- [x] **Phase 19**: Security Hardening
- [x] **Phase 20**: Performance Optimization
- [ ] **Phase 21**: Production Deployment
- [ ] **Phase 22**: Documentation & v1.0 Release
