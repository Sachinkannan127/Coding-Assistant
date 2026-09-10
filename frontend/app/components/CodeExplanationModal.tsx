"use client";

import React, { useState, useEffect, useCallback } from "react";
import { Lightbulb, X, Sparkles, BookOpen, Layers, Cpu, Check, Copy, RefreshCw, HelpCircle } from "lucide-react";

export interface LineExplanation {
  line_range: string;
  snippet: string;
  explanation: string;
}

export interface ExplainResult {
  summary: string;
  real_world_analogy: string;
  line_by_line: LineExplanation[];
  key_concepts: string[];
  audience: "simple" | "beginner" | "developer";
}

interface CodeExplanationModalProps {
  isOpen: boolean;
  onClose: () => void;
  code: string;
  language: string;
}

export default function CodeExplanationModal({
  isOpen,
  onClose,
  code,
  language,
}: CodeExplanationModalProps) {
  const [audience, setAudience] = useState<"simple" | "beginner" | "developer">("simple");
  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<ExplainResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState<boolean>(false);

  const fetchExplanation = useCallback(async (targetAudience: "simple" | "beginner" | "developer") => {
    if (!code || !code.trim()) return;

    setLoading(true);
    setError(null);
    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8005";
      const res = await fetch(`${baseUrl}/api/explain`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          code: code,
          language: language,
          audience: targetAudience,
        }),
      });

      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}));
        throw new Error(errJson.detail || `Server error ${res.status}`);
      }

      const data: ExplainResult = await res.json();
      setResult(data);
    } catch (err: any) {
      setError(err.message || "Failed to generate code explanation.");
    } finally {
      setLoading(false);
    }
  }, [code, language]);

  useEffect(() => {
    if (isOpen && code) {
      fetchExplanation(audience);
    }
  }, [isOpen, code, audience, fetchExplanation]);

  if (!isOpen) return null;

  const handleCopy = () => {
    if (!result) return;
    const text = `Explanation Summary:\n${result.summary}\n\nAnalogy:\n${result.real_world_analogy}\n\nLine Breakdown:\n` +
      result.line_by_line.map(l => `${l.line_range}: ${l.snippet} -> ${l.explanation}`).join("\n");
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

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
        maxWidth: "850px",
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
              <Lightbulb className="w-5 h-5 text-white" />
            </div>
            <div>
              <h2 style={{ fontSize: "1.2rem", fontWeight: 700, margin: 0 }}>
                Plain English Code Explainer
              </h2>
              <div style={{ fontSize: "0.78rem", color: "var(--text-muted)", marginTop: "2px" }}>
                AI-Powered Code Breakdown & Metaphor Guide
              </div>
            </div>
          </div>

          <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              onClick={handleCopy}
              disabled={!result}
              style={{ fontSize: "0.78rem" }}
            >
              {copied ? <Check className="w-3.5 h-3.5 text-emerald-400 mr-1 inline" /> : <Copy className="w-3.5 h-3.5 mr-1 inline" />}
              {copied ? "Copied" : "Copy Explanation"}
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

        {/* Audience Mode Selector Bar */}
        <div style={{ padding: "0.75rem 1.5rem", background: "rgba(0, 0, 0, 0.3)", borderBottom: "1px solid rgba(255, 255, 255, 0.05)", display: "flex", gap: "0.5rem", flexWrap: "wrap", alignItems: "center" }}>
          <span style={{ fontSize: "0.8rem", color: "var(--text-muted)", marginRight: "0.5rem", fontWeight: 600 }}>
            Explanation Mode:
          </span>

          <button
            type="button"
            className={`btn btn-sm ${audience === "simple" ? "btn-primary" : "btn-secondary"}`}
            onClick={() => setAudience("simple")}
            style={{ fontSize: "0.78rem", padding: "0.35rem 0.85rem" }}
          >
            🧒 Kids & Beginners (Fun Analogy)
          </button>

          <button
            type="button"
            className={`btn btn-sm ${audience === "beginner" ? "btn-primary" : "btn-secondary"}`}
            onClick={() => setAudience("beginner")}
            style={{ fontSize: "0.78rem", padding: "0.35rem 0.85rem" }}
          >
            🎓 Students & Learners (Step-by-Step)
          </button>

          <button
            type="button"
            className={`btn btn-sm ${audience === "developer" ? "btn-primary" : "btn-secondary"}`}
            onClick={() => setAudience("developer")}
            style={{ fontSize: "0.78rem", padding: "0.35rem 0.85rem" }}
          >
            💻 Experienced Developers (Technical)
          </button>
        </div>

        {/* Modal Body Scroll Area */}
        <div style={{ padding: "1.5rem", overflowY: "auto", flex: 1, display: "flex", flexDirection: "column", gap: "1.25rem" }}>
          {loading && (
            <div style={{ textAlign: "center", padding: "3rem 1rem", color: "var(--text-muted)" }}>
              <RefreshCw className="w-8 h-8 mx-auto mb-3 animate-spin text-purple-400" />
              <div style={{ fontSize: "1rem", fontWeight: 600, color: "var(--text-primary)" }}>
                Generating {audience === "simple" ? "Kids & Beginner" : audience === "beginner" ? "Student Step-by-Step" : "Technical Developer"} Explanation...
              </div>
              <div style={{ fontSize: "0.8rem", marginTop: "0.4rem" }}>
                Translating logic into clear, simple English steps...
              </div>
            </div>
          )}

          {error && !loading && (
            <div style={{ background: "rgba(244, 63, 94, 0.1)", border: "1px solid rgba(244, 63, 94, 0.3)", padding: "1rem", borderRadius: "10px", color: "#fb7185" }}>
              ⚠️ {error}
            </div>
          )}

          {result && !loading && (
            <>
              {/* Summary Card */}
              <div style={{ background: "rgba(99, 102, 241, 0.1)", border: "1px solid rgba(99, 102, 241, 0.25)", padding: "1.25rem", borderRadius: "12px" }}>
                <div style={{ fontSize: "0.8rem", fontWeight: 700, color: "#818cf8", marginBottom: "0.4rem", textTransform: "uppercase", letterSpacing: "0.05em", display: "flex", alignItems: "center", gap: "0.4rem" }}>
                  <BookOpen className="w-4 h-4" /> Plain English Overview
                </div>
                <p style={{ fontSize: "0.95rem", lineHeight: 1.6, color: "var(--text-primary)", margin: 0 }}>
                  {result.summary}
                </p>
              </div>

              {/* Real World Analogy Metaphor Card */}
              <div style={{ background: "linear-gradient(135deg, rgba(168, 85, 247, 0.12), rgba(99, 102, 241, 0.08))", border: "1px solid rgba(168, 85, 247, 0.3)", padding: "1.25rem", borderRadius: "12px" }}>
                <div style={{ fontSize: "0.8rem", fontWeight: 700, color: "#c084fc", marginBottom: "0.4rem", textTransform: "uppercase", letterSpacing: "0.05em", display: "flex", alignItems: "center", gap: "0.4rem" }}>
                  <Sparkles className="w-4 h-4 text-purple-400" /> Fun Real-World Metaphor
                </div>
                <p style={{ fontSize: "0.92rem", lineHeight: 1.6, color: "#e9d5ff", fontStyle: "italic", margin: 0 }}>
                  &ldquo;{result.real_world_analogy}&rdquo;
                </p>
              </div>

              {/* Key Concepts Badges */}
              {result.key_concepts && result.key_concepts.length > 0 && (
                <div>
                  <div style={{ fontSize: "0.8rem", fontWeight: 700, color: "var(--text-muted)", marginBottom: "0.5rem" }}>
                    KEY PROGRAMMING CONCEPTS USED:
                  </div>
                  <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
                    {result.key_concepts.map((concept, i) => (
                      <span key={i} className="badge badge-indigo" style={{ fontSize: "0.78rem", padding: "0.3rem 0.65rem" }}>
                        ⚡ {concept}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Step-by-Step Line Breakdown */}
              <div>
                <div style={{ fontSize: "0.85rem", fontWeight: 700, color: "var(--text-primary)", marginBottom: "0.85rem", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                  <span style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
                    <Layers className="w-4 h-4 text-cyan-400" /> Detailed Line-by-Line Breakdown ({result.line_by_line?.length || 0} Lines Explained)
                  </span>
                  <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
                    Every line analyzed individually
                  </span>
                </div>

                <div style={{ display: "flex", flexDirection: "column", gap: "0.85rem" }}>
                  {result.line_by_line?.map((step, idx) => (
                    <div key={idx} style={{ background: "rgba(15, 23, 42, 0.8)", border: "1px solid rgba(168, 85, 247, 0.2)", padding: "1.1rem", borderRadius: "10px", boxShadow: "0 4px 12px rgba(0,0,0,0.2)" }}>
                      <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", marginBottom: "0.6rem", flexWrap: "wrap" }}>
                        <span className="badge badge-purple" style={{ fontSize: "0.72rem", padding: "0.25rem 0.6rem", fontWeight: 700 }}>
                          {step.line_range}
                        </span>
                        <div style={{ flex: 1, background: "#090d16", padding: "0.35rem 0.75rem", borderRadius: "6px", border: "1px solid rgba(255, 255, 255, 0.08)", overflowX: "auto" }}>
                          <code style={{ fontSize: "0.82rem", color: "#38bdf8", fontFamily: "var(--font-mono, monospace)", whiteSpace: "pre-wrap" }}>
                            {step.snippet}
                          </code>
                        </div>
                      </div>

                      <div style={{ paddingLeft: "0.5rem", borderLeft: "2px solid #a855f7" }}>
                        <p style={{ fontSize: "0.9rem", color: "#e2e8f0", margin: 0, lineHeight: 1.6 }}>
                          💡 <strong>What this line does:</strong> {step.explanation}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
