"use client";

import { useEffect, useState } from "react";

interface HeaderProps {
  backendStatus?: "connected" | "disconnected" | "checking";
}

export default function Header({ backendStatus = "checking" }: HeaderProps) {
  const [status, setStatus] = useState<"connected" | "disconnected" | "checking">(backendStatus);

  useEffect(() => {
    const checkBackend = async () => {
      try {
        const res = await fetch("http://localhost:8000/health");
        if (res.ok) {
          setStatus("connected");
        } else {
          setStatus("disconnected");
        }
      } catch {
        setStatus("disconnected");
      }
    };

    checkBackend();
    const interval = setInterval(checkBackend, 15000);
    return () => clearInterval(interval);
  }, []);

  return (
    <nav className="navbar">
      <div className="logo-container">
        <div className="logo-icon">⚡</div>
        <div>
          <div className="logo-text">CodePilot AI</div>
          <div className="logo-tagline">Multi-Agent Code Review & Refactoring Engine</div>
        </div>
      </div>

      <div style={{ display: "flex", gap: "0.75rem", alignItems: "center" }}>
        <span className="badge badge-indigo">
          <span style={{ fontSize: "0.85rem" }}>🤖</span> LangGraph Multi-Agent
        </span>
        <span className="badge badge-cyan">
          <span style={{ fontSize: "0.85rem" }}>⚡</span> Gemini + Mistral Router
        </span>
        {status === "connected" && (
          <span className="badge badge-success">
            <span className="status-dot"></span> Backend Active
          </span>
        )}
        {status === "disconnected" && (
          <span className="badge badge-danger">
            <span className="status-dot offline"></span> Backend Offline
          </span>
        )}
        {status === "checking" && (
          <span className="badge badge-amber">
            <span className="spinner" style={{ width: "12px", height: "12px" }}></span> Connecting
          </span>
        )}
      </div>
    </nav>
  );
}
