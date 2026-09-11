"use client";

import React, { useState, useEffect } from "react";

import { useAuth, useUser } from "@clerk/nextjs";
import { useRouter } from "next/navigation";
import LandingHeader from "./components/LandingHeader";
import LandingPage from "./components/LandingPage";
import CodeEditor from "./components/CodeEditor";
import ReviewSummary from "./components/ReviewSummary";
import MetricsDashboard from "./components/MetricsDashboard";
import FindingsExplorer from "./components/FindingsExplorer";
import RefactoringDiff from "./components/RefactoringDiff";
import CodeSandbox, { ExecutionResult } from "./components/CodeSandbox";
import CompilerSandboxView from "./components/CompilerSandboxView";
import McpConnectorsView from "./components/McpConnectorsView";
import CodeExplanationModal from "./components/CodeExplanationModal";
import { Sparkles, ArrowLeft, Layout, Code2, Terminal, Network } from "lucide-react";

const DEFAULT_SAMPLE = `def calculate_user_discount(user, cart_items):
    # Calculate initial subtotal
    subtotal = 0
    for item in cart_items:
        subtotal += item['price'] * item['quantity']
    
    # Insecure direct key access & missing error bounds
    if user['role'] == 'VIP':
        discount = subtotal * 0.20
    else:
        discount = subtotal * 0.05
        
    final_total = subtotal - discount
    return final_total
`;

const MAX_CHAR_LIMIT = 50000; // 50 KB ceiling

