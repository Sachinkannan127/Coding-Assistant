"use client";

import React, { useState, useEffect, useCallback } from "react";
import { FlaskConical, X, Play, Plus, Trash2, CheckCircle2, AlertTriangle, Clock, RefreshCw, Check, Copy, Sparkles, Lightbulb } from "lucide-react";

export interface TestCaseItem {
  id: number;
  name: string;
  input_data: string;
  expected_output: string;
}

export interface TestCaseRunResult {
  id: number;
  name: string;
  input_data: string;
  expected_output: string;
  actual_output: string;
  passed: boolean;
  execution_time_ms: number;
  status: "PASSED" | "FAILED" | "TIMEOUT" | "ERROR";
}

export interface TestCaseSuiteResponse {
  results: TestCaseRunResult[];
  total_tests: number;
  passed_tests: number;
  success_rate: number;
}

export interface GenerateTestCasesResponse {
  test_cases: TestCaseItem[];
  reasoning: string;
  detected_inputs: string[];
}

interface TestCasesModalProps {
  isOpen: boolean;
  onClose: () => void;
  code: string;
  language: string;
}

const DEFAULT_TEST_CASES: TestCaseItem[] = [
  {
    id: 1,
    name: "Test Case 1 (Sample Verification)",
    input_data: "",
    expected_output: ""
  }
];

