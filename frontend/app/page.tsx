"use client";

import { useEffect, useState } from "react";

interface HealthStatus {
  status: string;
  app_name: string;
  version: string;
  environment: string;
  timestamp: string;
}

export default function Home() {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const checkHealth = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("http://localhost:8000/health");
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}: ${res.statusText}`);
      }
      const data = await res.json();
      setHealth(data);
    } catch (err: any) {
      setError(err.message || "Failed to connect to FastAPI backend.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    checkHealth();
  }, []);

  return (
    <main className="container">
      <div style={{ marginBottom: "2rem" }}>
        <h1 style={{ fontSize: "2.25rem", fontWeight: 700, marginBottom: "0.5rem" }}>
          Full-Stack Foundation Status
        </h1>
        <p style={{ color: "var(--text-secondary)", fontSize: "1.05rem" }}>
          Phase 1 setup complete — Next.js frontend integrated with FastAPI backend gateway.
        </p>
      </div>

      <div className="grid">
        <div className="card">
          <div className="card-title">
            <span>🚀</span> Backend API Status
          </div>
          {loading && <p className="card-text">Connecting to FastAPI endpoint...</p>}
          {error && (
            <div>
              <p className="card-text" style={{ color: "#ef4444", marginBottom: "0.5rem" }}>
                ⚠️ {error}
              </p>
              <p className="card-text">Ensure FastAPI server is running on <code>http://localhost:8000</code>.</p>
            </div>
          )}
          {health && (
            <div>
              <p className="card-text" style={{ marginBottom: "0.75rem" }}>
                FastAPI server is operational and responding to health probes.
              </p>
              <div className="code-block">
                <pre>{JSON.stringify(health, null, 2)}</pre>
              </div>
            </div>
          )}
          <button 
            className="btn btn-primary" 
            style={{ marginTop: "1rem" }} 
            onClick={checkHealth}
          >
            Refresh Probe
          </button>
        </div>

        <div className="card">
          <div className="card-title">
            <span>⚙️</span> System Architecture Baseline
          </div>
          <p className="card-text" style={{ marginBottom: "1rem" }}>
            The platform architecture specifies the following stack for incoming phases:
          </p>
          <ul style={{ listStyle: "none", color: "var(--text-secondary)", fontSize: "0.875rem" }}>
            <li style={{ marginBottom: "0.5rem" }}>• <strong>Primary Model</strong>: Google Gemini (gemini-2.5-flash / pro)</li>
            <li style={{ marginBottom: "0.5rem" }}>• <strong>Secondary Model</strong>: Mistral AI (codestral / mistral-large)</li>
            <li style={{ marginBottom: "0.5rem" }}>• <strong>Embeddings</strong>: Gemini text-embedding-004</li>
            <li style={{ marginBottom: "0.5rem" }}>• <strong>Vector Store</strong>: MongoDB Atlas Vector Search</li>
            <li style={{ marginBottom: "0.5rem" }}>• <strong>Orchestration</strong>: LangGraph multi-agent engine</li>
          </ul>
        </div>

        <div className="card">
          <div className="card-title">
            <span>📋</span> Upcoming Roadmap
          </div>
          <p className="card-text" style={{ marginBottom: "0.75rem" }}>
            Next phase execution targets:
          </p>
          <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
            <div style={{ padding: "0.5rem 0.75rem", background: "rgba(255,255,255,0.03)", borderRadius: "6px" }}>
              <span style={{ fontWeight: 600, color: "var(--accent-cyan)" }}>Phase 2</span>: MongoDB Persistence Layer
            </div>
            <div style={{ padding: "0.5rem 0.75rem", background: "rgba(255,255,255,0.03)", borderRadius: "6px" }}>
              <span style={{ fontWeight: 600, color: "var(--accent-indigo)" }}>Phase 3</span>: Gemini & Mistral Provider Layer
            </div>
            <div style={{ padding: "0.5rem 0.75rem", background: "rgba(255,255,255,0.03)", borderRadius: "6px" }}>
              <span style={{ fontWeight: 600, color: "var(--accent-purple)" }}>Phase 4</span>: Code Validation & Language Detection
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
