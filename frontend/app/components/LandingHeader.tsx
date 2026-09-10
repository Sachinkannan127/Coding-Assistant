"use client";

import React, { useEffect, useState, useCallback } from "react";
import { Zap, Sparkles, RefreshCw, Terminal, Code } from "lucide-react";

interface LandingHeaderProps {
  currentView: "landing" | "studio" | "compiler";
  onSwitchView: (view: "landing" | "studio" | "compiler") => void;
}

export default function LandingHeader({ currentView, onSwitchView }: LandingHeaderProps) {
  const [status, setStatus] = useState<"connected" | "disconnected" | "checking">("checking");
  const [scrolled, setScrolled] = useState(false);

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

  useEffect(() => {
    const handleScroll = () => {
      if (window.scrollY > 20) {
        setScrolled(true);
      } else {
        setScrolled(false);
      }
    };
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <header className={`landing-navbar ${scrolled ? "scrolled" : ""}`}>
      <div className="landing-navbar-container">
        {/* Brand Logo */}
        <div className="logo-container" onClick={() => onSwitchView("landing")} style={{ cursor: "pointer" }}>
          <div className="logo-icon animate-glow">
            <Zap className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="logo-text">CodePilot AI</div>
            <div className="logo-tagline">Multi-Agent Code Review & Sandbox</div>
          </div>
        </div>

        {/* Center Nav Links */}
        <nav className="nav-links">
          {currentView === "landing" ? (
            <>
              <a href="#features" className="nav-link">Features</a>
              <a href="#architecture" className="nav-link">8-Agent Engine</a>
              <a href="#sandbox" className="nav-link">Live Demo</a>
              <a href="#benchmarks" className="nav-link">Benchmarks</a>
              <a href="#pricing" className="nav-link">Pricing</a>
              <a href="#faq" className="nav-link">FAQ</a>
            </>
          ) : (
            <div style={{ display: "flex", gap: "0.5rem" }}>
              <button
                type="button"
                className={`nav-link ${currentView === "studio" ? "active" : ""}`}
                onClick={() => onSwitchView("studio")}
                style={{ background: currentView === "studio" ? "rgba(99, 102, 241, 0.2)" : "transparent", padding: "0.35rem 0.75rem", borderRadius: "6px" }}
              >
                <Code className="w-4 h-4 mr-1 inline" /> AI Review Studio
              </button>
            </div>
          )}
        </nav>

        {/* Right Actions */}
        <div className="nav-actions">
          {/* Backend Status Indicator */}
          {status === "connected" && (
            <span className="status-badge connected" title="FastAPI Backend Connected">
              <span className="status-dot"></span> API Active
            </span>
          )}
          {status === "disconnected" && (
            <button 
              type="button" 
              className="status-badge disconnected" 
              onClick={checkBackend}
              title="Click to re-check API connection"
            >
              <RefreshCw className="w-3 h-3 animate-spin" /> Offline (Retry)
            </button>
          )}
          {status === "checking" && (
            <span className="status-badge checking">
              <span className="spinner-mini"></span> Connecting...
            </span>
          )}

          {/* Primary CTAs on Landing Page */}
          {currentView === "landing" && (
            <div style={{ display: "flex", gap: "0.5rem" }}>
              <button
                type="button"
                className="btn-launch-primary"
                onClick={() => onSwitchView("studio")}
              >
                <Sparkles className="w-4 h-4 mr-1.5 inline" />
                Launch Studio
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
