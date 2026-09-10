"use client";

import React, { useState, useMemo } from "react";
import { computeLineDiff } from "./DiffUtils";
import { Finding } from "./FindingsExplorer";

interface RefactoringDiffProps {
  originalCode: string;
  refactoredCode?: string;
  refactoringExplanation?: string;
  astValidated?: boolean;
  languageDetected?: string;
  findings?: Finding[];
  onApplyCode?: (code: string) => void;
  onTestRefactoredCode?: (code: string) => void;
}

export default function RefactoringDiff({
  originalCode,
  refactoredCode,
  refactoringExplanation,
  astValidated = true,
  languageDetected = "python",
  findings = [],
  onApplyCode,
  onTestRefactoredCode,
}: RefactoringDiffProps) {
  const [viewMode, setViewMode] = useState<"split" | "unified">("split");
  const [copied, setCopied] = useState(false);
  const [applied, setApplied] = useState(false);

  // Compute line diff
  const diffResult = useMemo(() => {
    if (!refactoredCode) return null;
    return computeLineDiff(originalCode, refactoredCode);
  }, [originalCode, refactoredCode]);

  // Set of original line numbers associated with findings
  const findingLineNumbers = useMemo(() => {
    const lines = new Set<number>();
    findings.forEach((f) => {
      if (f.line_numbers) {
        f.line_numbers.forEach((ln) => lines.add(ln));
      }
    });
    return lines;
  }, [findings]);

  if (!refactoredCode) {
    return (
      <div className="card fade-in">
        <div className="card-header">
          <div className="card-title">
            <span>🛠️</span> Automated Code Refactoring Engine
          </div>
        </div>
        <div style={{ padding: "2.5rem", textAlign: "center", background: "rgba(10, 14, 23, 0.5)", borderRadius: "10px", border: "1px solid var(--border-subtle)" }}>
          <div style={{ fontSize: "2.5rem", marginBottom: "0.5rem" }}>⚡</div>
          <div style={{ fontWeight: 600, color: "var(--text-primary)" }}>No Refactored Code Available</div>
          <div style={{ fontSize: "0.825rem", color: "var(--text-muted)", marginTop: "0.35rem" }}>
            Run in <strong>Deep Review Mode</strong> to trigger AST-validated multi-pass AI refactoring.
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

  const handleApply = () => {
    if (onApplyCode && refactoredCode) {
      onApplyCode(refactoredCode);
      setApplied(true);
      setTimeout(() => setApplied(false), 2500);
    }
  };

  const handleDownload = () => {
    const extMap: Record<string, string> = {
      python: "py",
      javascript: "js",
      typescript: "ts",
      react: "jsx",
      nextjs: "tsx",
      c: "c",
      cpp: "cpp",
      java: "java",
      go: "go",
      rust: "rs",
      django: "py",
    };
    const ext = extMap[languageDetected.toLowerCase()] || "txt";
    const filename = `refactored_code.${ext}`;

    const blob = new Blob([refactoredCode], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="card fade-in">
      {/* Header & Controls */}
      <div className="card-header" style={{ flexWrap: "wrap", gap: "0.75rem" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
          <div className="card-title">
            <span>🛠️</span> Code Refactoring & Line Comparison
          </div>
          {astValidated ? (
            <span className="badge badge-success" style={{ fontSize: "0.7rem" }}>
              ✅ AST Validated
            </span>
          ) : (
            <span className="badge badge-amber" style={{ fontSize: "0.7rem" }}>
              ⚠️ Validation Bypassed
            </span>
          )}
        </div>

        {/* View Mode Toggle & Action Buttons */}
        <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap", alignItems: "center" }}>
          <div style={{ display: "flex", background: "var(--bg-input)", padding: "2px", borderRadius: "6px", border: "1px solid var(--border-subtle)" }}>
            <button
              type="button"
              className={`btn btn-sm ${viewMode === "split" ? "btn-primary" : "btn-secondary"}`}
              style={{ padding: "0.25rem 0.6rem", fontSize: "0.75rem" }}
              onClick={() => setViewMode("split")}
            >
              Split View
            </button>
            <button
              type="button"
              className={`btn btn-sm ${viewMode === "unified" ? "btn-primary" : "btn-secondary"}`}
              style={{ padding: "0.25rem 0.6rem", fontSize: "0.75rem" }}
              onClick={() => setViewMode("unified")}
            >
              Unified View
            </button>
          </div>

          <button
            type="button"
            className="btn btn-secondary btn-sm"
            style={{ fontSize: "0.75rem" }}
            onClick={handleDownload}
          >
            📥 Download
          </button>

          <button
            type="button"
            className="btn btn-secondary btn-sm"
            style={{ fontSize: "0.75rem" }}
            onClick={handleCopy}
          >
            {copied ? "✓ Copied!" : "📋 Copy"}
          </button>

          {onTestRefactoredCode && refactoredCode && (
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              style={{ fontSize: "0.75rem", borderColor: "rgba(168, 85, 247, 0.5)", color: "#c084fc" }}
              onClick={() => onTestRefactoredCode(refactoredCode)}
            >
              ▶ Test in Sandbox
            </button>
          )}

          {onApplyCode && (
            <button
              type="button"
              className="btn btn-primary btn-sm"
              style={{ fontSize: "0.75rem" }}
              onClick={handleApply}
            >
              {applied ? "✓ Applied to Editor!" : "🚀 Apply to Editor"}
            </button>
          )}
        </div>
      </div>

      {/* Diff Statistics Bar */}
      {diffResult && (
        <div style={{ display: "flex", gap: "1rem", marginBottom: "1rem", background: "rgba(10, 14, 23, 0.6)", padding: "0.6rem 1rem", borderRadius: "8px", border: "1px solid var(--border-subtle)", fontSize: "0.78rem" }}>
          <span style={{ color: "var(--accent-emerald)", fontWeight: 700 }}>
            +{diffResult.stats.additions} Additions
          </span>
          <span style={{ color: "var(--accent-rose)", fontWeight: 700 }}>
            -{diffResult.stats.deletions} Deletions
          </span>
          <span style={{ color: "var(--text-muted)" }}>
            {diffResult.stats.unchanged} Lines Unchanged
          </span>
          {findingLineNumbers.size > 0 && (
            <span style={{ color: "var(--accent-amber)", fontWeight: 600, marginLeft: "auto" }}>
              ⚠️ {findingLineNumbers.size} Line(s) directly linked to findings
            </span>
          )}
        </div>
      )}

      {/* Explanation Banner */}
      {refactoringExplanation && (
        <div style={{ background: "rgba(16, 185, 129, 0.08)", border: "1px solid rgba(16, 185, 129, 0.25)", padding: "0.875rem 1rem", borderRadius: "8px", marginBottom: "1.25rem" }}>
          <div style={{ fontSize: "0.75rem", fontWeight: 700, color: "var(--accent-emerald)", textTransform: "uppercase", marginBottom: "0.25rem" }}>
            Refactoring Rationale
          </div>
          <div style={{ fontSize: "0.85rem", color: "var(--text-primary)", lineHeight: 1.5 }}>
            {refactoringExplanation}
          </div>
        </div>
      )}

      {/* Split (Side-by-Side) View */}
      {viewMode === "split" && (
        <div className="diff-container">
          <div className="diff-pane diff-pane-original">
            <div className="diff-pane-title">❌ Original Code (Submitted)</div>
            <div style={{ display: "flex", flexDirection: "column" }}>
              {originalCode.split("\n").map((line, idx) => {
                const lineNum = idx + 1;
                const hasFinding = findingLineNumbers.has(lineNum);
                return (
                  <div key={idx} className={`diff-line-row ${hasFinding ? "deleted" : "unchanged"}`}>
                    <span className="diff-line-num">
                      {hasFinding && <span className="finding-marker-badge">!</span>}
                      {lineNum}
                    </span>
                    <span className="diff-line-content">{line || " "}</span>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="diff-pane diff-pane-refactored">
            <div className="diff-pane-title">✅ Refactored & Optimized Code</div>
            <div style={{ display: "flex", flexDirection: "column" }}>
              {refactoredCode.split("\n").map((line, idx) => {
                const lineNum = idx + 1;
                return (
                  <div key={idx} className="diff-line-row added">
                    <span className="diff-line-num">{lineNum}</span>
                    <span className="diff-line-content">{line || " "}</span>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* Unified (Inline) View */}
      {viewMode === "unified" && diffResult && (
        <div className="diff-unified-container">
          <div style={{ padding: "0.75rem 1rem", borderBottom: "1px solid var(--border-subtle)", fontSize: "0.75rem", fontWeight: 700, color: "var(--accent-cyan)", textTransform: "uppercase" }}>
            Unified Inline Diff Stream
          </div>
          <div style={{ padding: "0.5rem 0" }}>
            {diffResult.lines.map((line, idx) => {
              const hasFinding = line.originalLineNumber && findingLineNumbers.has(line.originalLineNumber);
              return (
                <div key={idx} className={`diff-line-row ${line.type}`}>
                  <span className="diff-line-num">
                    {hasFinding && <span className="finding-marker-badge">!</span>}
                    {line.originalLineNumber ?? " "}
                  </span>
                  <span className="diff-line-num">{line.refactoredLineNumber ?? " "}</span>
                  <span className={`diff-line-prefix ${line.type}`}>
                    {line.type === "added" ? "+" : line.type === "deleted" ? "-" : " "}
                  </span>
                  <span className="diff-line-content">{line.content || " "}</span>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