export default function Home() {
  const { getToken } = useAuth();
  const { isSignedIn, isLoaded } = useUser();
  const router = useRouter();
  const [currentView, setCurrentView] = useState<"landing" | "studio" | "compiler" | "mcp">("landing");

  // Automatically reset to Landing view if user logs out while in studio/compiler/mcp
  useEffect(() => {
    if (isLoaded && !isSignedIn && currentView !== "landing") {
      setCurrentView("landing");
    }
  }, [isSignedIn, isLoaded, currentView]);

  const handleSwitchView = (targetView: "landing" | "studio" | "compiler" | "mcp") => {
    if (targetView === "landing") {
      setCurrentView("landing");
      return;
    }
    if (!isSignedIn) {
      router.push("/sign-in");
      return;
    }
    setCurrentView(targetView);
  };


  const [code, setCode] = useState<string>(DEFAULT_SAMPLE);
  const [language, setLanguage] = useState<string>("auto");
  const [framework, setFramework] = useState<string>("none");
  const [reviewMode, setReviewMode] = useState<"quick" | "deep">("quick");
  
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [reviewResult, setReviewResult] = useState<any | null>(null);
  const [activeTab, setActiveTab] = useState<"summary" | "findings" | "metrics" | "diff">("summary");

  // Code Sandbox Execution State
  const [sandboxLoading, setSandboxLoading] = useState<boolean>(false);
  const [sandboxResult, setSandboxResult] = useState<ExecutionResult | null>(null);
  const [showSandbox, setShowSandbox] = useState<boolean>(false);

  // Code Explanation Modal State
  const [showExplanationModal, setShowExplanationModal] = useState<boolean>(false);

  const handleExecuteSandbox = async (targetCode?: string, stdinData: string = "") => {
    const codeToRun = targetCode || code;
    if (!codeToRun || !codeToRun.trim()) {
      setError("Code input cannot be empty for sandbox execution.");
      return;
    }

    setSandboxLoading(true);
    setShowSandbox(true);

    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8005";
      const token = await getToken();
      const headers: Record<string, string> = { "Content-Type": "application/json" };
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }

      const response = await fetch(`${baseUrl}/api/sandbox/execute`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          code: codeToRun,
          language: language,
          stdin_data: stdinData,
          timeout_seconds: 5
        })
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Sandbox Error: ${response.status} ${response.statusText}`);
      }

      const data: ExecutionResult = await response.json();
      setSandboxResult(data);
    } catch (err: any) {
      setSandboxResult({
        stdout: "",
        stderr: `Sandbox Execution Error: ${err.message || "Failed to communicate with sandbox runner backend."}`,
        exit_code: 1,
        status: "error",
        execution_time_ms: 0,
        language_used: language
      });
    } finally {
      setSandboxLoading(false);
    }
  };

  const handleReviewSubmit = async () => {
    // 1. Client-Side Input Validation
    if (!code || !code.trim()) {
      setError("Code input cannot be empty. Please paste or enter source code to analyze.");
      return;
    }

    if (code.length > MAX_CHAR_LIMIT) {
      setError(`Payload size (${code.length.toLocaleString()} chars) exceeds limit of 50 KB (${MAX_CHAR_LIMIT.toLocaleString()} chars). Please submit a smaller snippet.`);
      return;
    }

    setLoading(true);
    setError(null);

    // 2. AbortController Request Timeout (45 seconds)
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 45000);

    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8005";
      const token = await getToken();
      const headers: Record<string, string> = { "Content-Type": "application/json" };
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }

      const response = await fetch(`${baseUrl}/api/review`, {
        method: "POST",
        headers,
        signal: controller.signal,
        body: JSON.stringify({
          code: code,
          language: language,
          mode: reviewMode,
        }),
      });


      clearTimeout(timeoutId);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Server error: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      setReviewResult(data);
      setActiveTab("summary");
    } catch (err: any) {
      clearTimeout(timeoutId);
      if (err.name === "AbortError") {
        setError("Review request timed out after 45 seconds. The server might be processing a large graph or restarting. Please try again.");
      } else if (err.message && err.message.includes("Failed to fetch")) {
        setError("Unable to connect to FastAPI backend server. Ensure the server is running on http://localhost:8000.");
      } else {
        setError(err.message || "Failed to execute code review.");
      }
    } finally {
      setLoading(false);
    }
  };

  const handleApplyRefactoredCode = (newCode: string) => {
    setCode(newCode);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const handleLaunchStudio = () => {
    handleSwitchView("studio");
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  return (
    <div className="app-shell">
      {/* Global Header */}
      <LandingHeader 
        currentView={currentView} 
        onSwitchView={handleSwitchView} 
      />

      {currentView === "landing" ? (
        /* PREMIUM LANDING PAGE VIEW */
        <LandingPage 
          onLaunchStudio={handleLaunchStudio} 
          onLaunchCompiler={() => handleSwitchView("compiler")} 
        />
      ) : currentView === "compiler" ? (
        /* INTERACTIVE COMPILER SANDBOX WORKSPACE VIEW */
        <CompilerSandboxView onSwitchView={handleSwitchView} />
      ) : currentView === "mcp" ? (
        /* MODEL CONTEXT PROTOCOL (MCP) CONNECTORS HUB VIEW */
        <McpConnectorsView onSwitchView={handleSwitchView} />
      ) : (

        /* AI STUDIO WORKSPACE VIEW */
        <main className="container fade-in" style={{ paddingTop: "2rem" }}>
          
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1.5rem", flexWrap: "wrap", gap: "1rem" }}>
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", marginBottom: "0.4rem", flexWrap: "wrap" }}>
                <button 
                  type="button" 
                  onClick={() => setCurrentView("landing")}
                  className="btn-back-pill"
                >
                  <ArrowLeft className="w-4 h-4" />
                  <span>Back to Overview</span>
                </button>
                <button
                  type="button"
                  onClick={() => setCurrentView("compiler")}
                  className="btn-back-pill"
                  style={{ background: "rgba(168, 85, 247, 0.15)", color: "#c084fc", border: "1px solid rgba(168, 85, 247, 0.3)" }}
                >
                  <Terminal className="w-4 h-4" />
                  <span>Compiler Sandbox</span>
                </button>
                <button
                  type="button"
                  onClick={() => setCurrentView("mcp")}
                  className="btn-back-pill"
                  style={{ background: "rgba(56, 189, 248, 0.15)", color: "#38bdf8", border: "1px solid rgba(56, 189, 248, 0.3)" }}
                >
                  <Network className="w-4 h-4" />
                  <span>MCP Connectors Hub</span>
                </button>
              </div>
              <h1 style={{ fontSize: "1.75rem", fontWeight: 800, letterSpacing: "-0.02em" }}>
                AI Code Review & Refactoring Studio Workspace
              </h1>
              <p style={{ color: "var(--text-secondary)", fontSize: "0.9rem", marginTop: "0.4rem" }}>
                Powered by LangGraph 8-agent graph orchestration, Google Gemini 2.5, Mistral router, and AST syntax tree validation.
              </p>
            </div>

            <div style={{ display: "flex", gap: "0.75rem" }}>
              <span className="badge badge-indigo"><Sparkles className="w-3.5 h-3.5 mr-1" /> LangGraph Active</span>
              <span className="badge badge-success"><Code2 className="w-3.5 h-3.5 mr-1" /> AST Validator Ready</span>
            </div>
          </div>

          {error && (
            <div style={{ background: "rgba(244, 63, 94, 0.12)", border: "1px solid rgba(244, 63, 94, 0.3)", padding: "1rem 1.25rem", borderRadius: "10px", marginBottom: "1.5rem", color: "#fb7185", display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "1rem" }}>
              <div>
                <strong>⚠️ Review Alert:</strong> {error}
                <div style={{ fontSize: "0.8rem", color: "var(--text-secondary)", marginTop: "0.2rem" }}>
                  Ensure the FastAPI backend is running on <code>http://localhost:8000</code>.
                </div>
              </div>
              <div style={{ display: "flex", gap: "0.5rem" }}>
                <button className="btn btn-primary btn-sm" onClick={handleReviewSubmit}>Retry Request</button>
                <button className="btn btn-secondary btn-sm" onClick={() => setError(null)}>Dismiss</button>
              </div>
            </div>
          )}

          <div className="app-grid">
            {/* Left Column: Code Input Workspace & Sandbox Terminal */}
            <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
              <CodeEditor
                code={code}
                setCode={setCode}
                language={language}
                setLanguage={setLanguage}
                framework={framework}
                setFramework={setFramework}
                reviewMode={reviewMode}
                setReviewMode={setReviewMode}
                onSubmit={handleReviewSubmit}
                loading={loading}
                onExecuteSandbox={() => handleExecuteSandbox(code)}
                sandboxLoading={sandboxLoading}
                onExplainCode={() => setShowExplanationModal(true)}
              />

              {/* Permanent Code Sandbox Execution Terminal */}
              <CodeSandbox
                code={code}
                language={language}
                onExecute={(stdinData) => handleExecuteSandbox(code, stdinData)}
                loading={sandboxLoading}
                result={sandboxResult}
                onClear={() => {
                  setSandboxResult(null);
                }}
              />
            </div>

            {/* Right Column: Review Results & Analysis Dashboard */}
            <div>
              {!reviewResult && !loading && (
                <div className="card" style={{ height: "100%", display: "flex", flexDirection: "column", justifyContent: "center", alignItems: "center", minHeight: "450px", textAlign: "center", padding: "3rem" }}>
                  <div style={{ fontSize: "3.5rem", marginBottom: "1rem" }}>⚡</div>
                  <h3 style={{ fontSize: "1.25rem", fontWeight: 700, marginBottom: "0.5rem" }}>Ready for Code Analysis</h3>
                  <p style={{ color: "var(--text-secondary)", fontSize: "0.875rem", maxWidth: "400px", lineHeight: 1.6 }}>
                    Paste your code snippet or choose a sample preset, select language & review depth, then click <strong>Launch Multi-Agent Review</strong>.
                  </p>
                </div>
              )}

              {loading && (
                <div className="card" style={{ height: "100%", display: "flex", flexDirection: "column", justifyContent: "center", alignItems: "center", minHeight: "450px", textAlign: "center", padding: "3rem" }}>
                  <div className="spinner" style={{ width: "40px", height: "40px", borderWidth: "3px", marginBottom: "1.5rem" }}></div>
                  <h3 style={{ fontSize: "1.25rem", fontWeight: 700, marginBottom: "0.5rem" }}>Orchestrating Multi-Agent Pipeline...</h3>
                  <p style={{ color: "var(--text-secondary)", fontSize: "0.875rem", maxWidth: "420px", lineHeight: 1.6 }}>
                    {reviewMode === "deep" ? (
                      "Running Security, Quality, Complexity, Bug Detection, RAG Context Retrieval, Refactoring, and AST Validation nodes..."
                    ) : (
                      "Running Quick Scan for rapid bug detection and security analysis..."
                    )}
                  </p>
                  <div style={{ marginTop: "1.5rem", display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
                    <span className="badge badge-indigo">Security Node</span>
                    <span className="badge badge-purple">Quality Node</span>
                    <span className="badge badge-cyan">AST Validator</span>
                  </div>
                </div>
              )}

              {reviewResult && !loading && (
                <div>
                  {/* Result Navigation Tabs */}
                  <div className="tabs-container">
                    <button
                      type="button"
                      className={`tab-btn ${activeTab === "summary" ? "active" : ""}`}
                      onClick={() => setActiveTab("summary")}
                    >
                      <span>📊</span> Executive Summary
                    </button>

                    <button
                      type="button"
                      className={`tab-btn ${activeTab === "findings" ? "active" : ""}`}
                      onClick={() => setActiveTab("findings")}
                    >
                      <span>🔍</span> Findings ({reviewResult.findings?.length || 0})
                    </button>

                    <button
                      type="button"
                      className={`tab-btn ${activeTab === "metrics" ? "active" : ""}`}
                      onClick={() => setActiveTab("metrics")}
                    >
                      <span>📈</span> Metrics
                    </button>

                    <button
                      type="button"
                      className={`tab-btn ${activeTab === "diff" ? "active" : ""}`}
                      onClick={() => setActiveTab("diff")}
                    >
                      <span>🛠️</span> Refactored Diff
                    </button>
                  </div>

                  {/* Tab Content Panes */}
                  {activeTab === "summary" && (
                    <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
                      <ReviewSummary
                        reviewResult={reviewResult}
                        originalCode={code}
                        reviewId={reviewResult.review_id}
                        verdict={reviewResult.verdict}
                        ratingScore={reviewResult.rating_score}
                        executiveSummary={reviewResult.executive_summary}
                        totalFindings={reviewResult.findings?.length || 0}
                        executionTime={reviewResult.execution_time_seconds}
                        reviewMode={reviewResult.review_mode || reviewMode}
                        modelUsed={reviewResult.model_used}
                        languageDetected={reviewResult.language_detected || reviewResult.input_metadata?.language || language}
                      />

                      <MetricsDashboard metrics={reviewResult.metrics} />
                    </div>
                  )}

                  {activeTab === "findings" && (
                    <FindingsExplorer
                      findings={reviewResult.findings || []}
                      ragDocuments={reviewResult.rag_documents_cited}
                    />
                  )}

                  {activeTab === "metrics" && (
                    <MetricsDashboard metrics={reviewResult.metrics} />
                  )}

                  {activeTab === "diff" && (
                    <RefactoringDiff
                      originalCode={code}
                      refactoredCode={reviewResult.refactored_code}
                      refactoringExplanation={reviewResult.refactoring_explanation}
                      astValidated={reviewResult.ast_validated ?? true}
                      languageDetected={reviewResult.language_detected || reviewResult.input_metadata?.language || language}
                      findings={reviewResult.findings || []}
                      onApplyCode={handleApplyRefactoredCode}
                      onTestRefactoredCode={(refactored) => handleExecuteSandbox(refactored)}
                    />
                  )}
                </div>
              )}
            </div>
          </div>
        </main>
      )}

      <CodeExplanationModal
        isOpen={showExplanationModal}
        onClose={() => setShowExplanationModal(false)}
        code={code}
        language={language}
      />
    </div>
  );
}
