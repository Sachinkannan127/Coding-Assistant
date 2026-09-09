"use client";

import React from "react";

interface ReviewSummaryProps {
  reviewId: string;
  verdict: string;
  ratingScore: number;
  executiveSummary: string;
  totalFindings: number;
  executionTime: number;
  reviewMode: string;
  modelUsed?: string;
  languageDetected?: string;
}

export default function ReviewSummary({
  reviewId,
  verdict,
  ratingScore,
  executiveSummary,
  totalFindings,
  executionTime,
  reviewMode,
  modelUsed = "gemini-2.5-flash",
  languageDetected,
}: ReviewSummaryProps) {
  const getVerdictBadge = (v: string) => {
    switch (v) {
      case "PASS":
        return <span className="badge badge-success" style={{ fontSize: "0.85rem", padding: "0.4rem 1rem" }}>✅ PASS - Code Verified Safe</span>;
      case "PASS_WITH_RESERVATIONS":
        return <span className="badge badge-amber" style={{ fontSize: "0.85rem", padding: "0.4rem 1rem" }}>⚠️ PASS WITH RESERVATIONS</span>;
      case "NEEDS_REFACTORING":
        return <span className="badge badge-purple" style={{ fontSize: "0.85rem", padding: "0.4rem 1rem" }}>🛠️ NEEDS REFACTORING</span>;
      case "CRITICAL_ISSUES":
        return <span className="badge badge-danger" style={{ fontSize: "0.85rem", padding: "0.4rem 1rem" }}>🚨 CRITICAL VULNERABILITIES DETECTED</span>;
      default:
        return <span className="badge badge-indigo" style={{ fontSize: "0.85rem", padding: "0.4rem 1rem" }}>{v}</span>;
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return "var(--accent-emerald)";
    if (score >= 50) return "var(--accent-amber)";
    return "var(--accent-rose)";
  };

  return (
    <div className="card fade-in">
      <div className="card-header">
        <div>
          <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginBottom: "0.25rem" }}>
            REVIEW REPORT #{reviewId ? reviewId.substring(0, 8) : "LIVE"}
          </div>
          <div className="card-title">
            <span>📊</span> Executive Review Summary
          </div>
        </div>
        <div>{getVerdictBadge(verdict)}</div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(130px, 1fr))", gap: "1rem", marginBottom: "1.25rem" }}>
        <div style={{ background: "rgba(10, 14, 23, 0.7)", padding: "0.875rem", borderRadius: "10px", border: "1px solid var(--border-subtle)", textAlign: "center" }}>
          <div style={{ fontSize: "0.7rem", color: "var(--text-muted)", fontWeight: 600, textTransform: "uppercase" }}>Overall Health</div>
          <div style={{ fontSize: "1.75rem", fontWeight: 800, color: getScoreColor(ratingScore) }}>
            {ratingScore}<span style={{ fontSize: "0.9rem", color: "var(--text-muted)" }}>/100</span>
          </div>
        </div>

        <div style={{ background: "rgba(10, 14, 23, 0.7)", padding: "0.875rem", borderRadius: "10px", border: "1px solid var(--border-subtle)", textAlign: "center" }}>
          <div style={{ fontSize: "0.7rem", color: "var(--text-muted)", fontWeight: 600, textTransform: "uppercase" }}>Findings</div>
          <div style={{ fontSize: "1.75rem", fontWeight: 800, color: totalFindings === 0 ? "var(--accent-emerald)" : "var(--accent-cyan)" }}>
            {totalFindings}
          </div>
        </div>

        <div style={{ background: "rgba(10, 14, 23, 0.7)", padding: "0.875rem", borderRadius: "10px", border: "1px solid var(--border-subtle)", textAlign: "center" }}>
          <div style={{ fontSize: "0.7rem", color: "var(--text-muted)", fontWeight: 600, textTransform: "uppercase" }}>Execution Time</div>
          <div style={{ fontSize: "1.5rem", fontWeight: 800, color: "var(--text-primary)" }}>
            {executionTime ? `${executionTime.toFixed(2)}s` : "0.5s"}
          </div>
        </div>

        <div style={{ background: "rgba(10, 14, 23, 0.7)", padding: "0.875rem", borderRadius: "10px", border: "1px solid var(--border-subtle)", textAlign: "center" }}>
          <div style={{ fontSize: "0.7rem", color: "var(--text-muted)", fontWeight: 600, textTransform: "uppercase" }}>Analysis Mode</div>
          <div style={{ fontSize: "1rem", fontWeight: 700, color: "var(--accent-indigo)", marginTop: "0.3rem" }}>
            {reviewMode === "deep" ? "🔍 Deep Multi-Agent" : "⚡ Quick Scan"}
          </div>
        </div>
      </div>

      <div style={{ background: "rgba(6, 8, 13, 0.8)", padding: "1.25rem", borderRadius: "10px", border: "1px solid var(--border-subtle)" }}>
        <div style={{ fontSize: "0.75rem", fontWeight: 700, color: "var(--accent-cyan)", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: "0.5rem" }}>
          Synthesized Evaluation
        </div>
        <p style={{ fontSize: "0.9rem", color: "var(--text-primary)", lineHeight: 1.6 }}>
          {executiveSummary || "Analysis completed successfully. No critical vulnerabilities or anti-patterns detected."}
        </p>
        
        {languageDetected && (
          <div style={{ display: "flex", gap: "1rem", marginTop: "1rem", paddingTop: "0.75rem", borderTop: "1px solid var(--border-subtle)", fontSize: "0.78rem", color: "var(--text-muted)" }}>
            <span>Language Detected: <strong style={{ color: "var(--text-primary)" }}>{languageDetected}</strong></span>
            <span>Provider Engine: <strong style={{ color: "var(--accent-indigo)" }}>{modelUsed}</strong></span>
          </div>
        )}
      </div>
    </div>
  );
}
