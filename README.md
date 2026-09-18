# 🚀 Codepilot: Enterprise AI Code Review, Refactoring & Execution Platform

[![Release v1.0.0](https://img.shields.io/badge/Release-v1.0.0%20Production%20Ready-brightgreen.svg)](#implementation-roadmap)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Frontend-Next.js%2014-000000.svg)](https://nextjs.org/)
[![LangGraph](https://img.shields.io/badge/Orchestration-LangGraph-FF6F61.svg)](https://langchain-ai.github.io/langgraph/)
[![Clerk Auth](https://img.shields.io/badge/Auth-Clerk-6C47FF.svg)](https://clerk.com/)
[![MongoDB Atlas](https://img.shields.io/badge/Database-MongoDB%20Atlas-47A248.svg)](https://www.mongodb.com/atlas)

**Codepilot** is an enterprise-grade, multi-agent AI software engineering platform. It analyzes source code for syntax flaws, security vulnerabilities, performance bottlenecks, and architectural debt, generates AST-validated refactorings, executes code in a multi-language compiler sandbox, provides line-by-line AI explanations, auto-generates unit test suites, and integrates with external repositories via Model Context Protocol (MCP) connectors.

---

## 📑 Table of Contents

- [🏗 System Architecture Overview](#-system-architecture-overview)
- [✨ Key Features](#-key-features)
- [🤖 Multi-Agent Review Architecture](#-multi-agent-review-architecture)
- [📁 Repository Directory Structure](#-repository-directory-structure)
- [🛠 Tech Stack & Frameworks](#-tech-stack--frameworks)
- [⚡ Quick Start & Installation Guide](#-quick-start--installation-guide)
  - [1. Prerequisites](#1-prerequisites)
  - [2. Environment Configuration](#2-environment-configuration)
  - [3. Backend Setup (FastAPI)](#3-backend-setup-fastapi)
  - [4. Frontend Setup (Next.js 14)](#4-frontend-setup-nextjs-14)
  - [5. Containerized Deployment (Docker Compose)](#5-containerized-deployment-docker-compose)
- [📡 API Documentation & Endpoints](#-api-documentation--endpoints)
- [🧪 Testing & AI System Evaluation](#-testing--ai-system-evaluation)
- [📍 Implementation Roadmap](#-implementation-roadmap)
- [🤝 Contributing & License](#-contributing--license)

---

## 🏗 System Architecture Overview

```
                          ┌───────────────────────────────────────────────┐
                          │         Next.js 14 Web Application            │
                          │  (Monaco Editor, Diff View, Sandbox, MCP UI) │
                          └───────────────────────┬───────────────────────┘
                                                  │ HTTP / REST / SSE
                                                  ▼
                          ┌───────────────────────────────────────────────┐
                          │            FastAPI Backend Gateway            │
                          │   (Auth Middleware, Rate Limiter, CORS)       │
                          └──────┬────────────────┬───────────────┬───────┘
                                 │                │               │
      ┌──────────────────────────┴───┐     ┌──────┴─────────┐    ┌┴──────────────────────────┐
      │   LangGraph Workflow Engine  │     │ Compiler       │    │  MCP Connector Gateway    │
      │   (8 Multi-Agent System)     │     │ Sandbox Engine │    │  (GitHub & Ext. Protocol) │
      └──────────────┬───────────────┘     └────────────────┘    └───────────────────────────┘
                     │
      ┌──────────────┴──────────────────┐
      ▼                                 ▼
┌───────────────────────────┐     ┌───────────────────────────┐
│ Primary LLM Engine        │     │ Secondary Fallback LLM    │
│ Google Gemini 2.5 Flash   │     │ Mistral AI / Codestral    │
└───────────────────────────┘     └───────────────────────────┘
```

---

## ✨ Key Features

### 🔍 1. Multi-Agent AI Code Review Engine
- **Dual Analysis Modes**:
  - **Quick Scan**: Rapid, single-pass static inspection for high-priority syntax and security risks.
  - **Deep Review**: Comprehensive multi-stage graph analysis with AST compilation check, parallel agent evaluation, and refactoring validation loops.
- **AST & Linter Guardrails**: Automatically verifies generated code edits against native syntax parsers before returning suggestions to the user.

### ⚡ 2. Multi-Language Compiler Sandbox
- Interactive code execution environment supporting **Python, JavaScript, TypeScript, C++, Java, Go, and Rust**.
- Tracks **execution time (ms)**, **memory usage (MB)**, exit codes, standard output (`stdout`), and standard error (`stderr`).

### 💡 3. Line-by-Line AI Explanation & Test Case Generator
- **Code Explainer**: Breaks down complex algorithms, functions, and database queries into human-readable explanations with customizable detail levels.
- **Automated Test Generator**: Synthesizes ready-to-run unit test suites using standard test frameworks (pytest, Jest, JUnit, Go testing).

### 🔌 4. Model Context Protocol (MCP) & Connectors
- Connects directly to external codebases, **GitHub Repositories**, and custom MCP servers.
- Retrieves live context, repository file trees, and project dependencies for contextualized code reviews.

### 🛡 5. Enterprise Authentication & Security
- Integrated **Clerk Authentication** with JWT token validation and custom fallback user sessions.
- Built-in **Security Headers Middleware**, IP-based **Rate Limiting**, and Pydantic v2 data sanitization to scrub sensitive credentials from logs.

---

## 🤖 Multi-Agent Review Architecture

The core code analysis engine is orchestrated using **LangGraph** with 8 specialized agent roles:

| Agent Role | Responsibility & Focus Area |
| :--- | :--- |
| 🛡 **Security Auditor** | Detects OWASP Top 10 vulnerabilities, SQL injection, XSS, insecure deserialization, and hardcoded secrets. |
| ⚡ **Performance Optimizer** | Identifies $O(N^2)$ algorithm bottlenecks, memory leaks, unoptimized queries, and unnecessary re-renders. |
| 🏗 **Architectural Advisor** | Evaluates SOLID principles, modularity, DRY compliance, dependency coupling, and design patterns. |
| 📝 **Syntax & Style Reviewer** | Checks language-specific idiomatic style, PEP8 / ESLint standards, naming conventions, and docstrings. |
| 🧪 **Test Coverage Analyst** | Inspects edge-case coverage, missing unit tests, boundary conditions, and mock implementations. |
| 📚 **RAG & Context Agent** | Queries MongoDB Vector Search (`text-embedding-004`) for historical review patterns and company standards. |
| 🛠 **Refactoring Engine** | Generates side-by-side AST-valid unified diffs and optimized replacements. |
| ✍️ **Synthesis & Exporter** | Aggregates findings from all agents, calculates overall quality scores (0-100), and generates Markdown reports. |

---

## 📁 Repository Directory Structure

```
Codepilot/
├── backend/                        # FastAPI Backend Application
│   ├── app/
│   │   ├── api/                    # REST API Routers
│   │   │   ├── auth_routes.py      # Clerk Auth & Session Validation
│   │   │   ├── connector_routes.py # Repository & MCP Connections
│   │   │   ├── explain_routes.py   # AI Code Explainer & Test Generator
│   │   │   ├── mcp_routes.py       # Model Context Protocol Gateway
│   │   │   ├── review_routes.py    # Code Review & Markdown Export
│   │   │   ├── sandbox_routes.py   # Multi-language Compiler Execution
│   │   │   └── user_profile_routes.py # User Profiles & Settings
│   │   ├── agents/                 # 8 Specialized Agent Prompts & Logic
│   │   ├── db/                     # Async MongoDB Client & Repositories
│   │   ├── graph/                  # LangGraph ReviewState & Workflow Graph
│   │   ├── mcp/                    # MCP Client & Gateway Services
│   │   ├── middleware/             # Security Headers & Rate Limiter
│   │   ├── models/                 # Pydantic v2 Collection Schemas
│   │   ├── services/               # LLM Router, Embeddings, RAG, Tracing
│   │   ├── config.py               # Application Settings Loader
│   │   └── main.py                 # FastAPI Application Gateway Entrypoint
│   └── requirements.txt            # Backend Python Dependencies
├── frontend/                       # Next.js 14 App Router Frontend
│   ├── app/
│   │   ├── components/             # React UI Components
│   │   │   ├── CodeEditor.tsx      # Code Workspace & Editing Engine
│   │   │   ├── CodeExplanationModal.tsx # Line-by-Line AI Explanations
│   │   │   ├── CompilerSandboxView.tsx  # Multi-language Execution UI
│   │   │   ├── FindingsExplorer.tsx     # Filterable Issues & Vulnerabilities
│   │   │   ├── LandingPage.tsx          # Marketing & Hero Section
│   │   │   ├── McpConnectorsView.tsx    # GitHub & MCP Connectors Manager
│   │   │   ├── RefactoringDiff.tsx      # Side-by-Side Diff Comparison
│   │   │   ├── ReviewSummary.tsx        # Scores & Metric Cards
│   │   │   └── TestCasesModal.tsx       # Auto Unit Test Generator UI
│   │   ├── sign-in/                # Clerk Sign-in Page
│   │   ├── sign-up/                # Clerk Sign-up Page
│   │   ├── globals.css             # HSL Dark Glassmorphism CSS System
│   │   ├── layout.tsx              # Root Next.js App Layout & Providers
│   │   └── page.tsx                # Main Application Dashboard Workspace
│   ├── package.json                # Frontend Node Dependencies
│   └── tsconfig.json               # TypeScript Compiler Configuration
├── docs/                           # Architecture Specs & Schema Manuals
├── tests/                          # Automated Pytest Test Suite (89 Test Cases)
├── scripts/                        # AI Evaluation & Benchmark Scripts
├── Dockerfile.backend              # Backend Container Build Instructions
├── Dockerfile.frontend             # Frontend Container Build Instructions
├── docker-compose.yml              # Production Container Orchestration
├── .env                            # Environment Configuration File
└── README.md                       # Project Documentation
```

---

## 🛠 Tech Stack & Frameworks

- **Backend**: Python 3.11, FastAPI, Pydantic v2, Uvicorn
- **Orchestration**: LangGraph, LangChain Core
- **AI Models**: Google Gemini (`gemini-2.5-flash`, `gemini-2.5-pro`), Mistral AI (`codestral-latest`, `mistral-large-latest`)
- **Database & RAG**: MongoDB Atlas, Motor (Async Driver), Google `text-embedding-004`
- **Frontend**: Next.js 14 (App Router), TypeScript, Tailwind CSS / Vanilla HSL Glassmorphism, Lucide React Icons
- **Authentication**: Clerk React/Next SDK + PyJWT / Clerk Backend Validation
- **Observability**: LangSmith Multi-Agent Tracing

---

## ⚡ Quick Start & Installation Guide

### 1. Prerequisites
- **Python 3.11+** installed
- **Node.js 18+** & **npm** installed
- **MongoDB** (MongoDB Atlas URI or local instance)

### 2. Environment Configuration
Create or verify the `.env` file in the project root:

```env
# Application Config
APP_NAME="AI Code Review & Refactoring Platform"
APP_VERSION="1.0.0"
ENVIRONMENT="development"
DEBUG=true

# API Gateway Config
HOST="0.0.0.0"
PORT=8005
CORS_ORIGINS="http://localhost:3000,http://127.0.0.1:3000"

# Copy the provided environment configuration template:
cp .env.example .env

# LLM Providers
GEMINI_API_KEY=""
MISTRAL_API_KEY=""

# Database Config
MONGODB_URI="mongodb://localhost:27017"
MONGODB_DATABASE="code_pilot"

# Clerk Authentication Config (Optional in dev)
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=""
CLERK_SECRET_KEY=""
CLERK_ISSUER_URL=""
```


### 3. Backend Setup (FastAPI)

```bash
# Navigate to project root directory
cd Codepilot

# Activate your virtual environment (Windows example)
cd backend
venv\Scripts\activate
cd ..

# Install Python dependencies
pip install -r backend/requirements.txt

# Start the FastAPI server on port 8005
python -m uvicorn backend.app.main:app --reload --port 8005
```

The backend server will run at `http://localhost:8005`.
- **Interactive Swagger Documentation**: `http://localhost:8005/docs`
- **ReDoc API Documentation**: `http://localhost:8005/redoc`
- **Health Check Endpoint**: `http://localhost:8005/health`

### 4. Frontend Setup (Next.js 14)

```bash
# Open a new terminal and navigate to frontend directory
cd Codepilot/frontend

# Install Node dependencies
npm install

# Start Next.js development server
npm run dev
```

The web client will be accessible at `http://localhost:3000`.

### 5. Containerized Deployment (Docker Compose)

To build and run both frontend and backend using Docker Compose:

```bash
docker-compose up --build
```

---

## 📡 API Documentation & Endpoints

### 🔍 Code Review Endpoints (`/api`)
- `POST /api/review` - Trigger a full multi-agent code review (Quick Scan or Deep Review).
- `POST /api/review/stream` - Stream real-time agent execution progress via SSE (Server-Sent Events).
- `GET /api/review/{id}` - Fetch review findings, scores, and refactoring diff by Review ID.
- `GET /api/review/{id}/export` - Download synthesized Markdown code review report.

### 🧪 Code Sandbox Endpoints (`/api`)
- `POST /api/sandbox/execute` - Execute code in isolated compiler environment (Python, JS, TS, C++, Java, Go, Rust).

### 💡 Code Explanation & Test Case Endpoints (`/api`)
- `POST /api/explain` - Generate step-by-step line explanation for code snippets.
- `POST /api/explain/test-cases` - Synthesize unit test cases with standard testing frameworks.

### 🔌 MCP & Connector Endpoints (`/api`)
- `GET /api/connectors` - List user connected repositories and MCP tools.
- `POST /api/connectors` - Add a new GitHub repository or MCP connector.
- `GET /api/mcp/servers` - Discover available MCP servers and tools.

---

## 🧪 Testing & AI System Evaluation

```bash
# Execute unit & integration test suite (89 pytest test cases)
python -m pytest tests/

# Execute AI Evaluation & Benchmarking script
python scripts/run_ai_evaluation.py
```

---

## 📍 Implementation Roadmap

- [x] **Phase 0**: System Architecture & Specification Docs (`docs/`)
- [x] **Phase 1**: FastAPI & Next.js Foundation Setup
- [x] **Phase 2**: MongoDB Atlas Persistence Layer Integration
- [x] **Phase 3**: Gemini 2.5 & Mistral Fallback LLM Gateway
- [x] **Phase 4**: AST Validation & Code Security Guardrails
- [x] **Phase 5**: LangGraph 8-Agent Workflow Graph Orchestration
- [x] **Phase 6**: MongoDB Atlas Vector Search RAG Memory System
- [x] **Phase 7**: Multi-Language Compiler Execution Sandbox
- [x] **Phase 8**: Interactive Code Explanation & Unit Test Generator
- [x] **Phase 9**: Model Context Protocol (MCP) & GitHub Connectors Integration
- [x] **Phase 10**: Clerk Authentication & User Profile Persistence
- [x] **Phase 11**: Next.js HSL Glassmorphic Dashboard Workspace
- [x] **Phase 12**: Interactive Diff Viewer & Markdown Report Exporter
- [x] **Phase 13**: End-to-End Automated Testing (89 Pytest Cases) & AI Benchmarks
- [x] **Phase 14**: Production Docker Containerization & v1.0 Release

---

## 🤝 Contributing & License

Contributions are welcome! Please ensure all pytest test cases pass (`python -m pytest tests/`) before submitting pull requests.

**License**: MIT License - see LICENSE file for details.
