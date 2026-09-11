"use client";

import { useEffect, useState, useCallback } from "react";
import { useUser, SignInButton, UserButton } from "@clerk/nextjs";

interface HeaderProps {
  backendStatus?: "connected" | "disconnected" | "checking";
}

export default function Header({ backendStatus = "checking" }: HeaderProps) {
  const { isSignedIn, isLoaded } = useUser();
  const [status, setStatus] = useState<"connected" | "disconnected" | "checking">(backendStatus);

  const checkBackend = useCallback(async () => {
    setStatus("checking");
    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8005";
      const res = await fetch(`${baseUrl}/health`);
      if (res.ok) {
        setStatus("connected");
      } else {
        setStatus("disconnected");
      }
    } catch {
      setStatus("disconnected");
    }
  }, []);

  useEffect(() => {
    checkBackend();
    const interval = setInterval(checkBackend, 15000);
    return () => clearInterval(interval);
  }, [checkBackend]);

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
          <span className="badge badge-success" title="FastAPI server operational">
            <span className="status-dot"></span> Backend Active
          </span>
        )}
        {status === "disconnected" && (
          <button
            type="button"
            className="badge badge-danger"
            onClick={checkBackend}
            style={{ cursor: "pointer", border: "1px solid rgba(244, 63, 94, 0.4)" }}
            title="Click to retry connecting to FastAPI backend"
          >
            <span className="status-dot offline"></span> Backend Offline (Retry)
          </button>
        )}
        {status === "checking" && (
          <span className="badge badge-amber">
            <span className="spinner" style={{ width: "12px", height: "12px" }}></span> Connecting
          </span>
        )}

        <div style={{ marginLeft: "0.5rem" }}>
          {isLoaded && !isSignedIn && (
            <SignInButton mode="modal">
              <button
                type="button"
                style={{
                  background: "linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)",
                  border: "none",
                  color: "#ffffff",
                  padding: "0.35rem 0.75rem",
                  borderRadius: "6px",
                  fontSize: "0.85rem",
                  fontWeight: 600,
                  cursor: "pointer"
                }}
              >
                Log In
              </button>
            </SignInButton>
          )}
          {isLoaded && isSignedIn && (
            <UserButton />
          )}


        </div>
      </div>
    </nav>
  );
}


