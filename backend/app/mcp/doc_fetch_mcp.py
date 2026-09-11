"""
🥉 Documentation / Fetch MCP Connector Server.
Provides RAG context retrieval and official documentation lookup tools.
"""

from typing import Dict, Any, List
from backend.app.services.rag_service import rag_service


class DocFetchMcpServer:
    SERVER_ID = "doc_fetch"
    NAME = "Documentation / Fetch MCP"
    DESCRIPTION = "RAG vector context retrieval and language/framework styleguide documentation lookup"
    CATEGORY = "Knowledge & RAG"

    STYLEGUIDES = {
        "python": "PEP 8: Use 4 spaces per indentation, snake_case for functions/variables, PascalCase for classes, type annotations, and docstrings.",
        "typescript": "Use strict types, interfaces for object models, camelCase for variables/functions, PascalCase for components, and avoid 'any'.",
        "react": "Use functional components with hooks, memoize expensive calculations with useMemo/useCallback, and enforce key props in arrays.",
        "fastapi": "Use Pydantic v2 schemas for payload validation, async path operations, and dependency injection via Depends().",
        "security": "Follow OWASP guidelines: parameterized queries for SQL, bcrypt for password hashing, and CORS origins restrictions."
    }

    @classmethod
    def get_tools(cls) -> List[Dict[str, Any]]:
        return [
            {
                "name": "fetch_rag_docs",
                "description": "Queries MongoDB Vector RAG database to retrieve official repository documentation and architecture rules.",
                "server_id": cls.SERVER_ID,
                "parameters": [
                    {"name": "query", "type": "string", "description": "Search query or architectural context topic", "required": True},
                    {"name": "top_k", "type": "integer", "description": "Number of top matching documents to retrieve", "required": False, "default": 3}
                ]
            },
            {
                "name": "lookup_language_styleguide",
                "description": "Retrieves official best-practice coding styleguides and architectural rules for a specified language/framework.",
                "server_id": cls.SERVER_ID,
                "parameters": [
                    {"name": "target", "type": "string", "description": "Target language or framework (python, typescript, react, fastapi, security)", "required": True}
                ]
            }
        ]

    @classmethod
    async def execute_tool(cls, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        if tool_name == "fetch_rag_docs":
            query = args.get("query", "")
            top_k = int(args.get("top_k", 3))
            return await cls._fetch_rag_docs(query, top_k)
        elif tool_name == "lookup_language_styleguide":
            target = args.get("target", "python").lower()
            return cls._lookup_styleguide(target)
        else:
            raise ValueError(f"Unknown tool '{tool_name}' for server '{cls.SERVER_ID}'")

    @classmethod
    async def _fetch_rag_docs(cls, query: str, top_k: int = 3) -> Dict[str, Any]:
        if not query or not query.strip():
            raise ValueError("Parameter 'query' cannot be empty.")

        docs = await rag_service.retrieve_knowledge(query_code=query, limit=top_k)
        return {
            "query": query,
            "docs_found_count": len(docs),
            "documents": [
                {
                    "content": doc
                }
                for doc in docs
            ]
        }

    @classmethod
    def _lookup_styleguide(cls, target: str) -> Dict[str, Any]:
        key = target.strip().lower()
        guide = cls.STYLEGUIDES.get(key)
        if not guide:
            return {
                "success": False,
                "target": target,
                "available_guides": list(cls.STYLEGUIDES.keys()),
                "message": f"Styleguide for '{target}' not found."
            }

        return {
            "success": True,
            "target": key,
            "styleguide": guide
        }
