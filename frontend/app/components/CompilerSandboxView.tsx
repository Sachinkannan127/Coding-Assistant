"use client";

import React, { useState, useMemo } from "react";
import { Terminal, Play, RefreshCw, X, Copy, Check, Download, CornerDownLeft, Sparkles, Code, Cpu, ShieldCheck, Zap, Lightbulb, FlaskConical } from "lucide-react";
import { ExecutionResult } from "./CodeSandbox";
import CodeExplanationModal from "./CodeExplanationModal";
import TestCasesModal from "./TestCasesModal";

interface CompilerSandboxViewProps {
  onSwitchView: (view: "landing" | "studio" | "compiler") => void;
}

const COMPILER_PRESETS = [
  {
    name: "Python: Fibonacci & Performance Benchmark",
    language: "python",
    code: `import time

def fibonacci(n):
    if n <= 1:
        return n
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b

print("CodePilot AI Python Execution Engine")
start = time.perf_counter()
n = 35
result = fibonacci(n)
elapsed = (time.perf_counter() - start) * 1000

print(f"Fibonacci({n}) = {result:,}")
print(f"Benchmark Execution Time: {elapsed:.3f} ms")
`
  },
  {
    name: "JavaScript: Data Processing & Algorithms",
    language: "javascript",
    code: `// Array transformation & filtering benchmark
const users = [
  { id: 1, name: "Alice", role: "Admin", score: 92 },
  { id: 2, name: "Bob", role: "Developer", score: 85 },
  { id: 3, name: "Charlie", role: "Designer", score: 78 },
  { id: 4, name: "Diana", role: "Lead Developer", score: 96 }
];

console.log("⚡ Executing JavaScript Sandbox Engine...");
const highScorers = users
  .filter(u => u.score >= 85)
  .map(u => ({ ...u, status: "Verified" }));

console.table(highScorers);
console.log("Total High Performers:", highScorers.length);
`
  },
  {
    name: "C Language: Pointer Math & Structs",
    language: "c",
    code: `#include <stdio.h>
#include <string.h>

typedef struct {
    int id;
    char name[32];
    double score;
} Student;

int main() {
    printf("⚡ CodePilot C Subprocess Compiler Engine\\n");
    Student s1 = {101, "Alex Mercer", 98.5};
    
    printf("Student ID: %d\\n", s1.id);
    printf("Name: %s\\n", s1.name);
    printf("Score: %.2f\\n", s1.score);
    
    return 0;
}
`
  },
  {
    name: "TypeScript: Type Safety & Objects",
    language: "typescript",
    code: `interface BenchmarkResult {
    testName: string;
    iterations: number;
    passed: boolean;
}

const runTest = (name: string, count: number): BenchmarkResult => {
    return { testName: name, iterations: count, passed: count > 0 };
};

console.log("🚀 CodePilot TypeScript Sandbox");
const res = runTest("AST Syntax Validation", 5000);
console.log("Test Result:", JSON.stringify(res, null, 2));
`
  }
];

