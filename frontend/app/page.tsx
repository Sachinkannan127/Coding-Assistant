"use client";

import React, { useState } from "react";
import Header from "./components/Header";
import CodeEditor from "./components/CodeEditor";
import ReviewSummary from "./components/ReviewSummary";
import MetricsDashboard from "./components/MetricsDashboard";
import FindingsExplorer from "./components/FindingsExplorer";
import RefactoringDiff from "./components/RefactoringDiff";

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

export default function Home() {
  const [code, setCode] = useState<string>(DEFAULT_SAMPLE);
  const [language, setLanguage] = useState<string>("auto");
  const [framework, setFramework] = useState<string>("none");
  const [reviewMode, setReviewMode] = useState<"quick" | "deep">("quick");
  
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [reviewResult, setReviewResult] = useState<any | null>(null);
  const [activeTab, setActiveTab] = useState<"summary" | "findings" | "metrics" | "diff">("summary");

  const handleReviewSubmit = async () => {
    if (!code.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const response = await fetch("http://localhost:8000/api/review", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          code: code,
          language: language,
          mode: reviewMode,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Server error: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      setReviewResult(data);
      setActiveTab("summary");
    } catch (err: any) {
      setError(err.message || "Failed to communicate with FastAPI backend server.");
    } finally {
      setLoading(false);
    }
  };

  const handleApplyRefactoredCode = (newCode: string) => {
    setCode(newCode);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  return (
    <div>
      <Header />

      <main className="container">
        <div style={{ marginBottom: "1.5rem" }}>
          <h1 style={{ fontSize: "2rem", fontWeight: 800, letterSpacing: "-0.02em", marginBottom: "0.4rem" }}>
            AI Code Review & Automated Refactoring Studio
          </h1>
          <p style={{ color: "var(--text-secondary)", fontSize: "0.95rem" }}>
            Powered by LangGraph multi-agent orchestration, Google Gemini, Mistral AI router, and RAG knowledge search.
          </p>
        </div>

        {error && (
          <div style={{ background: "rgba(244, 63, 94, 0.12)", border: "1px solid rgba(244, 63, 94, 0.3)", padding: "1rem 1.25rem", borderRadius: "10px", marginBottom: "1.5rem", color: "#fb7185", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div>
              <strong>⚠️ Review Error:</strong> {error}
              <div style={{ fontSize: "0.8rem", color: "var(--text-secondary)", marginTop: "0.2rem" }}>
                Make sure the FastAPI backend is running on <code>http://localhost:8000</code>.
              </div>
            </div>
            <button className="btn btn-secondary btn-sm" onClick={() => setError(null)}>Dismiss</button>
          </div>
        )}

        <div className="app-grid">
          {/* Left Column: Code Input Workspace */}
          <div>
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
                <div style={{ marginTop: "1.5rem", display: "flex", gap: "0.5rem" }}>
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
                      reviewId={reviewResult.review_id}
                      verdict={reviewResult.verdict}
                      ratingScore={reviewResult.rating_score}
                      executiveSummary={reviewResult.executive_summary}
                      totalFindings={reviewResult.findings?.length || 0}
                      executionTime={reviewResult.execution_time_seconds}
                      reviewMode={reviewResult.review_mode || reviewMode}
                      modelUsed={reviewResult.model_used}
                      languageDetected={reviewResult.language_detected || language}
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
                    languageDetected={reviewResult.language_detected || language}
                    findings={reviewResult.findings || []}
                    onApplyCode={handleApplyRefactoredCode}
                  />
                )}
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
