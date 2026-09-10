"use client";

import React, { useState } from "react";
import { 
  Zap, 
  ShieldCheck, 
  Cpu, 
  GitCompare, 
  Code2, 
  FileText, 
  CheckCircle2, 
  ArrowRight, 
  Sparkles, 
  Layers, 
  Activity, 
  Terminal, 
  Lock, 
  Play, 
  Copy, 
  Check, 
  ChevronDown, 
  ChevronUp, 
  Star, 
  BarChart3, 
  Server, 
  RefreshCw, 
  Database,
  Sliders,
  CheckCircle,
  XCircle,
  HelpCircle,
  X
} from "lucide-react";

interface LandingPageProps {
  onLaunchStudio: () => void;
}

// Sample scenarios for live interactive demo sandbox
const SAMPLE_SCENARIOS = [
  {
    id: "security",
    title: "SQL Injection & Vulnerable Auth",
    language: "python",
    icon: ShieldCheck,
    badgeColor: "rose",
    original: `def authenticate_user(db_connection, username, password):
    # CRITICAL: Insecure string concatenation vulnerable to SQL Injection
    query = "SELECT * FROM users WHERE username = '" + username + "' AND password = '" + password + "'"
    cursor = db_connection.cursor()
    cursor.execute(query)
    user = cursor.fetchone()
    
    # Insecure plain-text password comparison
    if user and user['password'] == password:
        return {"status": "success", "user": user}
    return {"status": "error", "message": "Invalid credentials"}`,
    refactored: `import bcrypt
from typing import Dict, Any, Optional

def authenticate_user(db_connection, username: str, password: str) -> Optional[Dict[str, Any]]:
    """
    Authenticates user safely using parameterized SQL query and bcrypt password verification.
    """
    # FIX: Parameterized SQL query prevents SQL injection attacks
    query = "SELECT id, username, password_hash, role FROM users WHERE username = %s"
    cursor = db_connection.cursor()
    cursor.execute(query, (username,))
    user = cursor.fetchone()
    
    if not user:
        return None
        
    # FIX: Secure constant-time hash comparison
    if bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
        return {
            "id": user['id'],
            "username": user['username'],
            "role": user['role']
        }
        
    return None`,
    findings: [
      { id: "F1", category: "Security", severity: "CRITICAL", title: "SQL Injection via String Concatenation", line: 3 },
      { id: "F2", category: "Security", severity: "HIGH", title: "Plain-text Password Storage & Comparison", line: 9 },
      { id: "F3", category: "Readability", severity: "LOW", title: "Missing Type Annotations & Docstrings", line: 1 }
    ],
    metrics: { securityScore: 32, performanceScore: 78, readabilityScore: 54, complexity: "High" }
  },
  {
    id: "performance",
    title: "TypeScript N+1 Query & Memory Leak",
    language: "typescript",
    icon: Cpu,
    badgeColor: "amber",
    original: `async function getUserOrders(userIds: string[]) {
  const results = [];
  // CRITICAL: N+1 async loop pattern blocks database event loop
  for (let i = 0; i < userIds.length; i++) {
    const user = await db.user.findUnique({ where: { id: userIds[i] } });
    const orders = await db.order.findMany({ where: { userId: userIds[i] } });
    results.push({ ...user, orders });
  }
  return results;
}`,
    refactored: `interface UserOrderSummary {
  userId: string;
  user: User;
  orders: Order[];
}

async function getUserOrdersBatch(userIds: string[]): Promise<UserOrderSummary[]> {
  if (!userIds || userIds.length === 0) return [];

  // FIX: Batch fetch users and orders in parallel using SQL IN clause
  const [users, orders] = await Promise.all([
    db.user.findMany({ where: { id: { in: userIds } } }),
    db.order.findMany({ where: { userId: { in: userIds } } }),
  ]);

  // FIX: Map orders by userId for O(1) in-memory lookup
  const orderMap = new Map<string, Order[]>();
  for (const order of orders) {
    const existing = orderMap.get(order.userId) || [];
    existing.push(order);
    orderMap.set(order.userId, existing);
  }

  return users.map((user) => ({
    userId: user.id,
    user,
    orders: orderMap.get(user.id) || [],
  }));
}`,
    findings: [
      { id: "F1", category: "Performance", severity: "CRITICAL", title: "N+1 Database Query Loop Pattern", line: 4 },
      { id: "F2", category: "Performance", severity: "MEDIUM", title: "Sequential Await inside Array Loop", line: 5 },
      { id: "F3", category: "Style", severity: "LOW", title: "Array index mutation over modern iterators", line: 4 }
    ],
    metrics: { securityScore: 92, performanceScore: 35, readabilityScore: 60, complexity: "High" }
  },
  {
    id: "modernization",
    title: "Legacy Callback Hell & Error Handling",
    language: "javascript",
    icon: Code2,
    badgeColor: "cyan",
    original: `function fetchUserData(userId, callback) {
  // CRITICAL: Deep callback nesting & swallowed exceptions
  http.get('/api/user/' + userId, function(res) {
    let data = '';
    res.on('data', function(chunk) { data += chunk; });
    res.on('end', function() {
      var user = JSON.parse(data);
      http.get('/api/posts/' + user.id, function(pRes) {
        let pData = '';
        pRes.on('data', function(c) { pData += c; });
        pRes.on('end', function() {
          user.posts = JSON.parse(pData);
          callback(null, user);
        });
      });
    });
  });
}`,
    refactored: `async function fetchUserData(userId) {
  if (!userId) throw new Error("userId argument is required");

  try {
    // FIX: Modern fetch API with Promise.all parallel request execution
    const userRes = await fetch(\`/api/user/\${encodeURIComponent(userId)}\`);
    if (!userRes.ok) throw new Error(\`Failed to fetch user: \${userRes.statusText}\`);
    const user = await userRes.json();

    const postsRes = await fetch(\`/api/posts/\${encodeURIComponent(user.id)}\`);
    if (!postsRes.ok) throw new Error(\`Failed to fetch user posts: \${postsRes.statusText}\`);
    const posts = await postsRes.json();

    return {
      ...user,
      posts,
    };
  } catch (error) {
    console.error('[fetchUserData] Network or JSON parsing error:', error);
    throw error;
  }
}`,
    findings: [
      { id: "F1", category: "Maintainability", severity: "HIGH", title: "Pyramid of Doom Callback Nesting", line: 3 },
      { id: "F2", category: "Reliability", severity: "HIGH", title: "Uncaught JSON.parse Syntax Errors", line: 8 },
      { id: "F3", category: "Security", severity: "MEDIUM", title: "Unescaped URL parameter path injection", line: 3 }
    ],
    metrics: { securityScore: 65, performanceScore: 50, readabilityScore: 40, complexity: "Very High" }
  }
];

