"""
Central Model Context Protocol (MCP) Server Registry.
Registers and manages all 7 MCP server connectors, providing catalog query and tool dispatching.
"""

import time
import logging
from typing import Dict, Any, List
from backend.app.mcp.schemas import McpServerInfo, McpToolDefinition, McpToolCallResult
from backend.app.mcp.static_analysis_mcp import StaticAnalysisMcpServer
from backend.app.mcp.security_scanner_mcp import SecurityScannerMcpServer
from backend.app.mcp.github_mcp import GithubMcpServer
from backend.app.mcp.filesystem_mcp import FilesystemMcpServer
from backend.app.mcp.doc_fetch_mcp import DocFetchMcpServer
from backend.app.mcp.git_mcp import GitMcpServer
from backend.app.mcp.sandbox_mcp import SandboxMcpServer

logger = logging.getLogger(__name__)


class McpRegistry:
    def __init__(self):
        self._servers: Dict[str, Any] = {}
        self._tools: Dict[str, Dict[str, Any]] = {}
        self._register_default_servers()

    def _register_default_servers(self):
        # Register all 7 MCP Stack Servers
        self._register_server(StaticAnalysisMcpServer)
        self._register_server(SecurityScannerMcpServer)
        self._register_server(GithubMcpServer)
        self._register_server(FilesystemMcpServer)
        self._register_server(DocFetchMcpServer)
        self._register_server(GitMcpServer)
        self._register_server(SandboxMcpServer)

    def _register_server(self, server_class: Any):
        server_id = server_class.SERVER_ID
        self._servers[server_id] = server_class

        tools = server_class.get_tools()
        for tool in tools:
            tool_name = tool["name"]
            tool["server_id"] = server_id
            self._tools[tool_name] = tool

        logger.info(f"Registered MCP Server Connector: '{server_class.NAME}' ({len(tools)} tools)")

    def get_all_servers(self) -> List[McpServerInfo]:
        servers_info = []
        for server_id, server_cls in self._servers.items():
            tools = server_cls.get_tools()
            info = McpServerInfo(
                id=server_id,
                name=server_cls.NAME,
                description=server_cls.DESCRIPTION,
                category=server_cls.CATEGORY,
                status="active",
                tools_count=len(tools)
            )
            servers_info.append(info)
        return servers_info

    def get_all_tools(self) -> List[McpToolDefinition]:
        tool_defs = []
        for tool_name, tool_data in self._tools.items():
            params = tool_data.get("parameters", [])
            param_models = [
                {
                    "name": p.get("name"),
                    "type": p.get("type", "string"),
                    "description": p.get("description", ""),
                    "required": p.get("required", True),
                    "default": p.get("default", None)
                }
                for p in params
            ]
            tdef = McpToolDefinition(
                name=tool_name,
                description=tool_data.get("description", ""),
                server_id=tool_data.get("server_id", ""),
                parameters=param_models
            )
            tool_defs.append(tdef)
        return tool_defs

    async def execute_tool(self, server_id: str, tool_name: str, arguments: Dict[str, Any]) -> McpToolCallResult:
        start_time = time.perf_counter()

        server_cls = self._servers.get(server_id)
        if not server_cls:
            return McpToolCallResult(
                status="error",
                server_id=server_id,
                tool_name=tool_name,
                error=f"MCP Server Connector '{server_id}' not found.",
                execution_time_ms=0.0
            )

        tool_info = self._tools.get(tool_name)
        if not tool_info or tool_info.get("server_id") != server_id:
            return McpToolCallResult(
                status="error",
                server_id=server_id,
                tool_name=tool_name,
                error=f"Tool '{tool_name}' not registered under server '{server_id}'.",
                execution_time_ms=0.0
            )

        try:
            result_payload = await server_cls.execute_tool(tool_name, arguments)
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            return McpToolCallResult(
                status="success",
                server_id=server_id,
                tool_name=tool_name,
                result=result_payload,
                execution_time_ms=elapsed_ms
            )
        except Exception as e:
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.error(f"MCP Tool Execution Error [{server_id}.{tool_name}]: {e}")
            return McpToolCallResult(
                status="error",
                server_id=server_id,
                tool_name=tool_name,
                error=f"Tool Execution Error: {str(e)}",
                execution_time_ms=elapsed_ms
            )


# Global singleton instance
mcp_registry = McpRegistry()
