"""
Model Context Protocol (MCP) FastAPI API Router.
Exposes REST and JSON-RPC 2.0 endpoints for querying active MCP servers, tool definitions, and tool execution.
"""

from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, status
from backend.app.mcp.schemas import McpServerInfo, McpToolDefinition, McpToolCallRequest, McpToolCallResult
from backend.app.mcp.mcp_registry import mcp_registry

router = APIRouter(prefix="/v1/mcp", tags=["Model Context Protocol (MCP)"])


@router.get(
    "/servers",
    response_model=List[McpServerInfo],
    status_code=status.HTTP_200_OK
)
async def list_mcp_servers():
    """
    List all active CodePilot MCP Server Connectors and status.
    """
    return mcp_registry.get_all_servers()


@router.get(
    "/tools",
    response_model=List[McpToolDefinition],
    status_code=status.HTTP_200_OK
)
async def list_mcp_tools():
    """
    List full catalog of registered MCP tools and JSON parameter schemas across all connectors.
    """
    return mcp_registry.get_all_tools()


@router.post(
    "/call",
    response_model=McpToolCallResult,
    status_code=status.HTTP_200_OK
)
async def call_mcp_tool(payload: McpToolCallRequest):
    """
    Executes a registered MCP tool call by server ID and tool name.
    """
    result = await mcp_registry.execute_tool(
        server_id=payload.server_id,
        tool_name=payload.tool_name,
        arguments=payload.arguments
    )
    return result


@router.post(
    "/jsonrpc",
    status_code=status.HTTP_200_OK
)
async def handle_jsonrpc_request(request: Dict[str, Any]):
    """
    Standard JSON-RPC 2.0 endpoint for official MCP Client protocol interaction (e.g. tools/list, tools/call).
    """
    method = request.get("method")
    req_id = request.get("id", 1)
    params = request.get("params", {})

    if method == "tools/list":
        tools = mcp_registry.get_all_tools()
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "tools": [t.dict() for t in tools]
            }
        }
    elif method == "tools/call":
        name = params.get("name")
        args = params.get("arguments", {})

        # Find tool to get its server_id
        tool_obj = next((t for t in mcp_registry.get_all_tools() if t.name == name), None)
        if not tool_obj:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32601, "message": f"Method/Tool '{name}' not found."}
            }

        res = await mcp_registry.execute_tool(tool_obj.server_id, name, args)
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": res.dict()
        }
    else:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32601, "message": f"Unsupported JSON-RPC method '{method}'."}
        }
