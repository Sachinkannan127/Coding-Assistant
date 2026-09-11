"use client";

import React, { useState, useEffect } from "react";
import {
  Network,
  ShieldCheck,
  Cpu,
  GitBranch,
  FolderTree,
  BookOpen,
  Terminal,
  Github,
  Play,
  RefreshCw,
  CheckCircle2,
  AlertCircle,
  Copy,
  Check,
  Zap,
  ArrowLeft,
  Sliders,
  Code2,
  Plug,
  PlugZap,
  Key,
  Lock,
  X,
  KeyRound
} from "lucide-react";

interface McpServerInfo {
  id: string;
  name: string;
  description: string;
  category: string;
  status: string;
  tools_count: number;
}

interface McpToolDefinition {
  name: string;
  description: string;
  server_id: string;
  parameters: Array<{
    name: string;
    type: string;
    description: string;
    required: boolean;
    default?: any;
  }>;
}

interface McpConnectorsViewProps {
  onSwitchView: (view: "landing" | "studio" | "compiler" | "mcp") => void;
}

export default function McpConnectorsView({ onSwitchView }: McpConnectorsViewProps) {
  const [servers, setServers] = useState<McpServerInfo[]>([]);
  const [tools, setTools] = useState<McpToolDefinition[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Connection & Token State
  const [connectedServers, setConnectedServers] = useState<Record<string, boolean>>({
    static_analysis: true,
    security_scanner: true,
    filesystem: true,
    doc_fetch: true,
    git: true,
    sandbox: true
  });
  const [serverTokens, setServerTokens] = useState<Record<string, string>>({});

  // Modal State for Connect Token Prompt
  const [activeConnectModalServer, setActiveConnectModalServer] = useState<McpServerInfo | null>(null);
  const [tokenInput, setTokenInput] = useState<string>("");
  const [verifyingToken, setVerifyingToken] = useState<boolean>(false);
  const [modalError, setModalError] = useState<string | null>(null);

  // Playground state
  const [selectedServerId, setSelectedServerId] = useState<string>("static_analysis");
  const [selectedToolName, setSelectedToolName] = useState<string>("calculate_complexity");
  const [toolArgsText, setToolArgsText] = useState<string>(
    JSON.stringify({ code: "def calculate_sum(a, b):\n    if a > 0:\n        return a + b\n    return b" }, null, 2)
  );
  const [executing, setExecuting] = useState<boolean>(false);
  const [execResult, setExecResult] = useState<any | null>(null);
  const [copiedEndpoint, setCopiedEndpoint] = useState<boolean>(false);

  const fetchMcpData = async () => {
    setLoading(true);
    setError(null);
    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8005";
      const [serversRes, toolsRes] = await Promise.all([
        fetch(`${baseUrl}/api/v1/mcp/servers`),
        fetch(`${baseUrl}/api/v1/mcp/tools`)
      ]);

      if (!serversRes.ok || !toolsRes.ok) {
        throw new Error("Failed to fetch MCP Server registry from FastAPI backend.");
      }

      const serversData = await serversRes.json();
      const toolsData = await toolsRes.json();

      setServers(serversData);
      setTools(toolsData);

      // Fetch stored connector states from MongoDB via API
      try {
        const connectorsRes = await fetch(`${baseUrl}/api/connectors`);
        if (connectorsRes.ok) {
          const savedConnectors: Array<{ connector_id: string; status: string; access_token?: string }> = await connectorsRes.json();
          const connMap: Record<string, boolean> = { ...connectedServers };
          const tokenMap: Record<string, string> = {};

          savedConnectors.forEach((c) => {
            connMap[c.connector_id] = c.status === "connected";
            if (c.access_token) {
              tokenMap[c.connector_id] = c.access_token;
            }
          });
          setConnectedServers(connMap);
          setServerTokens(tokenMap);
        }
      } catch (e) {
        console.warn("Could not load stored connectors from database:", e);
      }

      if (serversData.length > 0) {
        const firstServer = serversData[0].id;
        setSelectedServerId(firstServer);
        const matchingTools = toolsData.filter((t: any) => t.server_id === firstServer);
        if (matchingTools.length > 0) {
          setSelectedToolName(matchingTools[0].name);
          updateSampleArgs(matchingTools[0]);
        }
      }
    } catch (err: any) {
      setError(err.message || "Unable to connect to MCP backend endpoint.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMcpData();
  }, []);

  const updateSampleArgs = (tool: McpToolDefinition) => {
    const sampleObj: Record<string, any> = {};
    tool.parameters.forEach((p) => {
      if (p.name === "code") {
        sampleObj.code = "def authenticate_user(user, pwd):\n    if user == 'admin' and pwd == 'secret':\n        return True\n    return False";
      } else if (p.name === "owner") {
        sampleObj.owner = "facebook";
      } else if (p.name === "repo") {
        sampleObj.repo = "react";
      } else if (p.name === "pr_number") {
        sampleObj.pr_number = 28000;
      } else if (p.name === "query") {
        sampleObj.query = "security";
      } else if (p.name === "path" || p.name === "relative_file_path") {
        sampleObj[p.name] = "backend/app/main.py";
      } else if (p.name === "target") {
        sampleObj.target = "python";
      } else if (p.name === "language") {
        sampleObj.language = "python";
      } else {
        sampleObj[p.name] = p.default !== undefined && p.default !== null ? p.default : "sample_value";
      }
    });
    setToolArgsText(JSON.stringify(sampleObj, null, 2));
  };

  const handleServerChange = (serverId: string) => {
    setSelectedServerId(serverId);
    const matchingTools = tools.filter((t) => t.server_id === serverId);
    if (matchingTools.length > 0) {
      setSelectedToolName(matchingTools[0].name);
      updateSampleArgs(matchingTools[0]);
    }
  };

  const handleToolChange = (toolName: string) => {
    setSelectedToolName(toolName);
    const tool = tools.find((t) => t.name === toolName);
    if (tool) {
      updateSampleArgs(tool);
    }
  };

  const handleOpenConnectModal = (server: McpServerInfo) => {
    setActiveConnectModalServer(server);
    setTokenInput(serverTokens[server.id] || "");
    setModalError(null);
  };

  const handleVerifyAndConnect = async () => {
    if (!activeConnectModalServer) return;
    const serverId = activeConnectModalServer.id;

    if (!tokenInput || !tokenInput.trim()) {
      setModalError("Access Token or API Key cannot be empty.");
      return;
    }

    setVerifyingToken(true);
    setModalError(null);

    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8005";

      // If verifying OAuth or GitHub connector, call verify_oauth_token tool endpoint
      if (serverId === "oauth" || serverId === "github") {
        const res = await fetch(`${baseUrl}/api/v1/mcp/call`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            server_id: "oauth",
            tool_name: "verify_oauth_token",
            arguments: {
              access_token: tokenInput.trim(),
              provider: serverId === "github" ? "github" : "github"
            }
          })
        });

        const data = await res.json();
        if (!res.ok || data.status === "error" || (data.result && data.result.valid === false)) {
          throw new Error(data.result?.error || "Invalid or unauthorized OAuth token.");
        }
      } else {
        // Simple token length validation for standard keys
        if (tokenInput.trim().length < 4) {
          throw new Error("Token format is invalid or too short (minimum 4 characters required).");
        }
      }

      // Persist connected state & token to MongoDB via API
      await fetch(`${baseUrl}/api/connectors/connect`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          connector_id: serverId,
          name: activeConnectModalServer.name,
          provider: serverId,
          access_token: tokenInput.trim()
        })
      });

      // Update local state
      setServerTokens((prev) => ({ ...prev, [serverId]: tokenInput.trim() }));
      setConnectedServers((prev) => ({ ...prev, [serverId]: true }));
      setActiveConnectModalServer(null);
    } catch (err: any) {
      setModalError(err.message || "Failed to verify access token.");
    } finally {
      setVerifyingToken(false);
    }
  };

  const handleDisconnectServer = async (serverId: string) => {
    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8005";
      await fetch(`${baseUrl}/api/connectors/disconnect?connector_id=${serverId}`, {
        method: "POST"
      });
    } catch (e) {
      console.warn("Could not sync disconnect with MongoDB:", e);
    }

    setConnectedServers((prev) => ({ ...prev, [serverId]: false }));
    setServerTokens((prev) => {
      const updated = { ...prev };
      delete updated[serverId];
      return updated;
    });
  };


  const handleExecuteMcpTool = async () => {
    setExecuting(true);
    setExecResult(null);

    let parsedArgs = {};
    try {
      parsedArgs = JSON.parse(toolArgsText);
    } catch {
      setExecResult({
        status: "error",
        error: "Invalid JSON parameters payload in tool args input."
      });
      setExecuting(false);
      return;
    }

    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8005";
      const response = await fetch(`${baseUrl}/api/v1/mcp/call`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          server_id: selectedServerId,
          tool_name: selectedToolName,
          arguments: parsedArgs
        })
      });

      const resData = await response.json();
      setExecResult(resData);
    } catch (err: any) {
      setExecResult({
        status: "error",
        error: err.message || "Failed to communicate with MCP Tool router."
      });
    } finally {
      setExecuting(false);
    }
  };

  const getServerIcon = (serverId: string) => {
    switch (serverId) {
      case "static_analysis": return Cpu;
      case "security_scanner": return ShieldCheck;
      case "github": return Github;
      case "filesystem": return FolderTree;
      case "doc_fetch": return BookOpen;
      case "git": return GitBranch;
      case "sandbox": return Terminal;
      case "oauth": return KeyRound;
      default: return Network;
    }
  };

  return (
    <main className="container fade-in" style={{ paddingTop: "2rem", paddingBottom: "4rem" }}>
      
      {/* Header Bar */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "2rem", flexWrap: "wrap", gap: "1rem" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", marginBottom: "0.4rem" }}>
            <button 
              type="button" 
              onClick={() => onSwitchView("studio")}
              className="btn-back-pill"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>Back to Studio</span>
            </button>
            <h1 style={{ fontSize: "1.75rem", fontWeight: 800, letterSpacing: "-0.02em", display: "flex", alignItems: "center", gap: "0.6rem" }}>
              <Network className="w-6 h-6 text-purple-400" /> Model Context Protocol (MCP) Connectors Hub
            </h1>
          </div>
          <p style={{ color: "var(--text-secondary)", fontSize: "0.9rem" }}>
            Standardized MCP 1.0 JSON-RPC Server Architecture & External Tool Connectors Stack for AI Agents & IDE Integrations.
          </p>
        </div>

        <div style={{ display: "flex", gap: "0.5rem" }}>
          <button className="btn btn-secondary btn-sm" onClick={fetchMcpData} disabled={loading}>
            <RefreshCw className={`w-3.5 h-3.5 mr-1 ${loading ? "animate-spin" : ""}`} /> Refresh Registry
          </button>
        </div>
      </div>

      {error && (
        <div style={{ background: "rgba(244, 63, 94, 0.12)", border: "1px solid rgba(244, 63, 94, 0.3)", padding: "1rem 1.25rem", borderRadius: "10px", marginBottom: "1.5rem", color: "#fb7185", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div><strong>⚠️ MCP Connection Error:</strong> {error}</div>
          <button className="btn btn-primary btn-sm" onClick={fetchMcpData}>Retry</button>
        </div>
      )}

      {/* MCP CONNECTOR CARDS GRID */}
      <div style={{ marginBottom: "2.5rem" }}>
        <h2 style={{ fontSize: "1.2rem", fontWeight: 700, marginBottom: "1rem", display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <span>🔌</span> CodePilot MCP Connectors Stack ({servers.length} Active Servers)
        </h2>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(340px, 1fr))", gap: "1.25rem" }}>
          {servers.map((server) => {
            const Icon = getServerIcon(server.id);
            const isSelected = selectedServerId === server.id;
            const isConnected = Boolean(connectedServers[server.id]);

            return (
              <div 
                key={server.id}
                onClick={() => handleServerChange(server.id)}
                style={{
                  background: isSelected ? "rgba(168, 85, 247, 0.12)" : "rgba(15, 23, 42, 0.6)",
                  border: isSelected ? "1px solid rgba(168, 85, 247, 0.5)" : "1px solid rgba(255, 255, 255, 0.08)",
                  borderRadius: "12px",
                  padding: "1.25rem",
                  cursor: "pointer",
                  transition: "all 0.2s ease",
                  boxShadow: isSelected ? "0 8px 24px rgba(168, 85, 247, 0.2)" : "none"
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "0.75rem" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "0.6rem" }}>
                    <div style={{ background: isSelected ? "rgba(168, 85, 247, 0.25)" : "rgba(255, 255, 255, 0.05)", padding: "0.4rem", borderRadius: "8px" }}>
                      <Icon className="w-5 h-5 text-purple-400" />
                    </div>
                    <div>
                      <h3 style={{ fontSize: "1rem", fontWeight: 700, margin: 0 }}>{server.name}</h3>
                      <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "2px" }}>{server.category}</div>
                    </div>
                  </div>

                  {/* CONNECT / DISCONNECT BUTTON */}
                  <div>
                    {isConnected ? (
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDisconnectServer(server.id);
                        }}
                        style={{
                          background: "rgba(34, 197, 94, 0.15)",
                          border: "1px solid rgba(34, 197, 94, 0.4)",
                          color: "#4ade80",
                          padding: "0.3rem 0.75rem",
                          borderRadius: "8px",
                          fontSize: "0.78rem",
                          fontWeight: 600,
                          cursor: "pointer",
                          display: "inline-flex",
                          alignItems: "center",
                          gap: "0.35rem"
                        }}
                        title="Click to Disconnect Connector"
                      >
                        <PlugZap className="w-3.5 h-3.5 text-green-400" /> Connected
                      </button>
                    ) : (
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleOpenConnectModal(server);
                        }}
                        style={{
                          background: "linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)",
                          border: "none",
                          color: "#ffffff",
                          padding: "0.35rem 0.85rem",
                          borderRadius: "8px",
                          fontSize: "0.78rem",
                          fontWeight: 600,
                          cursor: "pointer",
                          display: "inline-flex",
                          alignItems: "center",
                          gap: "0.35rem",
                          boxShadow: "0 4px 12px rgba(99, 102, 241, 0.3)"
                        }}
                      >
                        <Plug className="w-3.5 h-3.5" /> Connect
                      </button>
                    )}
                  </div>
                </div>

                <p style={{ fontSize: "0.82rem", color: "var(--text-secondary)", lineHeight: 1.5, minHeight: "40px", marginBottom: "1rem" }}>
                  {server.description}
                </p>

                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: "0.78rem", borderTop: "1px solid rgba(255, 255, 255, 0.06)", paddingTop: "0.6rem" }}>
                  <span style={{ color: "#a855f7", fontWeight: 600 }}>{server.tools_count} Registered Tools</span>
                  {isConnected ? (
                    <span className="status-badge connected" style={{ fontSize: "0.7rem", padding: "0.15rem 0.5rem" }}>
                      <span className="status-dot"></span> Active
                    </span>
                  ) : (
                    <span className="status-badge offline" style={{ fontSize: "0.7rem", padding: "0.15rem 0.5rem", background: "rgba(148, 163, 184, 0.15)", color: "#94a3b8" }}>
                      Disconnected
                    </span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* INTERACTIVE MCP TOOL TESTER & PLAYGROUND */}
      <div className="card" style={{ border: "1px solid rgba(168, 85, 247, 0.3)", background: "rgba(15, 23, 42, 0.85)", padding: "1.75rem" }}>
        
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1.25rem", flexWrap: "wrap", gap: "1rem" }}>
          <div>
            <h2 style={{ fontSize: "1.2rem", fontWeight: 700, margin: 0, display: "flex", alignItems: "center", gap: "0.5rem" }}>
              <span>🧪</span> MCP Tool Execution Playground & Testing Suite
            </h2>
            <p style={{ fontSize: "0.82rem", color: "var(--text-secondary)", margin: 0, marginTop: "2px" }}>
              Select a connected server connector and test tool execution parameters interactively.
            </p>
          </div>
        </div>

        {/* Server & Tool Selection Controls */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.25rem", marginBottom: "1.5rem" }}>
          <div>
            <label style={{ display: "block", fontSize: "0.8rem", fontWeight: 600, color: "var(--text-muted)", marginBottom: "0.4rem" }}>
              Target MCP Connector Server:
            </label>
            <select
              className="select-input"
              value={selectedServerId}
              onChange={(e) => handleServerChange(e.target.value)}
              style={{ width: "100%", background: "rgba(30, 41, 59, 0.8)", border: "1px solid rgba(255, 255, 255, 0.15)", color: "#f8fafc" }}
            >
              {servers.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name} ({s.id}) {!connectedServers[s.id] ? " (Disconnected)" : ""}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label style={{ display: "block", fontSize: "0.8rem", fontWeight: 600, color: "var(--text-muted)", marginBottom: "0.4rem" }}>
              Target Tool Name:
            </label>
            <select
              className="select-input"
              value={selectedToolName}
              onChange={(e) => handleToolChange(e.target.value)}
              style={{ width: "100%", background: "rgba(30, 41, 59, 0.8)", border: "1px solid rgba(255, 255, 255, 0.15)", color: "#f8fafc" }}
            >
              {tools
                .filter((t) => t.server_id === selectedServerId)
                .map((t) => (
                  <option key={t.name} value={t.name}>
                    {t.name}
                  </option>
                ))}
            </select>
          </div>
        </div>

        {/* Workspace: Left Arguments Editor, Right Tool Response Output */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.25rem" }}>
          
          {/* Input JSON Arguments */}
          <div>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.5rem" }}>
              <label style={{ fontSize: "0.8rem", fontWeight: 600, color: "var(--text-muted)" }}>JSON Arguments Payload:</label>
            </div>
            <textarea
              value={toolArgsText}
              onChange={(e) => setToolArgsText(e.target.value)}
              style={{
                width: "100%",
                height: "280px",
                fontFamily: "monospace",
                fontSize: "0.82rem",
                background: "rgba(2, 6, 23, 0.8)",
                border: "1px solid rgba(255, 255, 255, 0.15)",
                borderRadius: "8px",
                padding: "0.85rem",
                color: "#f8fafc",
                resize: "vertical"
              }}
            />
            <button
              type="button"
              className="btn btn-primary"
              onClick={handleExecuteMcpTool}
              disabled={executing || !connectedServers[selectedServerId]}
              style={{
                width: "100%",
                marginTop: "1rem",
                background: !connectedServers[selectedServerId] ? "#475569" : "linear-gradient(135deg, #a855f7, #6366f1)",
                border: "none",
                fontWeight: 700
              }}
            >
              {executing ? (
                <>
                  <RefreshCw className="w-4 h-4 mr-2 animate-spin" /> Executing MCP Tool Call...
                </>
              ) : !connectedServers[selectedServerId] ? (
                "Connector Disconnected (Click Connect Above)"
              ) : (
                <>
                  <Play className="w-4 h-4 mr-2 fill-current" /> Execute MCP Tool Call
                </>
              )}
            </button>
          </div>

          {/* JSON Response Terminal */}
          <div>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.5rem" }}>
              <label style={{ fontSize: "0.8rem", fontWeight: 600, color: "var(--text-muted)" }}>MCP Tool Response Output:</label>
              {execResult && (
                <span className={`badge ${execResult.status === "success" ? "badge-success" : "badge-danger"}`} style={{ fontSize: "0.72rem" }}>
                  {execResult.status === "success" ? `Success (${execResult.execution_time_ms} ms)` : "Execution Error"}
                </span>
              )}
            </div>

            <pre
              style={{
                fontFamily: "monospace",
                fontSize: "0.8rem",
                background: "rgba(2, 6, 23, 0.95)",
                border: "1px solid rgba(255, 255, 255, 0.1)",
                borderRadius: "8px",
                padding: "1rem",
                height: "330px",
                overflowY: "auto",
                color: execResult?.status === "error" ? "#fb7185" : "#38bdf8",
                margin: 0
              }}
            >
              <code>
                {execResult 
                  ? JSON.stringify(execResult, null, 2) 
                  : "// Execute an MCP tool call on the left to view response JSON..."}
              </code>
            </pre>
          </div>

        </div>

      </div>

      {/* TOKEN VERIFICATION & CONNECTION MODAL */}
      {activeConnectModalServer && (
        <div style={{
          position: "fixed",
          inset: 0,
          background: "rgba(2, 6, 23, 0.8)",
          backdropFilter: "blur(8px)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          zIndex: 9999,
          padding: "1rem"
        }}>
          <div style={{
            background: "rgba(30, 41, 59, 0.95)",
            border: "1px solid rgba(168, 85, 247, 0.4)",
            boxShadow: "0 25px 50px -12px rgba(0, 0, 0, 0.7)",
            borderRadius: "16px",
            width: "100%",
            maxWidth: "520px",
            padding: "1.75rem",
            position: "relative"
          }}>
            <button
              type="button"
              onClick={() => setActiveConnectModalServer(null)}
              style={{
                position: "absolute",
                top: "1.25rem",
                right: "1.25rem",
                background: "transparent",
                border: "none",
                color: "#94a3b8",
                cursor: "pointer"
              }}
            >
              <X className="w-5 h-5" />
            </button>

            <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", marginBottom: "1.25rem" }}>
              <div style={{ background: "rgba(168, 85, 247, 0.2)", padding: "0.5rem", borderRadius: "10px" }}>
                <Key className="w-6 h-6 text-purple-400" />
              </div>
              <div>
                <h3 style={{ fontSize: "1.2rem", fontWeight: 700, margin: 0, color: "#f8fafc" }}>
                  Connect to {activeConnectModalServer.name}
                </h3>
                <div style={{ fontSize: "0.8rem", color: "#94a3b8" }}>
                  {activeConnectModalServer.category} Connector Authentication
                </div>
              </div>
            </div>

            <p style={{ fontSize: "0.85rem", color: "#cbd5e1", lineHeight: 1.5, marginBottom: "1.25rem" }}>
              Please enter your <strong>OAuth Access Token</strong> or <strong>API Key</strong> for {activeConnectModalServer.name}. The system will verify authorization before establishing the connection.
            </p>

            {modalError && (
              <div style={{
                background: "rgba(244, 63, 94, 0.15)",
                border: "1px solid rgba(244, 63, 94, 0.4)",
                color: "#fb7185",
                padding: "0.75rem 1rem",
                borderRadius: "8px",
                fontSize: "0.83rem",
                marginBottom: "1.25rem",
                display: "flex",
                alignItems: "center",
                gap: "0.5rem"
              }}>
                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                <span>{modalError}</span>
              </div>
            )}

            <div style={{ marginBottom: "1.5rem" }}>
              <label style={{ display: "block", fontSize: "0.8rem", fontWeight: 600, color: "#94a3b8", marginBottom: "0.4rem" }}>
                <Lock className="w-3.5 h-3.5 inline mr-1 text-purple-400" />
                Enter Access Token / API Key:
              </label>
              <input
                type="password"
                value={tokenInput}
                onChange={(e) => setTokenInput(e.target.value)}
                placeholder="ghp_... or Bearer token or secret key"
                style={{
                  width: "100%",
                  background: "rgba(15, 23, 42, 0.8)",
                  border: "1px solid rgba(255, 255, 255, 0.15)",
                  borderRadius: "8px",
                  padding: "0.65rem 0.85rem",
                  color: "#f8fafc",
                  fontSize: "0.85rem",
                  fontFamily: "monospace"
                }}
              />
            </div>

            <div style={{ display: "flex", justifyContent: "flex-end", gap: "0.75rem" }}>
              <button
                type="button"
                className="btn btn-secondary btn-sm"
                onClick={() => setActiveConnectModalServer(null)}
                disabled={verifyingToken}
              >
                Cancel
              </button>
              <button
                type="button"
                className="btn btn-primary btn-sm"
                onClick={handleVerifyAndConnect}
                disabled={verifyingToken}
                style={{
                  background: "linear-gradient(135deg, #a855f7, #6366f1)",
                  border: "none",
                  fontWeight: 600,
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "0.4rem"
                }}
              >
                {verifyingToken ? (
                  <>
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" /> Validating Token...
                  </>
                ) : (
                  <>
                    <CheckCircle2 className="w-3.5 h-3.5" /> Validate & Connect
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

    </main>
  );
}