export default function TestCasesModal({
  isOpen,
  onClose,
  code,
  language,
}: TestCasesModalProps) {
  const [testCases, setTestCases] = useState<TestCaseItem[]>([
    {
      id: 1,
      name: "Test Case 1",
      input_data: "10\n20",
      expected_output: "30"
    },
    {
      id: 2,
      name: "Test Case 2",
      input_data: "5\n15",
      expected_output: "20"
    }
  ]);
  const [loading, setLoading] = useState<boolean>(false);
  const [generatingAi, setGeneratingAi] = useState<boolean>(false);
  const [aiReasoning, setAiReasoning] = useState<string>("");
  const [detectedInputs, setDetectedInputs] = useState<string[]>([]);
  const [suiteResult, setSuiteResult] = useState<TestCaseSuiteResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleGenerateAiTestCases = useCallback(async () => {
    if (!code || !code.trim()) return;

    setGeneratingAi(true);
    setError(null);
    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8005";
      const res = await fetch(`${baseUrl}/api/sandbox/generate-testcases`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          code: code,
          language: language,
          max_cases: 4
        })
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || `Server error ${res.status}`);
      }

      const data: GenerateTestCasesResponse = await res.json();
      if (data.test_cases && data.test_cases.length > 0) {
        setTestCases(data.test_cases);
      }
      setAiReasoning(data.reasoning || "");
      setDetectedInputs(data.detected_inputs || []);
      setSuiteResult(null); // Reset previous results on new generation
    } catch (err: any) {
      setError(err.message || "Failed to generate AI test cases.");
    } finally {
      setGeneratingAi(false);
    }
  }, [code, language]);

  const handleRunSuite = useCallback(async () => {
    if (!code || !code.trim()) return;

    setLoading(true);
    setError(null);
    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8005";
      const res = await fetch(`${baseUrl}/api/sandbox/testcases`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          code: code,
          language: language,
          test_cases: testCases,
        }),
      });

      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}));
        throw new Error(errJson.detail || `Server error ${res.status}`);
      }

      const data: TestCaseSuiteResponse = await res.json();
      setSuiteResult(data);
    } catch (err: any) {
      setError(err.message || "Failed to execute test suite.");
    } finally {
      setLoading(false);
    }
  }, [code, language, testCases]);

  useEffect(() => {
    if (isOpen && code && code.trim()) {
      handleGenerateAiTestCases();
    }
  }, [isOpen, code, language, handleGenerateAiTestCases]);

  const addTestCase = () => {
    const nextId = testCases.length > 0 ? Math.max(...testCases.map(t => t.id)) + 1 : 1;
    setTestCases([
      ...testCases,
      {
        id: nextId,
        name: `Test Case ${nextId}`,
        input_data: "",
        expected_output: ""
      }
    ]);
  };

  const removeTestCase = (id: number) => {
    if (testCases.length <= 1) return;
    setTestCases(testCases.filter(t => t.id !== id));
  };

  const updateTestCase = (id: number, field: keyof TestCaseItem, value: string) => {
    setTestCases(testCases.map(t => t.id === id ? { ...t, [field]: value } : t));
  };

  if (!isOpen) return null;

  return (
    <div style={{
      position: "fixed",
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      background: "rgba(3, 7, 18, 0.85)",
      backdropFilter: "blur(12px)",
      zIndex: 9999,
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      padding: "1.5rem"
    }}>
      <div style={{
        background: "#0b0f19",
        border: "1px solid rgba(168, 85, 247, 0.3)",
        borderRadius: "16px",
        width: "100%",
        maxWidth: "900px",
        maxHeight: "90vh",
        display: "flex",
        flexDirection: "column",
        boxShadow: "0 25px 60px rgba(0, 0, 0, 0.6)",
        overflow: "hidden"
      }}>
        {/* Modal Header */}
        <div style={{ padding: "1.25rem 1.5rem", borderBottom: "1px solid rgba(255, 255, 255, 0.08)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
            <div style={{ background: "linear-gradient(135deg, #a855f7, #6366f1)", padding: "0.5rem", borderRadius: "10px", display: "flex" }}>
              <FlaskConical className="w-5 h-5 text-white" />
            </div>
            <div>
              <h2 style={{ fontSize: "1.2rem", fontWeight: 700, margin: 0, display: "flex", alignItems: "center", gap: "0.5rem" }}>
                Compiler Test Cases Suite Runner
              </h2>
              <div style={{ fontSize: "0.78rem", color: "var(--text-muted)", marginTop: "2px" }}>
                Input (stdin) → Expected Output Verification • {language.toUpperCase()} Engine
              </div>
            </div>
          </div>

          <div style={{ display: "flex", gap: "0.5rem", alignItems: "center", flexWrap: "wrap" }}>
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              onClick={handleGenerateAiTestCases}
              disabled={generatingAi || !code || !code.trim()}
              style={{ fontSize: "0.78rem", borderColor: "rgba(168, 85, 247, 0.4)", color: "#c084fc" }}
            >
              {generatingAi ? (
                <>
                  <RefreshCw className="w-3.5 h-3.5 mr-1 inline animate-spin" /> Detecting Code & Generating...
                </>
              ) : (
                <>
                  <Sparkles className="w-3.5 h-3.5 mr-1 inline text-amber-400" /> ✨ Auto-Generate AI Test Cases
                </>
              )}
            </button>

            <button
              type="button"
              className="btn btn-secondary btn-sm"
              onClick={addTestCase}
              style={{ fontSize: "0.78rem" }}
            >
              <Plus className="w-3.5 h-3.5 mr-1 inline" /> Add Test Case
            </button>

            <button
              type="button"
              className="btn btn-primary btn-sm"
              onClick={handleRunSuite}
              disabled={loading || !code || !code.trim()}
              style={{
                background: "linear-gradient(135deg, #a855f7, #6366f1)",
                border: "none",
                fontSize: "0.82rem",
                padding: "0.45rem 1rem"
              }}
            >
              {loading ? (
                <>
                  <RefreshCw className="w-3.5 h-3.5 mr-1.5 animate-spin" /> Running Suite...
                </>
              ) : (
                <>
                  <Play className="w-3.5 h-3.5 mr-1.5 fill-current" /> ▶ Run All Test Cases
                </>
              )}
            </button>

            <button
              type="button"
              onClick={onClose}
              style={{ background: "transparent", border: "none", color: "var(--text-muted)", cursor: "pointer", padding: "0.4rem", borderRadius: "6px" }}
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* AI Analysis Reasoning Banner */}
        {aiReasoning && (
          <div style={{ padding: "0.75rem 1.5rem", background: "rgba(168, 85, 247, 0.12)", borderBottom: "1px solid rgba(168, 85, 247, 0.2)", fontSize: "0.8rem", color: "#e9d5ff", display: "flex", alignItems: "flex-start", gap: "0.6rem" }}>
            <Sparkles className="w-4 h-4 text-amber-400 mt-0.5 flex-shrink-0" />
            <div>
              <strong style={{ color: "#ffffff" }}>AI Code Analysis & Test Strategy:</strong> {aiReasoning}
              {detectedInputs && detectedInputs.length > 0 && (
                <div style={{ marginTop: "4px", fontSize: "0.75rem", color: "#c084fc" }}>
                  Detected Inputs: <code>{detectedInputs.join(", ")}</code>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Test Suite Summary Score Bar */}
        {suiteResult && (
          <div style={{ padding: "0.75rem 1.5rem", background: "rgba(0, 0, 0, 0.35)", borderBottom: "1px solid rgba(255, 255, 255, 0.05)", display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "0.5rem" }}>
            <div style={{ display: "flex", gap: "0.75rem", alignItems: "center" }}>
              <span className={`badge ${suiteResult.passed_tests === suiteResult.total_tests ? "badge-success" : "badge-amber"}`} style={{ fontSize: "0.8rem", padding: "0.3rem 0.75rem", display: "flex", alignItems: "center", gap: "0.35rem" }}>
                {suiteResult.passed_tests === suiteResult.total_tests ? <CheckCircle2 className="w-4 h-4" /> : <AlertTriangle className="w-4 h-4" />}
                {suiteResult.passed_tests} / {suiteResult.total_tests} Test Cases Passed ({suiteResult.success_rate}%)
              </span>
            </div>

            <div style={{ fontSize: "0.78rem", color: "var(--text-muted)" }}>
              Evaluated {suiteResult.total_tests} input scenario{suiteResult.total_tests > 1 ? "s" : ""}
            </div>
          </div>
        )}

        {/* Modal Scroll Body */}
        <div style={{ padding: "1.5rem", overflowY: "auto", flex: 1, display: "flex", flexDirection: "column", gap: "1rem" }}>
          {error && (
            <div style={{ background: "rgba(244, 63, 94, 0.1)", border: "1px solid rgba(244, 63, 94, 0.3)", padding: "1rem", borderRadius: "10px", color: "#fb7185" }}>
              ⚠️ {error}
            </div>
          )}

          {testCases.map((tc, idx) => {
            const res = suiteResult?.results.find(r => r.id === tc.id);

            return (
              <div key={tc.id} style={{ background: "rgba(15, 23, 42, 0.75)", border: "1px solid rgba(168, 85, 247, 0.2)", borderRadius: "12px", padding: "1.25rem", display: "flex", flexDirection: "column", gap: "0.85rem" }}>
                {/* Card Title & Controls */}
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "0.6rem" }}>
                    <span className="badge badge-purple" style={{ fontSize: "0.75rem" }}>
                      Test #{idx + 1}
                    </span>
                    <input
                      type="text"
                      className="select-input"
                      value={tc.name}
                      onChange={(e) => updateTestCase(tc.id, "name", e.target.value)}
                      style={{ fontSize: "0.85rem", fontWeight: 600, padding: "0.25rem 0.5rem", background: "transparent", border: "1px solid transparent" }}
                    />
                  </div>

                  <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
                    {res && (
                      <span className={`badge ${res.passed ? "badge-success" : res.status === "TIMEOUT" ? "badge-amber" : "badge-danger"}`} style={{ fontSize: "0.75rem", display: "flex", alignItems: "center", gap: "0.3rem" }}>
                        {res.passed ? <CheckCircle2 className="w-3.5 h-3.5" /> : <AlertTriangle className="w-3.5 h-3.5" />}
                        {res.status} ({res.execution_time_ms} ms)
                      </span>
                    )}

                    {testCases.length > 1 && (
                      <button
                        type="button"
                        onClick={() => removeTestCase(tc.id)}
                        style={{ background: "transparent", border: "none", color: "#fb7185", cursor: "pointer", padding: "0.3rem" }}
                        title="Delete Test Case"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    )}
                  </div>
                </div>

                {/* Input & Expected Output Grid */}
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem" }}>
                  <div>
                    <label className="form-label" style={{ fontSize: "0.78rem", color: "var(--text-muted)" }}>
                      Standard Input (stdin):
                    </label>
                    <textarea
                      className="select-input"
                      rows={3}
                      placeholder="Enter stdin input string..."
                      value={tc.input_data}
                      onChange={(e) => updateTestCase(tc.id, "input_data", e.target.value)}
                      style={{ width: "100%", fontFamily: "monospace", fontSize: "0.82rem", background: "#080c14" }}
                    />
                  </div>

                  <div>
                    <label className="form-label" style={{ fontSize: "0.78rem", color: "var(--text-muted)" }}>
                      Expected Output (stdout):
                    </label>
                    <textarea
                      className="select-input"
                      rows={3}
                      placeholder="Enter expected stdout string..."
                      value={tc.expected_output}
                      onChange={(e) => updateTestCase(tc.id, "expected_output", e.target.value)}
                      style={{ width: "100%", fontFamily: "monospace", fontSize: "0.82rem", background: "#080c14" }}
                    />
                  </div>
                </div>

                {/* Actual Output Result Display */}
                {res && (
                  <div style={{ background: "#080c14", borderRadius: "8px", border: `1px solid ${res.passed ? "rgba(52, 211, 153, 0.3)" : "rgba(244, 63, 94, 0.3)"}`, padding: "0.75rem 1rem" }}>
                    <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginBottom: "0.3rem", fontWeight: 600 }}>
                      Actual Process Output:
                    </div>
                    <pre style={{ margin: 0, fontFamily: "monospace", fontSize: "0.82rem", color: res.passed ? "#34d399" : "#fb7185", whiteSpace: "pre-wrap" }}>
                      {res.actual_output}
                    </pre>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
