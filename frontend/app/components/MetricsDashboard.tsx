"use client";

import React from "react";

interface MetricsDashboardProps {
  metrics?: {
    readability?: number;
    security?: number;
    maintainability?: number;
    complexity?: number;
    quality?: number;
  };
}

export default function MetricsDashboard({ metrics }: MetricsDashboardProps) {
  const readability = metrics?.readability ?? 85;
  const security = metrics?.security ?? 90;
  const maintainability = metrics?.maintainability ?? 80;
  const complexity = metrics?.complexity ?? 75;
  const quality = metrics?.quality ?? 88;

  const getMetricColor = (val: number) => {
    if (val >= 80) return "var(--accent-emerald)";
    if (val >= 60) return "var(--accent-cyan)";
    if (val >= 40) return "var(--accent-amber)";
    return "var(--accent-rose)";
  };

  const items = [
    { label: "Security Rating", value: security, icon: "🛡️" },
    { label: "Readability Score", value: readability, icon: "📖" },
    { label: "Maintainability", value: maintainability, icon: "⚙️" },
    { label: "Complexity Rating", value: complexity, icon: "🧩" },
    { label: "Code Quality", value: quality, icon: "✨" },
  ];

  return (
    <div className="card fade-in">
      <div className="card-header">
        <div className="card-title">
          <span>📈</span> Multi-Dimensional Metrics Breakdown
        </div>
      </div>

      <div className="metrics-grid">
        {items.map((item, idx) => {
          const color = getMetricColor(item.value);
          return (
            <div key={idx} className="metric-card">
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <span className="metric-label">{item.label}</span>
                <span style={{ fontSize: "1rem" }}>{item.icon}</span>
              </div>
              <div className="metric-value" style={{ color }}>
                {item.value}<span style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>%</span>
              </div>
              <div className="progress-bar-bg">
                <div
                  className="progress-bar-fill"
                  style={{
                    width: `${Math.min(Math.max(item.value, 0), 100)}%`,
                    backgroundColor: color,
                    boxShadow: `0 0 8px ${color}`,
                  }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