// 8 Agent Roles Specification
const AGENT_ROLES = [
  { id: "agent_parser", name: "1. AST & Syntax Parser", model: "FastAPI / TreeSitter", color: "#3b82f6", desc: "Builds Abstract Syntax Tree (AST), validates token syntax, extracts function parameters & imported dependencies." },
  { id: "agent_security", name: "2. OWASP Security Scanner", model: "Gemini 2.5 Pro", color: "#f43f5e", desc: "Scans for SQL injection, hardcoded secrets, XSS, prototype pollution, and unsafe deserialization." },
  { id: "agent_performance", name: "3. Memory & Complexity Profiler", model: "Gemini 2.5 Flash", color: "#f59e0b", desc: "Evaluates Big-O time/space complexity, detects N+1 loops, memory leaks, and unindexed queries." },
  { id: "agent_readability", name: "4. Readability & Style Inspector", model: "Mistral Codestral", color: "#06b6d4", desc: "Checks naming conventions, missing type signatures, dead code, and adherence to clean code rules." },
  { id: "agent_refactoring", name: "5. AST Refactoring Engine", model: "Gemini 2.5 Pro", color: "#a855f7", desc: "Synthesizes modern, idiomatic, bug-fixed refactoring code matching your codebase style." },
  { id: "agent_validator", name: "6. AST Code Validator", model: "Python ast / Node parser", color: "#10b981", desc: "Compiles refactored code against language AST parser to guarantee 100% executable syntax." },
  { id: "agent_rag", name: "7. Vector RAG Enhancer", model: "Gemini Embeddings + MongoDB", color: "#6366f1", desc: "Queries MongoDB Atlas Vector Search to pull codebase context, utility helpers, and project rules." },
  { id: "agent_summarizer", name: "8. Executive Summary Synthesizer", model: "Gemini 2.5 Flash", color: "#ec4899", desc: "Consolidates all 8 agent findings into an executive report with Markdown export capabilities." }
];

