"""
⚙️ Git MCP Connector Server.
Provides local Git repository inspection, branch status, and commit diff extraction tools.
"""

import os
import subprocess
from typing import Dict, Any, List

WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))


class GitMcpServer:
    SERVER_ID = "git"
    NAME = "Git MCP"
    DESCRIPTION = "Local Git history, working tree status, branch tracking, and commit diffs"
    CATEGORY = "Version Control"

    @classmethod
    def get_tools(cls) -> List[Dict[str, Any]]:
        return [
            {
                "name": "get_git_status",
                "description": "Retrieves current git branch name, untracked files, modified files, and staging status.",
                "server_id": cls.SERVER_ID,
                "parameters": []
            },
            {
                "name": "get_git_diff",
                "description": "Extracts git diff output for unstaged or staged working tree changes.",
                "server_id": cls.SERVER_ID,
                "parameters": [
                    {"name": "staged", "type": "boolean", "description": "Whether to inspect staged changes (--cached)", "required": False, "default": False}
                ]
            }
        ]

    @classmethod
    async def execute_tool(cls, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        if tool_name == "get_git_status":
            return cls._get_git_status()
        elif tool_name == "get_git_diff":
            staged = bool(args.get("staged", False))
            return cls._get_git_diff(staged)
        else:
            raise ValueError(f"Unknown tool '{tool_name}' for server '{cls.SERVER_ID}'")

    @classmethod
    def _run_git_command(cls, cmd: List[str]) -> str:
        try:
            res = subprocess.run(
                cmd,
                cwd=WORKSPACE_ROOT,
                capture_output=True,
                text=True,
                timeout=5
            )
            if res.returncode != 0:
                return f"Git Error ({res.returncode}): {res.stderr.strip()}"
            return res.stdout.strip()
        except Exception as e:
            return f"Git Execution Exception: {str(e)}"

    @classmethod
    def _get_git_status(cls) -> Dict[str, Any]:
        branch = cls._run_git_command(["git", "rev-parse", "--abbrev-ref", "HEAD"])
        status_out = cls._run_git_command(["git", "status", "--porcelain"])

        modified = []
        untracked = []
        staged = []

        if not status_out.startswith("Git Error") and not status_out.startswith("Git Execution"):
            for line in status_out.splitlines():
                if not line.strip():
                    continue
                code = line[:2]
                path = line[3:].strip()
                if code == "??":
                    untracked.append(path)
                elif code[0] in ("M", "A", "D"):
                    staged.append(path)
                elif code[1] in ("M", "D"):
                    modified.append(path)

        return {
            "success": not branch.startswith("Git Error"),
            "current_branch": branch,
            "modified_files": modified,
            "staged_files": staged,
            "untracked_files": untracked,
            "clean": len(modified) == 0 and len(staged) == 0 and len(untracked) == 0
        }

    @classmethod
    def _get_git_diff(cls, staged: bool = False) -> Dict[str, Any]:
        cmd = ["git", "diff"]
        if staged:
            cmd.append("--cached")

        diff_text = cls._run_git_command(cmd)
        return {
            "success": not diff_text.startswith("Git Error"),
            "staged": staged,
            "diff": diff_text[:5000] if diff_text else "No local git diff changes detected."
        }