export default function CompilerSandboxView({ onSwitchView }: CompilerSandboxViewProps) {
  const [code, setCode] = useState<string>(COMPILER_PRESETS[0].code);
  const [language, setLanguage] = useState<string>("python");
  const [stdinData, setStdinData] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<ExecutionResult | null>(null);
  const [activeConsoleTab, setActiveConsoleTab] = useState<"stdout" | "stderr" | "stdin" | "metrics">("stdout");
  const [copied, setCopied] = useState<boolean>(false);
  const [showExplanationModal, setShowExplanationModal] = useState<boolean>(false);
  const [showTestCasesModal, setShowTestCasesModal] = useState<boolean>(false);

  const lineCount = useMemo(() => {
    if (!code) return 1;
    return code.split("\n").length;
  }, [code]);

  const lineNumbers = useMemo(() => {
    return Array.from({ length: Math.max(lineCount, 14) }, (_, i) => i + 1);
  }, [lineCount]);

  const handleExecute = async () => {
    if (!code || !code.trim()) return;

    setLoading(true);
    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8005";
      const response = await fetch(`${baseUrl}/api/sandbox/execute`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          code: code,
          language: language,
          stdin_data: stdinData,
          timeout_seconds: 5
        })
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.detail || `Server error ${response.status}`);
      }

      const data: ExecutionResult = await response.json();
      setResult(data);
    } catch (err: any) {
      setResult({
        stdout: "",
        stderr: `Compiler Execution Error: ${err.message || "Failed to communicate with sandbox engine."}`,
        exit_code: 1,
        status: "error",
        execution_time_ms: 0,
        language_used: language
      });
    } finally {
      setLoading(false);
    }
  };

  const loadPreset = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const idx = parseInt(e.target.value, 10);
    if (isNaN(idx)) return;
    const preset = COMPILER_PRESETS[idx];
    if (preset) {
      setCode(preset.code);
      setLanguage(preset.language);
    }
  };

  const handleCopyOutput = () => {
    if (!result) return;
    const text = result.stdout || result.stderr;
    if (!text) return;
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownloadOutput = () => {
    if (!result) return;
    const text = result.stdout || result.stderr || "No output";
    const blob = new Blob([text], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `compiler_output.txt`;
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <main className="container fade-in" style={{ paddingTop: "2rem" }}>
      {/* Compiler Header Bar */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1.5rem", flexWrap: "wrap", gap: "1rem" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", marginBottom: "0.4rem" }}>
            <span className="badge badge-purple" style={{ fontSize: "0.8rem", padding: "0.3rem 0.75rem" }}>
              <Terminal className="w-3.5 h-3.5 mr-1 inline text-purple-400" /> Interactive Compiler Sandbox
            </span>
            <h1 style={{ fontSize: "1.75rem", fontWeight: 800, letterSpacing: "-0.02em" }}>
              Online Code Execution Playground
            </h1>
          </div>
          <p style={{ color: "var(--text-secondary)", fontSize: "0.9rem" }}>
            Instant isolated subprocess execution, stdin stream support, runtime performance timing, and multi-language compilers.
          </p>
        </div>

        <div style={{ display: "flex", gap: "0.75rem", alignItems: "center" }}>
          <button
            type="button"
            className="btn btn-secondary"
            onClick={() => onSwitchView("studio")}
            style={{ fontSize: "0.85rem", padding: "0.5rem 1rem" }}
          >
            <Sparkles className="w-4 h-4 mr-1.5 inline text-indigo-400" /> Switch to AI Review Studio
          </button>
        </div>
      </div>

      {/* Main Sandbox Grid: 50% Editor / 50% Terminal */}
      <div className="app-grid" style={{ gridTemplateColumns: "1fr 1fr", gap: "1.5rem" }}>
        
        {/* Left Column: Code Editor */}
        <div className="card" style={{ display: "flex", flexDirection: "column" }}>
          {/* Header Controls */}
          <div className="card-header" style={{ flexWrap: "wrap", gap: "0.75rem" }}>
            <div className="card-title">
              <Code className="w-5 h-5 text-indigo-400 mr-1.5" /> Source Code Editor
            </div>

            <div style={{ display: "flex", gap: "0.5rem", alignItems: "center", flexWrap: "wrap" }}>
              <select
                className="select-input"
                onChange={loadPreset}
                defaultValue=""
                style={{ fontSize: "0.78rem", padding: "0.35rem 0.65rem", maxWidth: "200px" }}
              >
                <option value="" disabled>Load Sample Code...</option>
                {COMPILER_PRESETS.map((p, i) => (
                  <option key={i} value={i}>{p.name}</option>
                ))}
              </select>

              <select
                className="select-input"
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                style={{ fontSize: "0.78rem", padding: "0.35rem 0.65rem" }}
              >
                <option value="python">Python 3</option>
                <option value="javascript">JavaScript (Node)</option>
                <option value="typescript">TypeScript</option>
                <option value="c">C</option>
                <option value="cpp">C++</option>
                <option value="java">Java</option>
                <option value="go">Go</option>
                <option value="rust">Rust</option>
              </select>
            </div>
          </div>

          {/* Editor Body */}
          <div className="editor-container" style={{ flex: 1, display: "flex", flexDirection: "column" }}>
            <div className="editor-toolbar">
              <div style={{ display: "flex", gap: "0.5rem", alignItems: "center", fontSize: "0.75rem", color: "var(--text-muted)" }}>
                <span style={{ color: "var(--accent-cyan)", fontWeight: 600 }}>{language.toUpperCase()}</span>
                <span>•</span>
                <span>{lineCount} lines</span>
                <span>•</span>
                <span>{code.length.toLocaleString()} chars</span>
              </div>
              <button
                type="button"
                className="btn btn-secondary btn-sm"
                onClick={() => setCode("")}
                style={{ fontSize: "0.72rem", padding: "0.2rem 0.5rem" }}
              >
                Clear
              </button>
            </div>

            <div className="editor-body" style={{ flex: 1, minHeight: "380px" }}>
              <div className="line-numbers">
                {lineNumbers.map((num) => (
                  <div key={num}>{num}</div>
                ))}
              </div>
              <textarea
                className="code-textarea"
                placeholder="// Write or paste code snippet here..."
                value={code}
                onChange={(e) => setCode(e.target.value)}
                spellCheck={false}
                style={{ minHeight: "380px", height: "100%" }}
              />
            </div>
          </div>

          {/* Footer Actions */}
          <div style={{ marginTop: "1rem", display: "flex", justifyContent: "flex-end", gap: "0.75rem", flexWrap: "wrap" }}>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => setShowExplanationModal(true)}
              disabled={!code.trim()}
              style={{ fontSize: "0.9rem", padding: "0.85rem 1.25rem", borderColor: "rgba(168, 85, 247, 0.4)", color: "#c084fc" }}
            >
              <Lightbulb className="w-4 h-4 mr-1.5 inline text-amber-400" />
              Explain Code (Simple English)
            </button>

            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => setShowTestCasesModal(true)}
              disabled={!code.trim()}
              style={{ fontSize: "0.9rem", padding: "0.85rem 1.25rem", borderColor: "rgba(56, 189, 248, 0.4)", color: "#38bdf8" }}
            >
              <FlaskConical className="w-4 h-4 mr-1.5 inline text-cyan-400" />
              🧪 Run Test Cases
            </button>

            <button
              type="button"
              className="btn btn-primary"
              onClick={handleExecute}
              disabled={loading || !code.trim()}
              style={{
                padding: "0.85rem 2.25rem",
                fontSize: "0.95rem",
                background: "linear-gradient(135deg, #a855f7, #6366f1)",
                border: "none",
                boxShadow: "0 4px 14px rgba(168, 85, 247, 0.4)"
              }}
            >
              {loading ? (
                <>
                  <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                  <span>Compiling & Executing...</span>
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 mr-2 fill-current" />
                  <span>▶ Execute Code in Sandbox</span>
                </>
              )}
            </button>
          </div>
        </div>

        <CodeExplanationModal
          isOpen={showExplanationModal}
          onClose={() => setShowExplanationModal(false)}
          code={code}
          language={language}
        />

        <TestCasesModal
          isOpen={showTestCasesModal}
          onClose={() => setShowTestCasesModal(false)}
          code={code}
          language={language}
        />

        {/* Right Column: Live Terminal Output */}
        <div className="card" style={{ display: "flex", flexDirection: "column", background: "rgba(10, 15, 26, 0.9)", border: "1px solid rgba(168, 85, 247, 0.25)" }}>
          {/* Header */}
          <div className="card-header" style={{ flexWrap: "wrap", gap: "0.5rem" }}>
            <div className="card-title" style={{ fontSize: "1rem" }}>
              <Terminal className="w-4 h-4 text-purple-400 mr-1.5" /> Compiler Terminal Console
            </div>

            {result && (
              <div style={{ display: "flex", gap: "0.4rem", alignItems: "center" }}>
                <button
                  type="button"
                  className="btn btn-secondary btn-sm"
                  onClick={handleCopyOutput}
                  title="Copy Output"
                  style={{ fontSize: "0.72rem", padding: "0.25rem 0.5rem" }}
                >
                  {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                </button>
                <button
                  type="button"
                  className="btn btn-secondary btn-sm"
                  onClick={handleDownloadOutput}
                  title="Download Output"
                  style={{ fontSize: "0.72rem", padding: "0.25rem 0.5rem" }}
                >
                  <Download className="w-3 h-3" />
                </button>
                <button
                  type="button"
                  className="btn btn-secondary btn-sm"
                  onClick={() => setResult(null)}
                  title="Clear Console"
                  style={{ fontSize: "0.72rem", padding: "0.25rem 0.5rem" }}
                >
                  <X className="w-3 h-3" />
                </button>
              </div>
            )}
          </div>

          {/* Result Status Bar */}
          {result && (
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "0.5rem 0.85rem", background: "rgba(0, 0, 0, 0.4)", borderRadius: "6px", marginBottom: "0.75rem", fontSize: "0.78rem" }}>
              <div style={{ display: "flex", gap: "0.6rem", alignItems: "center" }}>
                {result.status === "success" && (
                  <span className="badge badge-success" style={{ fontSize: "0.7rem" }}>
                    ✓ Clean Execution (Exit Code 0)
                  </span>
                )}
                {result.status === "error" && (
                  <span className="badge badge-danger" style={{ fontSize: "0.7rem" }}>
                    ⚠️ Process Error (Exit Code {result.exit_code})
                  </span>
                )}
                {result.status === "timeout" && (
                  <span className="badge badge-amber" style={{ fontSize: "0.7rem" }}>
                    ⏱️ Execution Timed Out (&gt; 5s limit)
                  </span>
                )}
                <span style={{ color: "var(--accent-cyan)", fontWeight: 600 }}>
                  ⚡ {result.execution_time_ms} ms
                </span>
              </div>
              <div style={{ color: "var(--text-muted)", fontSize: "0.72rem" }}>
                Engine: <code style={{ color: "#c084fc" }}>{result.language_used}</code>
              </div>
            </div>
          )}

          {/* Subtabs Bar */}
          <div style={{ display: "flex", gap: "0.4rem", marginBottom: "0.75rem", borderBottom: "1px solid rgba(255, 255, 255, 0.08)", paddingBottom: "0.4rem" }}>
            <button
              type="button"
              className={`btn btn-sm ${activeConsoleTab === "stdout" ? "btn-primary" : "btn-secondary"}`}
              onClick={() => setActiveConsoleTab("stdout")}
              style={{ fontSize: "0.75rem", padding: "0.25rem 0.6rem" }}
            >
              Output (stdout)
            </button>
            <button
              type="button"
              className={`btn btn-sm ${activeConsoleTab === "stderr" ? (result?.stderr ? "btn-danger" : "btn-secondary") : "btn-secondary"}`}
              onClick={() => setActiveConsoleTab("stderr")}
              style={{ fontSize: "0.75rem", padding: "0.25rem 0.6rem" }}
            >
              Errors (stderr) {result?.stderr ? "!" : ""}
            </button>
            <button
              type="button"
              className={`btn btn-sm ${activeConsoleTab === "stdin" ? "btn-primary" : "btn-secondary"}`}
              onClick={() => setActiveConsoleTab("stdin")}
              style={{ fontSize: "0.75rem", padding: "0.25rem 0.6rem" }}
            >
              Input Stream (stdin) {stdinData ? "• Active" : ""}
            </button>
            <button
              type="button"
              className={`btn btn-sm ${activeConsoleTab === "metrics" ? "btn-primary" : "btn-secondary"}`}
              onClick={() => setActiveConsoleTab("metrics")}
              style={{ fontSize: "0.75rem", padding: "0.25rem 0.6rem" }}
            >
              Metrics
            </button>
          </div>

          {/* Console Output Terminal */}
          <div style={{ flex: 1, display: "flex", flexDirection: "column" }}>
            {activeConsoleTab === "stdout" && (
              <div style={{
                flex: 1,
                background: "#080c14",
                borderRadius: "8px",
                border: "1px solid rgba(255, 255, 255, 0.1)",
                padding: "1rem",
                minHeight: "350px",
                fontFamily: "var(--font-mono, monospace)",
                fontSize: "0.85rem",
                color: "#38bdf8",
                lineHeight: 1.6,
                whiteSpace: "pre-wrap",
                wordBreak: "break-all",
                overflowY: "auto"
              }}>
                {loading ? (
                  <div style={{ display: "flex", alignItems: "center", gap: "0.6rem", color: "var(--text-muted)", padding: "2rem 0", justifyContent: "center" }}>
                    <span className="spinner"></span> Running code inside isolated subprocess sandbox...
                  </div>
                ) : result?.stdout ? (
                  result.stdout
                ) : result ? (
                  <span style={{ color: "var(--text-muted)", fontStyle: "italic" }}>(Process completed with no stdout text output)</span>
                ) : (
                  <div style={{ textAlign: "center", color: "var(--text-muted)", padding: "3rem 1rem" }}>
                    <Terminal className="w-10 h-10 mx-auto mb-3 text-slate-600" />
                    <div style={{ fontSize: "0.95rem", fontWeight: 600, color: "var(--text-primary)", marginBottom: "0.25rem" }}>
                      Compiler Terminal Ready
                    </div>
                    <div style={{ fontSize: "0.8rem" }}>
                      Write or paste your code snippet, select runtime language, and click <strong>▶ Execute Code in Sandbox</strong>.
                    </div>
                  </div>
                )}
              </div>
            )}

            {activeConsoleTab === "stderr" && (
              <div style={{
                flex: 1,
                background: "#16090c",
                borderRadius: "8px",
                border: "1px solid rgba(244, 63, 94, 0.25)",
                padding: "1rem",
                minHeight: "350px",
                fontFamily: "var(--font-mono, monospace)",
                fontSize: "0.85rem",
                color: "#fb7185",
                lineHeight: 1.6,
                whiteSpace: "pre-wrap",
                wordBreak: "break-all",
                overflowY: "auto"
              }}>
                {result?.stderr ? (
                  result.stderr
                ) : (
                  <span style={{ color: "var(--text-muted)" }}>No process errors or warnings reported.</span>
                )}
              </div>
            )}

            {activeConsoleTab === "stdin" && (
              <div style={{ flex: 1, background: "#080c14", padding: "1rem", borderRadius: "8px", border: "1px solid rgba(255, 255, 255, 0.1)", display: "flex", flexDirection: "column" }}>
                <label className="form-label" style={{ fontSize: "0.8rem", color: "var(--text-secondary)", marginBottom: "0.5rem", display: "flex", alignItems: "center", gap: "0.4rem" }}>
                  <CornerDownLeft className="w-3.5 h-3.5 text-purple-400" /> Standard Input Payload (stdin):
                </label>
                <textarea
                  className="select-input"
                  rows={8}
                  placeholder="Enter inputs (one per line) to pass to process stdin..."
                  value={stdinData}
                  onChange={(e) => setStdinData(e.target.value)}
                  style={{ width: "100%", flex: 1, fontFamily: "monospace", fontSize: "0.85rem", background: "#0f172a", border: "1px solid var(--border-subtle)" }}
                />
                <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "0.5rem" }}>
                  Stdin string will be piped directly to the subprocess stdin stream during execution.
                </div>
              </div>
            )}

            {activeConsoleTab === "metrics" && (
              <div style={{ flex: 1, background: "#080c14", padding: "1.25rem", borderRadius: "8px", border: "1px solid rgba(255, 255, 255, 0.1)" }}>
                <h4 style={{ fontSize: "0.9rem", fontWeight: 700, marginBottom: "1rem", color: "var(--text-primary)" }}>
                  📊 Execution & Runtime Diagnostics
                </h4>
                {result ? (
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem" }}>
                    <div className="metric-box" style={{ background: "rgba(15, 23, 42, 0.6)", padding: "1rem", borderRadius: "8px", border: "1px solid var(--border-subtle)" }}>
                      <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>Execution Status</div>
                      <div style={{ fontSize: "1.1rem", fontWeight: 700, color: result.status === "success" ? "#34d399" : "#fb7185", marginTop: "0.25rem" }}>
                        {result.status.toUpperCase()}
                      </div>
                    </div>
                    <div className="metric-box" style={{ background: "rgba(15, 23, 42, 0.6)", padding: "1rem", borderRadius: "8px", border: "1px solid var(--border-subtle)" }}>
                      <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>Runtime Execution Time</div>
                      <div style={{ fontSize: "1.1rem", fontWeight: 700, color: "#38bdf8", marginTop: "0.25rem" }}>
                        {result.execution_time_ms} ms
                      </div>
                    </div>
                    <div className="metric-box" style={{ background: "rgba(15, 23, 42, 0.6)", padding: "1rem", borderRadius: "8px", border: "1px solid var(--border-subtle)" }}>
                      <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>Process Exit Code</div>
                      <div style={{ fontSize: "1.1rem", fontWeight: 700, color: "var(--text-primary)", marginTop: "0.25rem" }}>
                        {result.exit_code}
                      </div>
                    </div>
                    <div className="metric-box" style={{ background: "rgba(15, 23, 42, 0.6)", padding: "1rem", borderRadius: "8px", border: "1px solid var(--border-subtle)" }}>
                      <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>Resolved Engine</div>
                      <div style={{ fontSize: "0.95rem", fontWeight: 600, color: "#c084fc", marginTop: "0.25rem" }}>
                        {result.language_used}
                      </div>
                    </div>
                  </div>
                ) : (
                  <div style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>Run code to generate execution diagnostics.</div>
                )}
              </div>
            )}
          </div>
        </div>

      </div>
    </main>
  );
}