export default function LandingPage({ onLaunchStudio }: LandingPageProps) {
  const [activeScenarioId, setActiveScenarioId] = useState<string>("security");
  const [selectedAgentId, setSelectedAgentId] = useState<string>("agent_security");
  const [copiedCode, setCopiedCode] = useState<boolean>(false);
  const [billingCycle, setBillingCycle] = useState<"monthly" | "yearly">("yearly");
  const [openFaq, setOpenFaq] = useState<number | null>(0);

  // Premium Modal State
  const [premiumModalPlan, setPremiumModalPlan] = useState<"pro" | "enterprise" | null>(null);
  const [modalSubmitted, setModalSubmitted] = useState<boolean>(false);
  const [upgradeEmail, setUpgradeEmail] = useState<string>("");
  const [upgradeName, setUpgradeName] = useState<string>("");

  const handleOpenModal = (plan: "pro" | "enterprise") => {
    setPremiumModalPlan(plan);
    setModalSubmitted(false);
  };

  const handleCloseModal = () => {
    setPremiumModalPlan(null);
    setModalSubmitted(false);
  };

  const handleModalFormSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setModalSubmitted(true);
  };

  // Simulation state for sandbox demo
  const [isSimulating, setIsSimulating] = useState<boolean>(false);
  const [simulationStep, setSimulationStep] = useState<number>(0);
  const [simulationComplete, setSimulationComplete] = useState<boolean>(true);

  const activeScenario = SAMPLE_SCENARIOS.find(s => s.id === activeScenarioId) || SAMPLE_SCENARIOS[0];
  const selectedAgent = AGENT_ROLES.find(a => a.id === selectedAgentId) || AGENT_ROLES[1];

  const handleRunSimulation = () => {
    setIsSimulating(true);
    setSimulationComplete(false);
    setSimulationStep(1);

    const interval = setInterval(() => {
      setSimulationStep((prev) => {
        if (prev >= 8) {
          clearInterval(interval);
          setIsSimulating(false);
          setSimulationComplete(true);
          return 8;
        }
        return prev + 1;
      });
    }, 400);
  };

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedCode(true);
    setTimeout(() => setCopiedCode(false), 2000);
  };

  return (
    <div className="landing-wrapper fade-in">
      
      {/* HERO SECTION */}
      <section className="hero-section">
        <div className="hero-glow-bg"></div>
        <div className="hero-container">
          
          {/* Release Announcement Pill */}
          <div className="announcement-pill" onClick={onLaunchStudio}>
            <span className="pill-sparkle">🚀</span>
            <span className="pill-text">CodePilot 2.0 Released with Gemini 2.5 Pro & LangGraph Parallel Graphing</span>
            <ArrowRight className="w-3.5 h-3.5 ml-1 inline text-indigo-400" />
          </div>

          {/* Main Hero Headline */}
          <h1 className="hero-title">
            Enterprise-Grade AI Code Review & <br className="hidden md:inline" />
            <span className="text-gradient-purple-cyan">Autonomous Refactoring Engine</span>
          </h1>

          <p className="hero-subtitle">
            Deploy an autonomous 8-agent AI graph operating in parallel to scan codebases, audit security vulnerabilities, 
            validate syntax trees (AST), assess memory complexity, and deliver instant production refactoring.
          </p>

          {/* Hero Action Buttons */}
          <div className="hero-actions">
            <button type="button" className="btn-hero-primary" onClick={onLaunchStudio}>
              <Sparkles className="w-5 h-5 mr-2" />
              Launch Studio Workspace
            </button>
            <a href="#sandbox" className="btn-hero-secondary">
              <Play className="w-4 h-4 mr-2 text-cyan-400" />
              Explore Live Demo
            </a>
          </div>

          {/* Tech Badges Row */}
          <div className="hero-tech-badges">
            <span className="tech-chip"><Zap className="w-3.5 h-3.5 text-amber-400 mr-1" /> LangGraph Workflow</span>
            <span className="tech-chip"><Cpu className="w-3.5 h-3.5 text-indigo-400 mr-1" /> Gemini 2.5 Pro + Flash</span>
            <span className="tech-chip"><ShieldCheck className="w-3.5 h-3.5 text-emerald-400 mr-1" /> AST Syntax Validator</span>
            <span className="tech-chip"><Database className="w-3.5 h-3.5 text-purple-400 mr-1" /> MongoDB Atlas Vector RAG</span>
          </div>

          {/* HERO CODE PREVIEW TERMINAL MOCKUP */}
          <div className="hero-mockup-card">
            <div className="terminal-header">
              <div className="terminal-dots">
                <span className="dot red"></span>
                <span className="dot yellow"></span>
                <span className="dot green"></span>
              </div>
              <div className="terminal-title">
                <Terminal className="w-3.5 h-3.5 inline mr-1.5 text-indigo-400" />
                codepilot-graph-engine v2.0 • Live Interactive Review Preview
              </div>
              <div className="scenario-selector-tabs">
                {SAMPLE_SCENARIOS.map((scenario) => {
                  const Icon = scenario.icon;
                  return (
                    <button
                      key={scenario.id}
                      type="button"
                      className={`tab-btn ${activeScenarioId === scenario.id ? "active" : ""}`}
                      onClick={() => setActiveScenarioId(scenario.id)}
                    >
                      <Icon className="w-3.5 h-3.5 mr-1" />
                      {scenario.title.split(" ")[0]}
                    </button>
                  );
                })}
              </div>
            </div>

            <div className="terminal-body">
              <div className="mockup-grid">
                
                {/* Left Side: Original Code with Vulnerability Markers */}
                <div className="code-pane pane-original">
                  <div className="pane-header">
                    <span className="badge badge-danger">
                      <ShieldCheck className="w-3 h-3 mr-1" /> Original (3 Issues Detected)
                    </span>
                    <span className="lang-tag">{activeScenario.language}</span>
                  </div>
                  <pre className="code-block">
                    <code>{activeScenario.original}</code>
                  </pre>
                  
                  {/* Inline Findings Alert List */}
                  <div className="findings-inline-list">
                    {activeScenario.findings.map((f) => (
                      <div key={f.id} className="finding-chip-mini">
                        <span className={`finding-severity ${f.severity.toLowerCase()}`}>{f.severity}</span>
                        <span className="finding-title">{f.title} (Line {f.line})</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Right Side: AST-Validated Refactored Code */}
                <div className="code-pane pane-refactored">
                  <div className="pane-header">
                    <span className="badge badge-success">
                      <CheckCircle2 className="w-3 h-3 mr-1" /> AI Refactored (100% AST Validated)
                    </span>
                    <button 
                      type="button" 
                      className="btn-icon-copy" 
                      onClick={() => handleCopy(activeScenario.refactored)}
                      title="Copy code"
                    >
                      {copiedCode ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                    </button>
                  </div>
                  <pre className="code-block highlighted">
                    <code>{activeScenario.refactored}</code>
                  </pre>
                  
                  <div className="refactor-highlights-bar">
                    <span className="highlight-pill success">✨ Parameterized SQL</span>
                    <span className="highlight-pill success">🔒 Constant-time Bcrypt Hash</span>
                    <span className="highlight-pill info">⚡ Strict Type Safety</span>
                  </div>
                </div>

              </div>
            </div>
          </div>

        </div>
      </section>

      {/* METRICS & KEY NUMBERS BAR */}
      <section className="metrics-banner">
        <div className="metrics-container">
          <div className="metric-stat-card">
            <div className="stat-value text-gradient-indigo">10x</div>
            <div className="stat-label">Faster Audit Velocity</div>
            <div className="stat-sub">Parallel multi-agent execution vs manual code reviews</div>
          </div>
          <div className="metric-stat-card">
            <div className="stat-value text-gradient-emerald">99.4%</div>
            <div className="stat-label">AST Refactor Accuracy</div>
            <div className="stat-sub">Validated against compiler syntax trees prior to export</div>
          </div>
          <div className="metric-stat-card">
            <div className="stat-value text-gradient-purple">8 Agents</div>
            <div className="stat-label">Specialized AI Roles</div>
            <div className="stat-sub">LangGraph parallel graph nodes for security & logic</div>
          </div>
          <div className="metric-stat-card">
            <div className="stat-value text-gradient-cyan">&lt; 3.2s</div>
            <div className="stat-label">Average Execution Latency</div>
            <div className="stat-sub">Dynamic smart router between Gemini 2.5 & Mistral</div>
          </div>
        </div>
      </section>

      {/* FEATURE SUITE GRID SECTION */}
      <section id="features" className="features-section">
        <div className="section-container">
          <div className="section-header center">
            <div className="section-pill"><Sparkles className="w-3.5 h-3.5 mr-1" /> Core Engine Capabilities</div>
            <h2 className="section-title">Built for Modern Developer Teams</h2>
            <p className="section-subtitle">
              Unlike generic chat assistants, CodePilot AI combines graph-based orchestration with compiler AST tree validation to ensure reliable code refactoring.
            </p>
          </div>

          <div className="features-grid">
            <div className="feature-card">
              <div className="feature-icon-wrapper bg-indigo-glow">
                <Layers className="w-6 h-6 text-indigo-400" />
              </div>
              <h3 className="feature-title">LangGraph Multi-Agent Engine</h3>
              <p className="feature-desc">
                Orchestrates 8 specialized agents running in parallel graph branches, eliminating single-prompt hallucination limits.
              </p>
              <ul className="feature-list">
                <li><CheckCircle2 className="w-4 h-4 text-emerald-400 mr-2" /> Parallel security, performance, & style branches</li>
                <li><CheckCircle2 className="w-4 h-4 text-emerald-400 mr-2" /> Conditional state retries on syntax failure</li>
              </ul>
            </div>

            <div className="feature-card">
              <div className="feature-icon-wrapper bg-emerald-glow">
                <ShieldCheck className="w-6 h-6 text-emerald-400" />
              </div>
              <h3 className="feature-title">Zero-Hallucination AST Validation</h3>
              <p className="feature-desc">
                Refactored output is passed through language AST compilers to verify syntactical correctness before rendering diffs.
              </p>
              <ul className="feature-list">
                <li><CheckCircle2 className="w-4 h-4 text-emerald-400 mr-2" /> AST syntax tree validation guarantee</li>
                <li><CheckCircle2 className="w-4 h-4 text-emerald-400 mr-2" /> One-click apply refactored code into editor</li>
              </ul>
            </div>

            <div className="feature-card">
              <div className="feature-icon-wrapper bg-cyan-glow">
                <Cpu className="w-6 h-6 text-cyan-400" />
              </div>
              <h3 className="feature-title">Gemini 2.5 + Mistral Smart Router</h3>
              <p className="feature-desc">
                Routes high-reasoning tasks (security & refactoring) to Gemini 2.5 Pro and rapid linting to Gemini 2.5 Flash / Mistral.
              </p>
              <ul className="feature-list">
                <li><CheckCircle2 className="w-4 h-4 text-emerald-400 mr-2" /> Automatic fallback on rate-limits</li>
                <li><CheckCircle2 className="w-4 h-4 text-emerald-400 mr-2" /> Sub-second latency for quick reviews</li>
              </ul>
            </div>

            <div className="feature-card">
              <div className="feature-icon-wrapper bg-purple-glow">
                <Database className="w-6 h-6 text-purple-400" />
              </div>
              <h3 className="feature-title">MongoDB Atlas Vector RAG</h3>
              <p className="feature-desc">
                Vectorizes repository documentation and architecture rules using Gemini Embeddings (`text-embedding-004`) for deep context.
              </p>
              <ul className="feature-list">
                <li><CheckCircle2 className="w-4 h-4 text-emerald-400 mr-2" /> Codebase context awareness</li>
                <li><CheckCircle2 className="w-4 h-4 text-emerald-400 mr-2" /> Custom team coding style rulesets</li>
              </ul>
            </div>

            <div className="feature-card">
              <div className="feature-icon-wrapper bg-amber-glow">
                <GitCompare className="w-6 h-6 text-amber-400" />
              </div>
              <h3 className="feature-title">Interactive Findings Explorer</h3>
              <p className="feature-desc">
                Filter and inspect findings across Security, Logic, Performance, and Readability with inline line markers and impact scores.
              </p>
              <ul className="feature-list">
                <li><CheckCircle2 className="w-4 h-4 text-emerald-400 mr-2" /> Severity tags (Critical, High, Medium, Low)</li>
                <li><CheckCircle2 className="w-4 h-4 text-emerald-400 mr-2" /> Side-by-side split & unified diff views</li>
              </ul>
            </div>

            <div className="feature-card">
              <div className="feature-icon-wrapper bg-rose-glow">
                <FileText className="w-6 h-6 text-rose-400" />
              </div>
              <h3 className="feature-title">Enterprise Markdown Reports</h3>
              <p className="feature-desc">
                Export comprehensive audit summary reports formatted for GitHub Pull Request reviews, Jira attachments, and security archives.
              </p>
              <ul className="feature-list">
                <li><CheckCircle2 className="w-4 h-4 text-emerald-400 mr-2" /> Downloadable `.md` audit reports</li>
                <li><CheckCircle2 className="w-4 h-4 text-emerald-400 mr-2" /> Executive metrics & score breakdowns</li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* 8-AGENT ARCHITECTURE VISUALIZER SECTION */}
      <section id="architecture" className="architecture-section">
        <div className="section-container">
          <div className="section-header center">
            <div className="section-pill"><Layers className="w-3.5 h-3.5 mr-1" /> Multi-Agent Graph Engine</div>
            <h2 className="section-title">Inside the 8-Agent Parallel Graph</h2>
            <p className="section-subtitle">
              Click on any agent node below to inspect its specialized role, execution pipeline, and assigned LLM provider.
            </p>
          </div>

          <div className="architecture-interactive-grid">
            
            {/* Agent Selection Grid */}
            <div className="agent-nodes-column">
              {AGENT_ROLES.map((agent) => {
                const isSelected = selectedAgentId === agent.id;
                return (
                  <div
                    key={agent.id}
                    className={`agent-node-card ${isSelected ? "selected" : ""}`}
                    onClick={() => setSelectedAgentId(agent.id)}
                    style={{ borderLeftColor: agent.color }}
                  >
                    <div className="agent-node-header">
                      <span className="agent-node-name">{agent.name}</span>
                      <span className="agent-node-model">{agent.model}</span>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Selected Agent Details Panel */}
            <div className="agent-details-card" style={{ borderColor: `${selectedAgent.color}40` }}>
              <div className="agent-details-header">
                <div className="agent-badge-title" style={{ backgroundColor: `${selectedAgent.color}20`, color: selectedAgent.color, border: `1px solid ${selectedAgent.color}50` }}>
                  {selectedAgent.name}
                </div>
                <span className="agent-model-chip"><Cpu className="w-3.5 h-3.5 mr-1" /> Router: {selectedAgent.model}</span>
              </div>

              <div className="agent-body-desc">
                <h4 className="label-heading">Agent Specification & Execution Role:</h4>
                <p className="desc-text">{selectedAgent.desc}</p>

                <div className="agent-pipeline-box">
                  <h4 className="label-heading">LangGraph Execution Flow:</h4>
                  <div className="pipeline-steps-flow">
                    <div className="flow-step">
                      <span className="step-num">1</span>
                      <span className="step-text">Receive ReviewState</span>
                    </div>
                    <div className="flow-arrow">→</div>
                    <div className="flow-step active" style={{ borderColor: selectedAgent.color }}>
                      <span className="step-num">2</span>
                      <span className="step-text">Parallel Node Execution</span>
                    </div>
                    <div className="flow-arrow">→</div>
                    <div className="flow-step">
                      <span className="step-num">3</span>
                      <span className="step-text">Synthesize State</span>
                    </div>
                  </div>
                </div>

                <div className="agent-metrics-row">
                  <div className="mini-metric">
                    <span className="m-label">Execution Mode</span>
                    <span className="m-val text-emerald-400">Parallel Graph</span>
                  </div>
                  <div className="mini-metric">
                    <span className="m-label">Validation Boundary</span>
                    <span className="m-val text-indigo-400">Pydantic v2 Schema</span>
                  </div>
                  <div className="mini-metric">
                    <span className="m-label">Fallback Policy</span>
                    <span className="m-val text-amber-400">Mistral Retry Loop</span>
                  </div>
                </div>
              </div>
            </div>

          </div>
        </div>
      </section>

      {/* LIVE INTERACTIVE DEMO SANDBOX */}
      <section id="sandbox" className="sandbox-section">
        <div className="section-container">
          <div className="section-header center">
            <div className="section-pill"><Terminal className="w-3.5 h-3.5 mr-1" /> Interactive Sandbox</div>
            <h2 className="section-title">Test Drive CodePilot AI Live</h2>
            <p className="section-subtitle">
              Simulate an 8-agent parallel review right here. Watch how findings are discovered and refactored in real time.
            </p>
          </div>

          <div className="sandbox-card">
            
            {/* Control Bar */}
            <div className="sandbox-controls">
              <div className="control-left">
                <span className="control-label">Preset Scenario:</span>
                <div className="scenario-btn-group">
                  {SAMPLE_SCENARIOS.map((sc) => (
                    <button
                      key={sc.id}
                      type="button"
                      className={`scenario-btn ${activeScenarioId === sc.id ? "active" : ""}`}
                      onClick={() => {
                        setActiveScenarioId(sc.id);
                        setSimulationComplete(true);
                      }}
                    >
                      {sc.title}
                    </button>
                  ))}
                </div>
              </div>

              <button
                type="button"
                className={`btn-run-simulation ${isSimulating ? "loading" : ""}`}
                onClick={handleRunSimulation}
                disabled={isSimulating}
              >
                {isSimulating ? (
                  <>
                    <RefreshCw className="w-4 h-4 mr-2 animate-spin text-white" />
                    Running Agent Graph ({simulationStep}/8)...
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4 mr-2 fill-current" />
                    Simulate 8-Agent Graph Audit
                  </>
                )}
              </button>
            </div>

            {/* Simulation Progress Bar (visible during active simulation) */}
            {isSimulating && (
              <div className="simulation-progress-container fade-in">
                <div className="progress-label">
                  <span>Graph Node {simulationStep} of 8: Executing {AGENT_ROLES[simulationStep - 1]?.name}</span>
                  <span className="text-cyan-400">{Math.round((simulationStep / 8) * 100)}%</span>
                </div>
                <div className="progress-track">
                  <div 
                    className="progress-fill" 
                    style={{ width: `${(simulationStep / 8) * 100}%` }}
                  ></div>
                </div>
              </div>
            )}

            {/* Sandbox Results Display */}
            <div className="sandbox-results-grid">
              
              {/* Left Column: Input Code */}
              <div className="sandbox-col">
                <div className="col-header">
                  <span className="title"><Code2 className="w-4 h-4 text-indigo-400 inline mr-1" /> Source Snippet</span>
                  <span className="badge badge-amber">Raw Input</span>
                </div>
                <pre className="sandbox-code">
                  <code>{activeScenario.original}</code>
                </pre>
              </div>

              {/* Right Column: AI Output */}
              <div className="sandbox-col">
                <div className="col-header">
                  <span className="title"><CheckCircle2 className="w-4 h-4 text-emerald-400 inline mr-1" /> Refactored Code</span>
                  <span className="badge badge-success">AST Compliant</span>
                </div>
                <pre className="sandbox-code refactored">
                  <code>{activeScenario.refactored}</code>
                </pre>
              </div>

            </div>

            {/* Sandbox Audit Score Cards */}
            <div className="sandbox-score-cards">
              <div className="score-card">
                <span className="score-label">Security Audit Score</span>
                <span className={`score-value ${activeScenario.metrics.securityScore < 50 ? "red" : "green"}`}>
                  {activeScenario.metrics.securityScore} / 100 → <span className="text-emerald-400">98 / 100</span>
                </span>
              </div>
              <div className="score-card">
                <span className="score-label">Performance Rating</span>
                <span className="score-value green">
                  {activeScenario.metrics.performanceScore} / 100 → <span className="text-emerald-400">95 / 100</span>
                </span>
              </div>
              <div className="score-card">
                <span className="score-label">Readability Index</span>
                <span className="score-value cyan">
                  {activeScenario.metrics.readabilityScore} / 100 → <span className="text-emerald-400">96 / 100</span>
                </span>
              </div>
            </div>

          </div>
        </div>
      </section>

      {/* BENCHMARKS & COMPETITIVE COMPARISON SECTION */}
      <section id="benchmarks" className="benchmarks-section">
        <div className="section-container">
          <div className="section-header center">
            <div className="section-pill"><BarChart3 className="w-3.5 h-3.5 mr-1" /> Competitive Matrix</div>
            <h2 className="section-title">Why CodePilot AI Outperforms</h2>
            <p className="section-subtitle">
              Comparing autonomous multi-agent graphs against legacy static linters and unconstrained chat models.
            </p>
          </div>

          <div className="comparison-table-wrapper">
            <table className="comparison-table">
              <thead>
                <tr>
                  <th className="feature-col">Architectural Capability</th>
                  <th className="highlight-col">⚡ CodePilot AI</th>
                  <th>Traditional Linters (ESLint/Pylint)</th>
                  <th>Generic Chat LLMs (ChatGPT / Claude)</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td className="feature-name">Parallel Graph Orchestration</td>
                  <td className="highlight-cell"><CheckCircle className="w-5 h-5 text-emerald-400 inline mr-1" /> 8 Autonomous Agents</td>
                  <td><XCircle className="w-5 h-5 text-rose-500 inline mr-1" /> Single Rule Check</td>
                  <td><XCircle className="w-5 h-5 text-rose-500 inline mr-1" /> Single Prompt Window</td>
                </tr>
                <tr>
                  <td className="feature-name">AST Compiler Syntax Guarantee</td>
                  <td className="highlight-cell"><CheckCircle className="w-5 h-5 text-emerald-400 inline mr-1" /> 100% Compiler Verified</td>
                  <td><CheckCircle className="w-5 h-5 text-emerald-400 inline mr-1" /> AST Rule Match</td>
                  <td><XCircle className="w-5 h-5 text-rose-500 inline mr-1" /> Risk of Hallucinations</td>
                </tr>
                <tr>
                  <td className="feature-name">OWASP Security Audit Depth</td>
                  <td className="highlight-cell"><CheckCircle className="w-5 h-5 text-emerald-400 inline mr-1" /> Deep Vulnerability Scans</td>
                  <td><XCircle className="w-5 h-5 text-rose-500 inline mr-1" /> Regex Patterns Only</td>
                  <td><CheckCircle className="w-5 h-5 text-amber-400 inline mr-1" /> Shallow Pattern Search</td>
                </tr>
                <tr>
                  <td className="feature-name">MongoDB Vector RAG Context</td>
                  <td className="highlight-cell"><CheckCircle className="w-5 h-5 text-emerald-400 inline mr-1" /> Gemini Embeddings Integration</td>
                  <td><XCircle className="w-5 h-5 text-rose-500 inline mr-1" /> No Context</td>
                  <td><XCircle className="w-5 h-5 text-rose-500 inline mr-1" /> Requires Manual Paste</td>
                </tr>
                <tr>
                  <td className="feature-name">One-Click Markdown PR Export</td>
                  <td className="highlight-cell"><CheckCircle className="w-5 h-5 text-emerald-400 inline mr-1" /> Native `.md` Download</td>
                  <td><XCircle className="w-5 h-5 text-rose-500 inline mr-1" /> Plain Console Output</td>
                  <td><CheckCircle className="w-5 h-5 text-amber-400 inline mr-1" /> Copy-Paste Required</td>
                </tr>
                <tr>
                  <td className="feature-name">Self-Correction State Retries</td>
                  <td className="highlight-cell"><CheckCircle className="w-5 h-5 text-emerald-400 inline mr-1" /> Automatic Retries on Errors</td>
                  <td><XCircle className="w-5 h-5 text-rose-500 inline mr-1" /> N/A</td>
                  <td><XCircle className="w-5 h-5 text-rose-500 inline mr-1" /> Manual Prompting</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* PRICING & PLANS SECTION */}
      <section id="pricing" className="pricing-section">
        <div className="section-container">
          <div className="section-header center">
            <div className="section-pill"><Sliders className="w-3.5 h-3.5 mr-1" /> Transparent Pricing</div>
            <h2 className="section-title">Flexible Plans for Every Developer</h2>
            <p className="section-subtitle">
              Start free with standard reviews or upgrade to Pro for deep multi-agent graph mode & RAG context.
            </p>

            {/* Monthly / Annual Toggle */}
            <div className="billing-toggle">
              <button
                type="button"
                className={`toggle-tab ${billingCycle === "monthly" ? "active" : ""}`}
                onClick={() => setBillingCycle("monthly")}
              >
                Monthly Billing
              </button>
              <button
                type="button"
                className={`toggle-tab ${billingCycle === "yearly" ? "active" : ""}`}
                onClick={() => setBillingCycle("yearly")}
              >
                Yearly Billing <span className="discount-tag">Save 20%</span>
              </button>
            </div>
          </div>

          <div className="pricing-cards-grid">
            
            {/* Free Developer Plan */}
            <div className="pricing-card">
              <div className="plan-header">
                <h3 className="plan-name">Developer</h3>
                <p className="plan-desc">Perfect for individual developers and quick code audits.</p>
                <div className="plan-price">
                  <span className="price-num">$0</span>
                  <span className="price-period">/ forever free</span>
                </div>
              </div>
              <ul className="plan-features">
                <li><Check className="w-4 h-4 text-emerald-400 mr-2 inline" /> 50 Code Reviews / month</li>
                <li><Check className="w-4 h-4 text-emerald-400 mr-2 inline" /> Quick Review Mode (Sub-3s)</li>
                <li><Check className="w-4 h-4 text-emerald-400 mr-2 inline" /> Basic Security & Style Checks</li>
                <li><Check className="w-4 h-4 text-emerald-400 mr-2 inline" /> Python & TypeScript support</li>
              </ul>
              <button type="button" className="btn-plan-outline" onClick={onLaunchStudio}>
                Get Started Free
              </button>
            </div>

            {/* Pro Plan (Featured) */}
            <div className="pricing-card featured-pro">
              <div className="popular-badge">MOST POPULAR</div>
              <div className="plan-header">
                <h3 className="plan-name text-gradient-purple-cyan">Pro Studio</h3>
                <p className="plan-desc">For senior engineers, tech leads, and fast-moving teams.</p>
                <div className="plan-price">
                  <span className="price-num">{billingCycle === "yearly" ? "$24" : "$29"}</span>
                  <span className="price-period">/ user / month</span>
                </div>
              </div>
              <ul className="plan-features">
                <li><Check className="w-4 h-4 text-emerald-400 mr-2 inline" /> Unlimited Code Reviews</li>
                <li><Check className="w-4 h-4 text-emerald-400 mr-2 inline" /> Deep 8-Agent LangGraph Mode</li>
                <li><Check className="w-4 h-4 text-emerald-400 mr-2 inline" /> AST Syntax Tree Validation Guarantee</li>
                <li><Check className="w-4 h-4 text-emerald-400 mr-2 inline" /> Markdown Export for Pull Requests</li>
                <li><Check className="w-4 h-4 text-emerald-400 mr-2 inline" /> Gemini 2.5 Pro Priority Router</li>
                <li><Check className="w-4 h-4 text-emerald-400 mr-2 inline" /> All 12+ programming languages</li>
              </ul>
              <button type="button" className="btn-plan-glow" onClick={() => handleOpenModal("pro")}>
                Launch Pro Studio Free Trial
              </button>
            </div>

            {/* Enterprise Plan */}
            <div className="pricing-card">
              <div className="plan-header">
                <h3 className="plan-name">Enterprise</h3>
                <p className="plan-desc">Dedicated cluster deployment with custom RAG vector search.</p>
                <div className="plan-price">
                  <span className="price-num">Custom</span>
                  <span className="price-period">/ organization</span>
                </div>
              </div>
              <ul className="plan-features">
                <li><Check className="w-4 h-4 text-emerald-400 mr-2 inline" /> Dedicated MongoDB Vector RAG</li>
                <li><Check className="w-4 h-4 text-emerald-400 mr-2 inline" /> Custom Organization Style Rules</li>
                <li><Check className="w-4 h-4 text-emerald-400 mr-2 inline" /> Private VPC / On-Prem Deployment</li>
                <li><Check className="w-4 h-4 text-emerald-400 mr-2 inline" /> SOC2 Compliance & 99.99% SLA</li>
                <li><Check className="w-4 h-4 text-emerald-400 mr-2 inline" /> Dedicated Support Engineer</li>
              </ul>
              <button type="button" className="btn-plan-outline" onClick={() => handleOpenModal("enterprise")}>
                Contact Sales
              </button>
            </div>

          </div>
        </div>
      </section>

      {/* INTERACTIVE FAQ ACCORDION SECTION */}
      <section id="faq" className="faq-section">
        <div className="section-container">
          <div className="section-header center">
            <div className="section-pill"><HelpCircle className="w-3.5 h-3.5 mr-1" /> Questions & Answers</div>
            <h2 className="section-title">Frequently Asked Questions</h2>
          </div>

          <div className="faq-accordion-list">
            {[
              {
                q: "How does CodePilot AI prevent hallucinated broken code in refactorings?",
                a: "Unlike standard chat models, CodePilot AI includes a dedicated AST Code Validator agent. All proposed refactored snippets are executed against abstract syntax tree compilers (like Python's `ast` module or Tree-Sitter) before rendering. If code fails compilation, the graph automatically triggers a retry loop."
              },
              {
                q: "What AI models power the 8-agent review engine?",
                a: "We leverage Google Gemini 2.5 Pro as our primary high-reasoning engine for security auditing and refactoring, coupled with Gemini 2.5 Flash for rapid summary generation, and Mistral Codestral as an automated secondary fallback router."
              },
              {
                q: "Can I connect CodePilot AI to my backend server?",
                a: "Yes! CodePilot AI frontend communicates seamlessly via REST API with a FastAPI backend server hosted at `http://localhost:8000` or custom cloud deployment endpoints."
              },
              {
                q: "What programming languages are supported?",
                a: "CodePilot AI supports Python, TypeScript, JavaScript, Go, Rust, Java, C++, C#, PHP, Ruby, SQL, and HTML/CSS. Auto-detection is built in."
              },
              {
                q: "Is my source code stored or used to train public models?",
                a: "No. Your code is processed statelessly in transient memory during graph execution. No code submitted to CodePilot AI is ever sold or used for model training."
              }
            ].map((faq, idx) => {
              const isOpen = openFaq === idx;
              return (
                <div key={idx} className={`faq-item ${isOpen ? "open" : ""}`} onClick={() => setOpenFaq(isOpen ? null : idx)}>
                  <div className="faq-question">
                    <span>{faq.q}</span>
                    {isOpen ? <ChevronUp className="w-5 h-5 text-indigo-400" /> : <ChevronDown className="w-5 h-5 text-slate-400" />}
                  </div>
                  {isOpen && (
                    <div className="faq-answer fade-in">
                      <p>{faq.a}</p>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* FINAL HIGH-IMPACT CTA BANNER */}
      <section className="final-cta-section">
        <div className="cta-card-glow">
          <div className="cta-content">
            <h2 className="cta-title">Start Auditing Code with 8 AI Agents Today</h2>
            <p className="cta-desc">
              Transform your code review workflow. Detect bugs instantly, enforce security standards, and export clean refactored code.
            </p>
            <div className="cta-buttons">
              <button type="button" className="btn-cta-launch" onClick={() => handleOpenModal("pro")}>
                <Sparkles className="w-5 h-5 mr-2" /> Upgrade to Pro Studio
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* FOOTER */}
      <footer className="landing-footer">
        <div className="footer-container">
          <div className="footer-top">
            <div className="footer-brand">
              <div className="logo-container">
                <div className="logo-icon">⚡</div>
                <span className="logo-text">CodePilot AI</span>
              </div>
              <p className="footer-tagline">
                Enterprise Multi-Agent Code Review & Autonomous Refactoring Engine.
              </p>
              <div className="footer-tech-stack">
                <span className="badge badge-indigo">FastAPI</span>
                <span className="badge badge-purple">LangGraph</span>
                <span className="badge badge-cyan">Gemini 2.5</span>
                <span className="badge badge-success">Next.js 14</span>
              </div>
            </div>

            <div className="footer-links-grid">
              <div className="link-col">
                <h4 className="col-title">Product</h4>
                <a href="#features">Features</a>
                <a href="#architecture">8-Agent Engine</a>
                <a href="#sandbox">Live Demo Sandbox</a>
                <a href="#benchmarks">Benchmarks</a>
                <a href="#pricing">Pricing</a>
              </div>
              <div className="link-col">
                <h4 className="col-title">Architecture</h4>
                <a href="#architecture">LangGraph Parallel State</a>
                <a href="#architecture">AST Validator Engine</a>
                <a href="#architecture">Gemini Embeddings RAG</a>
                <a href="#architecture">LLM Router & Failover</a>
              </div>
              <div className="link-col">
                <h4 className="col-title">Developers</h4>
                <a href="http://localhost:8000/docs" target="_blank" rel="noopener noreferrer">FastAPI Swagger Docs</a>
                <a href="http://localhost:8000/health" target="_blank" rel="noopener noreferrer">Backend Health Endpoint</a>
                <a href="#faq">FAQ</a>
              </div>
            </div>
          </div>

          <div className="footer-bottom">
            <p>© {new Date().getFullYear()} CodePilot AI Systems Inc. All rights reserved.</p>
            <div className="status-indicator">
              <span className="status-dot"></span> System Operational • FastAPI v1.0.0
            </div>
          </div>
        </div>
      </footer>

      {/* PREMIUM PLAN UPGRADE MODAL */}
      {premiumModalPlan && (
        <div className="modal-overlay" onClick={handleCloseModal}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <button type="button" className="modal-close-btn" onClick={handleCloseModal} title="Close">
              <X className="w-4 h-4" />
            </button>

            {!modalSubmitted ? (
              <>
                <div className={`modal-header-badge ${premiumModalPlan}`}>
                  <Sparkles className="w-3.5 h-3.5 mr-1" />
                  {premiumModalPlan === "pro" ? "Pro Studio Plan" : "Enterprise Plan"}
                </div>

                <h2 className="modal-title">
                  {premiumModalPlan === "pro" ? "Upgrade to Pro Studio" : "Request Enterprise Access"}
                </h2>
                <p className="modal-subtitle">
                  {premiumModalPlan === "pro" 
                    ? "Start your 14-day free trial. Unlock unlimited 8-agent graph reviews, AST compiler syntax validation, and Gemini 2.5 Pro priority routing."
                    : "Deploy dedicated MongoDB Atlas Vector RAG search, custom team style rulesets, and private VPC hosting for your organization."
                  }
                </p>

                <div className="plan-summary-box">
                  <div>
                    <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", textTransform: "uppercase", fontWeight: 700 }}>
                      {premiumModalPlan === "pro" ? "Selected Tier" : "Organization Tier"}
                    </div>
                    <div style={{ fontWeight: 800, fontSize: "1.1rem", color: "white" }}>
                      {premiumModalPlan === "pro" ? "Pro Studio (14-Day Free Trial)" : "Enterprise Organization"}
                    </div>
                  </div>
                  <div className="plan-summary-price">
                    {premiumModalPlan === "pro" 
                      ? (billingCycle === "yearly" ? "$24/mo" : "$29/mo")
                      : "Custom"
                    }
                  </div>
                </div>

                <ul className="modal-features-list">
                  {premiumModalPlan === "pro" ? (
                    <>
                      <li><CheckCircle2 className="w-4 h-4 text-emerald-400 mr-2 inline" /> Unlimited Code Reviews (Sub-3s Execution)</li>
                      <li><CheckCircle2 className="w-4 h-4 text-emerald-400 mr-2 inline" /> Deep 8-Agent LangGraph Workflow</li>
                      <li><CheckCircle2 className="w-4 h-4 text-emerald-400 mr-2 inline" /> 100% AST Syntax Compiler Validation Guarantee</li>
                      <li><CheckCircle2 className="w-4 h-4 text-emerald-400 mr-2 inline" /> Priority Gemini 2.5 Pro High-Reasoning LLM Router</li>
                    </>
                  ) : (
                    <>
                      <li><CheckCircle2 className="w-4 h-4 text-emerald-400 mr-2 inline" /> Dedicated MongoDB Atlas Vector RAG Context Search</li>
                      <li><CheckCircle2 className="w-4 h-4 text-emerald-400 mr-2 inline" /> Custom Team Coding Style Rules & Guidelines</li>
                      <li><CheckCircle2 className="w-4 h-4 text-emerald-400 mr-2 inline" /> Private VPC / On-Premise Enterprise Deployment</li>
                      <li><CheckCircle2 className="w-4 h-4 text-emerald-400 mr-2 inline" /> 99.99% SLA & Dedicated AI Solutions Engineer</li>
                    </>
                  )}
                </ul>

                <form onSubmit={handleModalFormSubmit}>
                  <div className="modal-form-group">
                    <label className="modal-form-label">Full Name</label>
                    <input
                      type="text"
                      required
                      className="modal-form-input"
                      placeholder="e.g. Alex Rivera"
                      value={upgradeName}
                      onChange={(e) => setUpgradeName(e.target.value)}
                    />
                  </div>

                  <div className="modal-form-group">
                    <label className="modal-form-label">Work Email Address</label>
                    <input
                      type="email"
                      required
                      className="modal-form-input"
                      placeholder="e.g. alex@company.com"
                      value={upgradeEmail}
                      onChange={(e) => setUpgradeEmail(e.target.value)}
                    />
                  </div>

                  <button type="submit" className="btn-modal-submit">
                    <Sparkles className="w-4 h-4" />
                    {premiumModalPlan === "pro" ? "Activate 14-Day Free Trial" : "Submit Enterprise Request"}
                  </button>
                </form>
              </>
            ) : (
              <div className="success-card fade-in">
                <div className="success-icon-wrapper">
                  <Check className="w-8 h-8 text-emerald-400" />
                </div>
                <h2 className="modal-title">🎉 Premium Access Requested!</h2>
                <p className="modal-subtitle" style={{ marginBottom: "2rem" }}>
                  Thank you, <strong>{upgradeName || "Developer"}</strong>! We have registered <strong>{upgradeEmail}</strong> for the <strong>{premiumModalPlan === "pro" ? "Pro Studio" : "Enterprise"}</strong> plan.
                </p>

                <button
                  type="button"
                  className="btn-modal-submit"
                  onClick={() => {
                    handleCloseModal();
                    onLaunchStudio();
                  }}
                >
                  <Sparkles className="w-4 h-4" />
                  Proceed to AI Studio Workspace
                </button>
              </div>
            )}
          </div>
        </div>
      )}

    </div>
  );
}
