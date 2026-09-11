"use client";

import React, { useEffect, useState, useCallback } from "react";
import { Zap, Sparkles, RefreshCw, Terminal, Code, Network, LogIn, UserPlus } from "lucide-react";
import { useUser, SignInButton, SignUpButton, UserButton } from "@clerk/nextjs";

interface LandingHeaderProps {
  currentView: "landing" | "studio" | "compiler" | "mcp";
  onSwitchView: (view: "landing" | "studio" | "compiler" | "mcp") => void;
}

export default function LandingHeader({ currentView, onSwitchView }: LandingHeaderProps) {
  const { isSignedIn, isLoaded } = useUser();
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
            <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
              <button
                type="button"
                className={`nav-link ${currentView === "studio" ? "active" : ""}`}
                onClick={() => onSwitchView("studio")}
                style={{ 
                  background: currentView === "studio" ? "rgba(99, 102, 241, 0.25)" : "transparent", 
                  border: currentView === "studio" ? "1px solid rgba(99, 102, 241, 0.4)" : "1px solid transparent",
                  padding: "0.35rem 0.75rem", 
                  borderRadius: "6px",
                  color: currentView === "studio" ? "#a5b4fc" : "#94a3b8",
                  cursor: "pointer",
                  display: "inline-flex",
                  alignItems: "center",
                  whiteSpace: "nowrap"
                }}
              >
                <Code className="w-4 h-4 mr-1 text-indigo-400" /> AI Review Studio
              </button>
              <button
                type="button"
                className={`nav-link ${currentView === "compiler" ? "active" : ""}`}
                onClick={() => onSwitchView("compiler")}
                style={{ 
                  background: currentView === "compiler" ? "rgba(168, 85, 247, 0.25)" : "transparent", 
                  border: currentView === "compiler" ? "1px solid rgba(168, 85, 247, 0.4)" : "1px solid transparent",
                  padding: "0.35rem 0.75rem", 
                  borderRadius: "6px",
                  color: currentView === "compiler" ? "#c084fc" : "#94a3b8",
                  cursor: "pointer",
                  display: "inline-flex",
                  alignItems: "center",
                  whiteSpace: "nowrap"
                }}
              >
                <Terminal className="w-4 h-4 mr-1 text-purple-400" /> Compiler Sandbox
              </button>
              <button
                type="button"
                className={`nav-link ${currentView === "mcp" ? "active" : ""}`}
                onClick={() => onSwitchView("mcp")}
                style={{ 
                  background: currentView === "mcp" ? "rgba(56, 189, 248, 0.25)" : "transparent", 
                  border: currentView === "mcp" ? "1px solid rgba(56, 189, 248, 0.4)" : "1px solid transparent",
                  padding: "0.35rem 0.75rem", 
                  borderRadius: "6px",
                  color: currentView === "mcp" ? "#38bdf8" : "#94a3b8",
                  cursor: "pointer",
                  display: "inline-flex",
                  alignItems: "center",
                  whiteSpace: "nowrap"
                }}
              >
                <Network className="w-4 h-4 mr-1 text-cyan-400" /> MCP Connectors
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
            <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
              <button
                type="button"
                className="btn-launch-primary"
                onClick={() => onSwitchView("studio")}
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  whiteSpace: "nowrap"
                }}
              >
                <Sparkles className="w-4 h-4 mr-1.5" />
                Launch Studio
              </button>
            </div>
          )}

          {/* Authentication Actions */}
          <div style={{ display: "flex", gap: "0.5rem", alignItems: "center", marginLeft: "0.5rem" }}>
            {isLoaded && !isSignedIn && (
              <>
                <SignInButton mode="modal">
                  <button
                    type="button"
                    style={{
                      background: "rgba(255, 255, 255, 0.05)",
                      border: "1px solid rgba(255, 255, 255, 0.15)",
                      color: "#f8fafc",
                      padding: "0.4rem 0.85rem",
                      borderRadius: "8px",
                      fontSize: "0.85rem",
                      fontWeight: 500,
                      cursor: "pointer",
                      display: "inline-flex",
                      alignItems: "center",
                      gap: "0.35rem"
                    }}
                  >
                    <LogIn className="w-3.5 h-3.5" /> Log In
                  </button>
                </SignInButton>
                <SignUpButton mode="modal">
                  <button
                    type="button"
                    style={{
                      background: "linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)",
                      border: "none",
                      color: "#ffffff",
                      padding: "0.4rem 0.85rem",
                      borderRadius: "8px",
                      fontSize: "0.85rem",
                      fontWeight: 600,
                      cursor: "pointer",
                      display: "inline-flex",
                      alignItems: "center",
                      gap: "0.35rem"
                    }}
                  >
                    <UserPlus className="w-3.5 h-3.5" /> Sign Up
                  </button>
                </SignUpButton>
              </>
            )}

            {isLoaded && isSignedIn && (
              <UserButton
                appearance={{
                  elements: {
                    userButtonAvatarBox: {
                      width: "36px",
                      height: "36px",
                      border: "2px solid #6366f1"
                    }
                  }
                }}
              />
            )}


          </div>

        </div>
      </div>
    </header>
  );
}

