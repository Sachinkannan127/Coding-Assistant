"use client";

import React, { useState } from "react";
import { Play, RefreshCw, Terminal, CheckCircle2, AlertTriangle, Clock, Copy, Check, X, CornerDownLeft, FlaskConical } from "lucide-react";
import TestCasesModal from "./TestCasesModal";

export interface ExecutionResult {
  stdout: string;
  stderr: string;
  exit_code: number;
  status: "success" | "error" | "timeout";
  execution_time_ms: number;
  language_used: string;
}

interface CodeSandboxProps {
  code: string;
  language: string;
  onExecute: (stdinData?: string) => Promise<void>;
  loading: boolean;
  result: ExecutionResult | null;
  onClear: () => void;
}

export default function CodeSandbox({
  code,
  language,
  onExecute,
  loading,
  result,
  onClear,
}: CodeSandboxProps) {
  const [activeConsoleTab, setActiveConsoleTab] = useState<"stdout" | "stderr" | "stdin">("stdout");
  const [stdinData, setStdinData] = useState<string>("");
  const [copied, setCopied] = useState<boolean>(false);
  const [showTestCasesModal, setShowTestCasesModal] = useState<boolean>(false);

  const handleCopy = (text: string) => {
    if (!text) return;
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const hasOutput = result && (result.stdout || result.stderr || result.status);

  return (
    <div className="card fade-in" style={{ border: "1px solid rgba(168, 85, 247, 0.3)", background: "rgba(15, 23, 42, 0.85)", boxShadow: "0 10px 30px rgba(0, 0, 0, 0.3)" }}>
      {/* Sandbox Terminal Header */}
      <div className="card-header" style={{ paddingBottom: "0.75rem", borderBottom: "1px solid rgba(255, 255, 255, 0.08)" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "0.6rem" }}>
          <div style={{ background: "linear-gradient(135deg, #a855f7, #6366f1)", padding: "0.4rem", borderRadius: "8px", display: "flex", alignItems: "center" }}>
            <Terminal className="w-4 h-4 text-white" />
          </div>
          <div>
            <h3 style={{ fontSize: "1.05rem", fontWeight: 700, margin: 0, display: "flex", alignItems: "center", gap: "0.5rem" }}>
              Code Execution Sandbox Terminal
            </h3>
            <div style={{ fontSize: "0.78rem", color: "var(--text-muted)", marginTop: "2px" }}>
              Isolated Subprocess Runner • {language.toUpperCase()} Engine
            </div>
          </div>
        </div>

        {/* Action Controls */}
        <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
          <button
            type="button"
            className="btn btn-secondary btn-sm"
            onClick={() => setShowTestCasesModal(true)}
            disabled={!code || !code.trim()}
            style={{ fontSize: "0.75rem", padding: "0.35rem 0.65rem", borderColor: "rgba(56, 189, 248, 0.4)", color: "#38bdf8" }}
          >
            <FlaskConical className="w-3.5 h-3.5 mr-1 inline text-cyan-400" /> Test Cases
          </button>

          {result && (
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              onClick={onClear}
              disabled={loading}
              style={{ fontSize: "0.75rem", padding: "0.35rem 0.65rem" }}
            >
              <X className="w-3.5 h-3.5 mr-1" /> Clear
            </button>
          )}

          <button
            type="button"
            className="btn btn-primary btn-sm"
            onClick={() => onExecute(stdinData)}
            disabled={loading || !code || !code.trim()}
            style={{
              background: "linear-gradient(135deg, #a855f7, #6366f1)",
              border: "none",
              padding: "0.45rem 1rem",
              fontSize: "0.82rem",
              fontWeight: 600,
              boxShadow: "0 4px 12px rgba(168, 85, 247, 0.3)"
            }}
          >
            {loading ? (
              <>
                <RefreshCw className="w-3.5 h-3.5 mr-1.5 animate-spin" /> Executing Code...
              </>
            ) : (
              <>
                <Play className="w-3.5 h-3.5 mr-1.5 fill-current" /> Run Code in Sandbox
              </>
            )}
          </button>
        </div>
      </div>

      {/* Execution Metrics Bar */}
      {result && (
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "0.6rem 1rem", background: "rgba(0, 0, 0, 0.3)", borderRadius: "8px", margin: "0.75rem 0", flexWrap: "wrap", gap: "0.5rem", fontSize: "0.8rem" }}>
          <div style={{ display: "flex", gap: "0.75rem", alignItems: "center" }}>
            {/* Status Badge */}
            {result.status === "success" && (
              <span className="badge badge-success" style={{ display: "flex", alignItems: "center", gap: "0.35rem" }}>
                <CheckCircle2 className="w-3.5 h-3.5" /> Executed Cleanly (Exit Code 0)
              </span>
            )}
            {result.status === "error" && (
              <span className="badge badge-danger" style={{ display: "flex", alignItems: "center", gap: "0.35rem" }}>
                <AlertTriangle className="w-3.5 h-3.5" /> Process Error (Exit Code {result.exit_code})
              </span>
            )}
            {result.status === "timeout" && (
              <span className="badge badge-amber" style={{ display: "flex", alignItems: "center", gap: "0.35rem" }}>
                <Clock className="w-3.5 h-3.5" /> Timed Out (&gt; 5s limit)
              </span>
            )}

            <span style={{ color: "var(--text-muted)" }}>•</span>
            <span style={{ color: "var(--accent-cyan)", display: "flex", alignItems: "center", gap: "0.3rem" }}>
              <Clock className="w-3 h-3 text-cyan-400" /> {result.execution_time_ms} ms
            </span>
          </div>

          <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
            <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
              Engine: <code style={{ color: "#a855f7" }}>{result.language_used}</code>
            </span>
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              onClick={() => handleCopy(result.stdout || result.stderr)}
              title="Copy Output"
              style={{ padding: "0.2rem 0.5rem", fontSize: "0.75rem" }}
            >
              {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
            </button>
          </div>
        </div>
      )}

      {/* Terminal View Body */}
      <div style={{ marginTop: "0.5rem" }}>
        {/* Terminal Subtabs */}
        <div style={{ display: "flex", gap: "0.5rem", marginBottom: "0.5rem", borderBottom: "1px solid rgba(255, 255, 255, 0.08)", paddingBottom: "0.35rem" }}>
          <button
            type="button"
            className={`btn btn-sm ${activeConsoleTab === "stdout" ? "btn-primary" : "btn-secondary"}`}
            onClick={() => setActiveConsoleTab("stdout")}
            style={{ fontSize: "0.75rem", padding: "0.25rem 0.65rem" }}
          >
            Standard Output {result?.stdout ? `(${result.stdout.trim().split("\n").length} lines)` : ""}
          </button>
          <button
            type="button"
            className={`btn btn-sm ${activeConsoleTab === "stderr" ? (result?.stderr ? "btn-danger" : "btn-secondary") : "btn-secondary"}`}
            onClick={() => setActiveConsoleTab("stderr")}
            style={{ fontSize: "0.75rem", padding: "0.25rem 0.65rem" }}
          >
            Standard Error {result?.stderr ? `(Alert)` : ""}
          </button>
          <button
            type="button"
            className={`btn btn-sm ${activeConsoleTab === "stdin" ? "btn-primary" : "btn-secondary"}`}
            onClick={() => setActiveConsoleTab("stdin")}
            style={{ fontSize: "0.75rem", padding: "0.25rem 0.65rem" }}
          >
            Standard Input (stdin) {stdinData ? "• Active" : ""}
          </button>
        </div>

        {/* Tab Panes */}
        {activeConsoleTab === "stdout" && (
          <div style={{
            background: "#090d16",
            borderRadius: "8px",
            border: "1px solid rgba(255, 255, 255, 0.1)",
            padding: "1rem",
            minHeight: "160px",
            maxHeight: "320px",
            overflowY: "auto",
            fontFamily: "var(--font-mono, monospace)",
            fontSize: "0.85rem",
            color: "#38bdf8",
            lineHeight: 1.6,
            whiteSpace: "pre-wrap",
            wordBreak: "break-all"
          }}>
            {loading ? (
              <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", color: "var(--text-muted)" }}>
                <span className="spinner-mini"></span> Executing subprocess in temporary workspace environment...
              </div>
            ) : result?.stdout ? (
              result.stdout
            ) : hasOutput ? (
              <span style={{ color: "var(--text-muted)", fontStyle: "italic" }}>(Process produced no stdout text output)</span>
            ) : (
              <div style={{ textAlign: "center", color: "var(--text-muted)", padding: "1.5rem 0" }}>
                <Terminal className="w-8 h-8 mx-auto mb-2 text-slate-600" />
                <div>Console ready. Click <strong>Run Code in Sandbox</strong> to execute your program.</div>
              </div>
            )}
          </div>
        )}

        {activeConsoleTab === "stderr" && (
          <div style={{
            background: "#16090c",
            borderRadius: "8px",
            border: "1px solid rgba(244, 63, 94, 0.2)",
            padding: "1rem",
            minHeight: "160px",
            maxHeight: "320px",
            overflowY: "auto",
            fontFamily: "var(--font-mono, monospace)",
            fontSize: "0.85rem",
            color: "#fb7185",
            lineHeight: 1.6,
            whiteSpace: "pre-wrap",
            wordBreak: "break-all"
          }}>
            {result?.stderr ? (
              result.stderr
            ) : (
              <span style={{ color: "var(--text-muted)" }}>No process errors or warnings reported.</span>
            )}
          </div>
        )}

        {activeConsoleTab === "stdin" && (
          <div style={{ background: "#090d16", padding: "1rem", borderRadius: "8px", border: "1px solid rgba(255, 255, 255, 0.1)" }}>
            <label className="form-label" style={{ fontSize: "0.8rem", color: "var(--text-secondary)", marginBottom: "0.4rem", display: "flex", alignItems: "center", gap: "0.4rem" }}>
              <CornerDownLeft className="w-3.5 h-3.5 text-purple-400" /> Stdin Input Stream Payload (Optional):
            </label>
            <textarea
              className="select-input"
              rows={4}
              placeholder="Enter input values (one per line) to pass to process stdin..."
              value={stdinData}
              onChange={(e) => setStdinData(e.target.value)}
              style={{ width: "100%", fontFamily: "monospace", fontSize: "0.85rem", background: "#0f172a", border: "1px solid var(--border-subtle)" }}
            />
            <div style={{ fontSize: "0.72rem", color: "var(--text-muted)", marginTop: "0.4rem" }}>
              Input entered here will be written to stdin when <strong>Run Code in Sandbox</strong> is clicked.
            </div>
          </div>
        )}
      </div>

      <TestCasesModal
        isOpen={showTestCasesModal}
        onClose={() => setShowTestCasesModal(false)}
        code={code}
        language={language}
      />
    </div>
  );
}
