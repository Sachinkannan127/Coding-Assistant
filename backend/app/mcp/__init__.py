"""
Model Context Protocol (MCP) Package for CodePilot Backend.
Exposes standardized tool servers and connectors.
"""

from backend.app.mcp.mcp_registry import mcp_registry

__all__ = ["mcp_registry"]
