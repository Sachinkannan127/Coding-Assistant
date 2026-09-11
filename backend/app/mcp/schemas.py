"""
Model Context Protocol (MCP) Pydantic Schemas & DTOs.
Provides standard schemas for MCP tool definitions, requests, tool call results, and server status.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class McpToolParameter(BaseModel):
    name: str = Field(..., description="Parameter name")
    type: str = Field(..., description="Parameter data type (string, integer, boolean, object, array)")
    description: str = Field(..., description="Description of the parameter")
    required: bool = Field(default=True, description="Whether the parameter is mandatory")
    default: Optional[Any] = Field(default=None, description="Default parameter value")


class McpToolDefinition(BaseModel):
    name: str = Field(..., description="Unique tool name identifier")
    description: str = Field(..., description="Human-readable description of what the tool does")
    server_id: str = Field(..., description="ID of the parent MCP server connector")
    parameters: List[McpToolParameter] = Field(default_factory=list, description="Tool input arguments schema")


class McpServerInfo(BaseModel):
    id: str = Field(..., description="Unique MCP Server ID")
    name: str = Field(..., description="Display name of the MCP connector server")
    description: str = Field(..., description="Description of server role & capabilities")
    category: str = Field(..., description="Category (Static Analysis, Security, Git, RAG, etc.)")
    status: str = Field(default="active", description="Connector status (active, offline, standby)")
    tools_count: int = Field(default=0, description="Total tools registered under this server")


class McpToolCallRequest(BaseModel):
    server_id: str = Field(..., description="Target MCP Server Connector ID")
    tool_name: str = Field(..., description="Target tool name to execute")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Input parameters dictionary")


class McpToolCallResult(BaseModel):
    status: str = Field(..., description="Execution status ('success' or 'error')")
    server_id: str = Field(..., description="MCP Server Connector ID")
    tool_name: str = Field(..., description="Executed tool name")
    result: Optional[Dict[str, Any]] = Field(default=None, description="Tool execution return payload")
    error: Optional[str] = Field(default=None, description="Error message if tool execution failed")
    execution_time_ms: float = Field(default=0.0, description="Execution duration in milliseconds")
