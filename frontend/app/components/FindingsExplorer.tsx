"use client";

import React, { useState } from "react";

export interface Finding {
  id?: string;
  category: string;
  severity: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | "INFO";
  title: string;
  description: string;
  line_numbers?: number[];
  recommendation?: string;
  impact?: string;
  rag_cited?: boolean;
}

interface FindingsExplorerProps {
  findings: Finding[];
  ragDocuments?: Array<{ id?: string; title: string; category: string; content: string }>;
}

export default function FindingsExplorer({ findings, ragDocuments }: FindingsExplorerProps) {
  const [selectedSeverity, setSelectedSeverity] = useState<string>("ALL");
  const [selectedCategory, setSelectedCategory] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [expandedId, setExpandedId] = useState<number | null>(0); // First item expanded by default

  const severities = ["ALL", "CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"];
  const categories = ["ALL", "security", "bug_risk", "code_quality", "complexity", "style"];

  const filteredFindings = findings.filter((f) => {
    if (selectedSeverity !== "ALL" && f.severity !== selectedSeverity) return false;
    if (selectedCategory !== "ALL" && f.category.toLowerCase() !== selectedCategory.toLowerCase()) return false;
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const matchTitle = f.title.toLowerCase().includes(q);
      const matchDesc = f.description.toLowerCase().includes(q);
      return matchTitle || matchDesc;
    }
    return true;
  });

  const toggleAccordion = (idx: number) => {
    setExpandedId(expandedId === idx ? null : idx);
  };

  return (
    <div className="card fade-in">
      <div className="card-header">
        <div className="card-title">
          <span>🔍</span> Detailed Findings Explorer
          <span className="badge badge-cyan">{filteredFindings.length} Items</span>
        </div>
      </div>

      {/* Filters Bar */}
      <div style={{ display: "flex", flexDirection: "column", gap: "1rem", marginBottom: "1.25rem" }}>
        <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap", alignItems: "center" }}>
          <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", fontWeight: 700, textTransform: "uppercase" }}>Severity:</span>
          {severities.map((sev) => (
            <button
              key={sev}
              type="button"
              className={`btn btn-sm ${selectedSeverity === sev ? "btn-primary" : "btn-secondary"}`}
              style={{ fontSize: "0.75rem", padding: "0.25rem 0.6rem" }}
              onClick={() => setSelectedSeverity(sev)}
            >
              {sev}
            </button>
          ))}
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 2fr", gap: "1rem" }}>
          <select
            className="select-input"
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            style={{ fontSize: "0.825rem" }}
          >
            <option value="ALL">All Categories</option>
            <option value="security">Security Vulnerabilities</option>
            <option value="bug_risk">Bug Risks</option>
            <option value="code_quality">Code Quality</option>
            <option value="complexity">Complexity</option>
            <option value="style">Style & Best Practices</option>
          </select>

          <input
            type="text"
            className="text-input"
            placeholder="Search findings by keyword..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{ fontSize: "0.825rem" }}
          />
        </div>
      </div>

      {/* Findings List */}
      {filteredFindings.length === 0 ? (
        <div style={{ padding: "2.5rem", textAlign: "center", background: "rgba(10, 14, 23, 0.5)", borderRadius: "10px", border: "1px solid var(--border-subtle)" }}>
          <div style={{ fontSize: "2rem", marginBottom: "0.5rem" }}>🎉</div>
          <div style={{ fontWeight: 600, color: "var(--text-primary)" }}>No Findings Match Filter Criteria</div>
          <div style={{ fontSize: "0.825rem", color: "var(--text-muted)", marginTop: "0.25rem" }}>
            Try resetting filters or adjusting search queries.
          </div>
        </div>
      ) : (
        <div>
          {filteredFindings.map((finding, idx) => {
            const isExpanded = expandedId === idx;
            return (
              <div key={idx} className="finding-item">
                <div className="finding-header" onClick={() => toggleAccordion(idx)}>
                  <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
                    <span className={`severity-pill severity-${finding.severity}`}>
                      {finding.severity}
                    </span>
                    <span className="badge badge-purple" style={{ fontSize: "0.7rem" }}>
                      {finding.category.toUpperCase()}
                    </span>
                    <span style={{ fontWeight: 600, fontSize: "0.9rem", color: "var(--text-primary)" }}>
                      {finding.title}
                    </span>
                  </div>

                  <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
                    {finding.line_numbers && finding.line_numbers.length > 0 && (
                      <span className="badge badge-indigo" style={{ fontSize: "0.7rem" }}>
                        Lines {finding.line_numbers.join(", ")}
                      </span>
                    )}
                    <span style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>
                      {isExpanded ? "▲" : "▼"}
                    </span>
                  </div>
                </div>

                {isExpanded && (
                  <div className="finding-body fade-in">
                    <div style={{ marginBottom: "0.75rem", color: "#e2e8f0", lineHeight: 1.6 }}>
                      <strong style={{ color: "var(--accent-cyan)" }}>Description:</strong> {finding.description}
                    </div>

                    {finding.impact && (
                      <div style={{ marginBottom: "0.75rem", color: "var(--text-secondary)", lineHeight: 1.6 }}>
                        <strong style={{ color: "var(--accent-amber)" }}>Impact:</strong> {finding.impact}
                      </div>
                    )}

                    {finding.recommendation && (
                      <div style={{ marginTop: "0.75rem" }}>
                        <div style={{ fontSize: "0.75rem", fontWeight: 700, color: "var(--accent-emerald)", textTransform: "uppercase", marginBottom: "0.35rem" }}>
                          💡 Recommended Remediation
                        </div>
                        <div className="code-block" style={{ marginTop: "0.25rem" }}>
                          <pre>{finding.recommendation}</pre>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* RAG Knowledge Base Section if present */}
      {ragDocuments && ragDocuments.length > 0 && (
        <div style={{ marginTop: "1.5rem", paddingTop: "1rem", borderTop: "1px solid var(--border-subtle)" }}>
          <div style={{ fontSize: "0.85rem", fontWeight: 700, color: "var(--accent-purple)", marginBottom: "0.75rem", display: "flex", alignItems: "center", gap: "0.4rem" }}>
            📚 RAG Vector Knowledge Base Context
          </div>
          <div style={{ display: "grid", gap: "0.75rem" }}>
            {ragDocuments.map((doc, i) => (
              <div key={i} style={{ background: "rgba(168, 85, 247, 0.08)", border: "1px solid rgba(168, 85, 247, 0.25)", padding: "0.75rem 1rem", borderRadius: "8px" }}>
                <div style={{ fontWeight: 600, fontSize: "0.85rem", color: "var(--accent-purple)", marginBottom: "0.25rem" }}>
                  📖 {doc.title} ({doc.category})
                </div>
                <div style={{ fontSize: "0.8rem", color: "var(--text-secondary)" }}>
                  {doc.content.length > 180 ? `${doc.content.substring(0, 180)}...` : doc.content}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
