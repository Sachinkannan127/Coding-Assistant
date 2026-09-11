"""
🥈 GitHub MCP Connector Server.
Provides repository fetching, PR inspection, and GitHub file retrieval tools.
"""

import httpx
from typing import Dict, Any, List


class GithubMcpServer:
    SERVER_ID = "github"
    NAME = "GitHub MCP Connector"
    DESCRIPTION = "GitHub Pull Request inspection, repository file fetching, and commit diff analysis"
    CATEGORY = "Integrations"

    @classmethod
    def get_tools(cls) -> List[Dict[str, Any]]:
        return [
            {
                "name": "fetch_github_pr",
                "description": "Retrieves pull request details, title, description, modified files count, and diff url from GitHub API.",
                "server_id": cls.SERVER_ID,
                "parameters": [
                    {"name": "owner", "type": "string", "description": "GitHub Repository Owner / Org", "required": True},
                    {"name": "repo", "type": "string", "description": "GitHub Repository Name", "required": True},
                    {"name": "pr_number", "type": "integer", "description": "Pull Request Number", "required": True}
                ]
            },
            {
                "name": "fetch_repo_file",
                "description": "Fetches raw file content from a GitHub public repository branch.",
                "server_id": cls.SERVER_ID,
                "parameters": [
                    {"name": "owner", "type": "string", "description": "GitHub Repository Owner", "required": True},
                    {"name": "repo", "type": "string", "description": "GitHub Repository Name", "required": True},
                    {"name": "path", "type": "string", "description": "File relative path in repo (e.g. 'backend/main.py')", "required": True},
                    {"name": "ref", "type": "string", "description": "Branch, tag, or commit hash", "required": False, "default": "main"}
                ]
            }
        ]

    @classmethod
    async def execute_tool(cls, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        if tool_name == "fetch_github_pr":
            return await cls._fetch_github_pr(
                owner=args.get("owner", ""),
                repo=args.get("repo", ""),
                pr_number=int(args.get("pr_number", 0))
            )
        elif tool_name == "fetch_repo_file":
            return await cls._fetch_repo_file(
                owner=args.get("owner", ""),
                repo=args.get("repo", ""),
                path=args.get("path", ""),
                ref=args.get("ref", "main")
            )
        else:
            raise ValueError(f"Unknown tool '{tool_name}' for server '{cls.SERVER_ID}'")

    @classmethod
    async def _fetch_github_pr(cls, owner: str, repo: str, pr_number: int) -> Dict[str, Any]:
        if not owner or not repo or not pr_number:
            raise ValueError("Parameters 'owner', 'repo', and 'pr_number' are required.")

        url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.get(url, headers={"User-Agent": "CodePilot-MCP"})
            if res.status_code != 200:
                return {
                    "success": False,
                    "error": f"GitHub API Error: {res.status_code} {res.reason_phrase}",
                    "details": res.json() if res.status_code == 404 else None
                }
            data = res.json()
            return {
                "success": True,
                "pr_number": data.get("number"),
                "title": data.get("title"),
                "author": data.get("user", {}).get("login"),
                "state": data.get("state"),
                "additions": data.get("additions"),
                "deletions": data.get("deletions"),
                "changed_files": data.get("changed_files"),
                "html_url": data.get("html_url"),
                "diff_url": data.get("diff_url"),
                "body": data.get("body", "")[:500]
            }

    @classmethod
    async def _fetch_repo_file(cls, owner: str, repo: str, path: str, ref: str = "main") -> Dict[str, Any]:
        if not owner or not repo or not path:
            raise ValueError("Parameters 'owner', 'repo', and 'path' are required.")

        raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{ref}/{path}"
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.get(raw_url, headers={"User-Agent": "CodePilot-MCP"})
            if res.status_code != 200:
                return {
                    "success": False,
                    "error": f"File not found on GitHub ({res.status_code})",
                    "raw_url": raw_url
                }

            content = res.text
            return {
                "success": True,
                "file_path": path,
                "ref": ref,
                "size_bytes": len(content.encode("utf-8")),
                "content": content
            }
