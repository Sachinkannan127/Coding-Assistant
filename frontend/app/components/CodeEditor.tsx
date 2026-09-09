"use client";

import React, { useMemo } from "react";

interface CodeEditorProps {
  code: string;
  setCode: (val: string) => void;
  language: string;
  setLanguage: (val: string) => void;
  framework: string;
  setFramework: (val: string) => void;
  reviewMode: "quick" | "deep";
  setReviewMode: (val: "quick" | "deep") => void;
  onSubmit: () => void;
  loading: boolean;
}

const PRESET_SAMPLES = [
  {
    name: "Python API (SQL Injection & Insecure Eval)",
    language: "python",
    framework: "fastapi",
    code: `import sqlite3
import os

def handle_user_login(username, password):
    # SQL Injection vulnerability
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
    cursor.execute(query)
    user = cursor.fetchone()
    
    # Insecure eval of user preference
    config = eval(username.get("config", "{}"))
    
    return user
`
  },
  {
    name: "JavaScript/React (Memory Leak & Anti-Pattern)",
    language: "javascript",
    framework: "react",
    code: `import React, { useState, useEffect } from 'react';

export function UserFeed({ userId }) {
  const [data, setData] = useState(null);

  useEffect(() => {
    // Missing cleanup function causing memory leak on unmount
    const timer = setInterval(() => {
      fetch('/api/user/' + userId)
        .then(res => res.json())
        .then(res => setData(res));
    }, 1000);
  }, []); // Missing userId dependency

  return <div>{data ? JSON.stringify(data) : 'Loading...'}</div>;
}
`
  },
  {
    name: "C Language (Buffer Overflow & Null Pointer)",
    language: "c",
    framework: "none",
    code: `#include <stdio.h>
#include <string.h>
#include <stdlib.h>

void process_input(char *user_str) {
    char buffer[16];
    // Vulnerable strcpy without length check
    strcpy(buffer, user_str);
    
    char *ptr = NULL;
    if (strlen(user_str) > 10) {
        printf("Length exceeds threshold\n");
    }
    // Null pointer dereference hazard
    *ptr = 'X';
}
`
  }
];

export default function CodeEditor({
  code,
  setCode,
  language,
  setLanguage,
  framework,
  setFramework,
  reviewMode,
  setReviewMode,
  onSubmit,
  loading,
}: CodeEditorProps) {
  const lineCount = useMemo(() => {
    if (!code) return 1;
    return code.split("\n").length;
  }, [code]);

  const lineNumbers = useMemo(() => {
    return Array.from({ length: Math.max(lineCount, 12) }, (_, i) => i + 1);
  }, [lineCount]);

  const loadPreset = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const idx = parseInt(e.target.value, 10);
    if (isNaN(idx)) return;
    const sample = PRESET_SAMPLES[idx];
    if (sample) {
      setCode(sample.code);
      setLanguage(sample.language);
      setFramework(sample.framework);
    }
  };

  return (
    <div className="card">
      <div className="card-header">
        <div className="card-title">
          <span style={{ fontSize: "1.2rem" }}>💻</span> Code Input Workspace
        </div>
        <div style={{ display: "flex", gap: "0.5rem" }}>
          <select 
            className="select-input" 
            onChange={loadPreset}
            defaultValue=""
            style={{ fontSize: "0.8rem", padding: "0.35rem 0.75rem" }}
          >
            <option value="" disabled>Load Preset Sample Code...</option>
            {PRESET_SAMPLES.map((s, i) => (
              <option key={i} value={i}>{s.name}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Control Bar: Language, Framework, Mode */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "1rem", marginBottom: "1rem" }}>
        <div className="form-group">
          <label className="form-label">Language</label>
          <select
            className="select-input"
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
          >
            <option value="auto">Auto-Detect</option>
            <option value="python">Python</option>
            <option value="javascript">JavaScript</option>
            <option value="typescript">TypeScript</option>
            <option value="react">React JSX/TSX</option>
            <option value="nextjs">Next.js</option>
            <option value="nodejs">Node.js</option>
            <option value="c">C</option>
            <option value="cpp">C++</option>
            <option value="java">Java</option>
            <option value="go">Go</option>
            <option value="rust">Rust</option>
            <option value="django">Django</option>
          </select>
        </div>

        <div className="form-group">
          <label className="form-label">Framework</label>
          <select
            className="select-input"
            value={framework}
            onChange={(e) => setFramework(e.target.value)}
          >
            <option value="none">None / Standard</option>
            <option value="react">React</option>
            <option value="nextjs">Next.js</option>
            <option value="nodejs">Node.js / Express</option>
            <option value="fastapi">FastAPI</option>
            <option value="flask">Flask</option>
            <option value="django">Django</option>
            <option value="springboot">Spring Boot</option>
          </select>
        </div>

        <div className="form-group">
          <label className="form-label">Review Mode</label>
          <div style={{ display: "flex", gap: "0.25rem", background: "var(--bg-input)", padding: "3px", borderRadius: "8px", border: "1px solid var(--border-subtle)" }}>
            <button
              type="button"
              className={`btn btn-sm ${reviewMode === "quick" ? "btn-primary" : "btn-secondary"}`}
              style={{ flex: 1, padding: "0.4rem 0.5rem", fontSize: "0.78rem" }}
              onClick={() => setReviewMode("quick")}
            >
              ⚡ Quick Scan
            </button>
            <button
              type="button"
              className={`btn btn-sm ${reviewMode === "deep" ? "btn-primary" : "btn-secondary"}`}
              style={{ flex: 1, padding: "0.4rem 0.5rem", fontSize: "0.78rem" }}
              onClick={() => setReviewMode("deep")}
            >
              🔍 Deep Review
            </button>
          </div>
        </div>
      </div>

      {/* Editor Body with Line Numbers */}
      <div className="editor-container">
        <div className="editor-toolbar">
          <div style={{ display: "flex", gap: "0.5rem", alignItems: "center", fontSize: "0.75rem", color: "var(--text-muted)" }}>
            <span style={{ color: "var(--accent-cyan)", fontWeight: 600 }}>{language.toUpperCase()}</span>
            <span>•</span>
            <span>{lineCount} lines</span>
            <span>•</span>
            <span>{code.length} characters</span>
          </div>
          <button 
            type="button" 
            className="btn btn-secondary btn-sm"
            onClick={() => setCode("")}
          >
            Clear Code
          </button>
        </div>

        <div className="editor-body">
          <div className="line-numbers">
            {lineNumbers.map((num) => (
              <div key={num}>{num}</div>
            ))}
          </div>
          <textarea
            className="code-textarea"
            placeholder="// Paste code snippet here or select a Preset Sample above..."
            value={code}
            onChange={(e) => setCode(e.target.value)}
            spellCheck={false}
          />
        </div>
      </div>

      {/* Action Button */}
      <div style={{ marginTop: "1.25rem", display: "flex", justifyContent: "flex-end" }}>
        <button
          type="button"
          className="btn btn-primary"
          onClick={onSubmit}
          disabled={loading || !code.trim()}
          style={{ padding: "0.875rem 2rem", fontSize: "0.95rem" }}
        >
          {loading ? (
            <>
              <span className="spinner"></span>
              <span>Analyzing with LangGraph Agents...</span>
            </>
          ) : (
            <>
              <span>🚀 Launch Multi-Agent Review</span>
            </>
          )}
        </button>
      </div>
    </div>
  );
}
