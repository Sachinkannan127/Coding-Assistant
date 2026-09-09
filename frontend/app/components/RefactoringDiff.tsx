"use client";

import React, { useState } from "react";

interface RefactoringDiffProps {
  originalCode: string;
  refactoredCode?: string;
  refactoringExplanation?: string;
  astValidated?: boolean;
}

export default function RefactoringDiff({
  originalCode,
  refactoredCode,
  refactoringExplanation,
  astValidated = true,
}: RefactoringDiffProps) {
  const [copied, setCopied] = useState(false);

  if (!refactoredCode) {
    return (
      <div className="card fade-in">
        <div className="card-header">
          <div className="card-title">
            <span>🛠️</span> Automated Code Refactoring Engine
          </div>
        </div>
        <div style={{ padding: "2rem", textAlign: "center", background: "rgba(10, 14, 23, 0.5)", borderRadius: "10px", border: "1px solid var(--border-subtle)" }}>
          <div style={{ fontSize: "2rem", marginBottom: "0.5rem" }}>⚡</div>
          <div style={{ fontWeight: 600, color: "var(--text-primary)" }}>No Refactored Code Generated</div>
          <div style={{ fontSize: "0.825rem", color: "var(--text-muted)", marginTop: "0.25rem" }}>
            Run in <strong>Deep Review Mode</strong> to trigger AST-validated AI refactoring.
          </div>
        </div>
      </div>
    );
  }

  const handleCopy = () => {
    navigator.clipboard.writeText(refactoredCode);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  return (
    <div className="card fade-in">
      <div className="card-header">
        <div className="card-title">
          <span>🛠️</span> Refactored Code & AST Validation Diff
        </div>
        <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
          {astValidated ? (
            <span className="badge badge-success">
              ✅ AST Syntax Validated
            </span>
          ) : (
            <span className="badge badge-amber">
              ⚠️ Syntax Validation Bypassed
            </span>
          )}
          <button
            type="button"
            className="btn btn-primary btn-sm"
            onClick={handleCopy}
          >
            {copied ? "✓ Copied Code!" : "📋 Copy Refactored Code"}
          </button>
        </div>
      </div>

      {refactoringExplanation && (
        <div style={{ background: "rgba(16, 185, 129, 0.08)", border: "1px solid rgba(16, 185, 129, 0.25)", padding: "1rem", borderRadius: "10px", marginBottom: "1.25rem" }}>
          <div style={{ fontSize: "0.75rem", fontWeight: 700, color: "var(--accent-emerald)", textTransform: "uppercase", marginBottom: "0.35rem" }}>
            Refactoring Rationale
          </div>
          <div style={{ fontSize: "0.875rem", color: "var(--text-primary)", lineHeight: 1.6 }}>
            {refactoringExplanation}
          </div>
        </div>
      )}

      <div className="diff-container">
        <div className="diff-pane diff-pane-original">
          <div className="diff-pane-title">❌ Original Code (Submitted)</div>
          <pre style={{ margin: 0, whiteSpace: "pre-wrap", wordBreak: "break-all" }}>
            {originalCode}
          </pre>
        </div>

        <div className="diff-pane diff-pane-refactored">
          <div className="diff-pane-title">✅ Refactored & Optimized Code</div>
          <pre style={{ margin: 0, whiteSpace: "pre-wrap", wordBreak: "break-all" }}>
            {refactoredCode}
          </pre>
        </div>
      </div>
    </div>
  );
}
