"""
🥈 Filesystem MCP Connector Server.
Provides local codebase exploration, multi-file directory listing, and pattern searching.
"""

import os
from typing import Dict, Any, List

WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))


class FilesystemMcpServer:
    SERVER_ID = "filesystem"
    NAME = "Filesystem MCP"
    DESCRIPTION = "Multi-file project access, repository tree inspection, and codebase grep searching"
    CATEGORY = "Local Workspace"

    @classmethod
    def get_tools(cls) -> List[Dict[str, Any]]:
        return [
            {
                "name": "list_workspace_files",
                "description": "Lists files and directories under workspace root or a specified relative directory path.",
                "server_id": cls.SERVER_ID,
                "parameters": [
                    {"name": "relative_path", "type": "string", "description": "Relative directory path (e.g., 'backend/app')", "required": False, "default": ""},
                    {"name": "max_depth", "type": "integer", "description": "Maximum directory recursion depth", "required": False, "default": 2}
                ]
            },
            {
                "name": "read_project_file",
                "description": "Reads raw content from a project file safely within the workspace boundaries.",
                "server_id": cls.SERVER_ID,
                "parameters": [
                    {"name": "relative_file_path", "type": "string", "description": "Relative file path (e.g. 'backend/app/main.py')", "required": True}
                ]
            },
            {
                "name": "search_codebase_grep",
                "description": "Searches for a text pattern or symbol across codebase files.",
                "server_id": cls.SERVER_ID,
                "parameters": [
                    {"name": "query", "type": "string", "description": "Search query keyword or symbol name", "required": True},
                    {"name": "file_extension", "type": "string", "description": "Filter by file extension (e.g., '.py', '.tsx')", "required": False, "default": ""}
                ]
            }
        ]

    @classmethod
    async def execute_tool(cls, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        if tool_name == "list_workspace_files":
            return cls._list_workspace_files(
                rel_path=args.get("relative_path", ""),
                max_depth=int(args.get("max_depth", 2))
            )
        elif tool_name == "read_project_file":
            return cls._read_project_file(
                rel_file_path=args.get("relative_file_path", "")
            )
        elif tool_name == "search_codebase_grep":
            return cls._search_codebase_grep(
                query=args.get("query", ""),
                ext_filter=args.get("file_extension", "")
            )
        else:
            raise ValueError(f"Unknown tool '{tool_name}' for server '{cls.SERVER_ID}'")

    @classmethod
    def _list_workspace_files(cls, rel_path: str = "", max_depth: int = 2) -> Dict[str, Any]:
        target_dir = os.path.abspath(os.path.join(WORKSPACE_ROOT, rel_path))
        if not target_dir.startswith(WORKSPACE_ROOT):
            raise ValueError("Access Denied: Path outside workspace bounds.")

        if not os.path.exists(target_dir) or not os.path.isdir(target_dir):
            return {"success": False, "error": f"Directory '{rel_path}' does not exist."}

        items = []
        for root, dirs, files in os.walk(target_dir):
            # Skip hidden and cache folders
            dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("node_modules", "venv", "__pycache__", "dist", ".git")]
            
            rel_root = os.path.relpath(root, WORKSPACE_ROOT)
            depth = 0 if rel_root == "." else len(rel_root.split(os.sep))
            if depth > max_depth:
                dirs.clear()
                continue

            for file in files:
                if file.startswith("."):
                    continue
                file_abs = os.path.join(root, file)
                rel_file = os.path.relpath(file_abs, WORKSPACE_ROOT)
                size = os.path.getsize(file_abs)
                items.append({
                    "path": rel_file,
                    "size_bytes": size,
                    "name": file
                })

        return {
            "success": True,
            "workspace_root": WORKSPACE_ROOT,
            "target_dir": rel_path or "/",
            "total_files": len(items),
            "files": items[:100]  # Cap at 100 entries for safety
        }

    @classmethod
    def _read_project_file(cls, rel_file_path: str) -> Dict[str, Any]:
        if not rel_file_path:
            raise ValueError("Parameter 'relative_file_path' is required.")

        target_file = os.path.abspath(os.path.join(WORKSPACE_ROOT, rel_file_path))
        if not target_file.startswith(WORKSPACE_ROOT):
            raise ValueError("Access Denied: Path outside workspace bounds.")

        if not os.path.exists(target_file) or not os.path.isfile(target_file):
            return {"success": False, "error": f"File '{rel_file_path}' not found."}

        try:
            with open(target_file, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()

            return {
                "success": True,
                "relative_path": rel_file_path,
                "size_bytes": len(content.encode("utf-8")),
                "total_lines": len(content.splitlines()),
                "content": content
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to read file: {str(e)}"}

    @classmethod
    def _search_codebase_grep(cls, query: str, ext_filter: str = "") -> Dict[str, Any]:
        if not query or not query.strip():
            raise ValueError("Parameter 'query' cannot be empty.")

        matches = []
        ext = ext_filter.strip().lower()

        for root, dirs, files in os.walk(WORKSPACE_ROOT):
            dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("node_modules", "venv", "__pycache__", "dist", ".git")]
            for file in files:
                if ext and not file.endswith(ext):
                    continue
                file_abs = os.path.join(root, file)
                rel_file = os.path.relpath(file_abs, WORKSPACE_ROOT)
                try:
                    with open(file_abs, "r", encoding="utf-8", errors="ignore") as f:
                        for idx, line in enumerate(f, start=1):
                            if query in line:
                                matches.append({
                                    "file": rel_file,
                                    "line": idx,
                                    "snippet": line.strip()[:150]
                                })
                                if len(matches) >= 50:
                                    break
                except Exception:
                    continue
                if len(matches) >= 50:
                    break

        return {
            "query": query,
            "total_matches": len(matches),
            "matches": matches
        }
