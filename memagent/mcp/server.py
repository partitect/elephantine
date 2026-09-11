import asyncio
import sys
from typing import Any, Dict, List, Optional
from mcp.server.fastmcp import FastMCP
from memagent.api.routes.memory import get_container
from memagent.api.schemas import RememberRequest, RecallRequest, ToolCallExecution

mcp = FastMCP("MemAgent")

@mcp.tool()
async def remember_fact(
    content: str,
    category: str = "general",
    entity_key: Optional[str] = None,
    source_agent: str = "cursor_agent"
) -> str:
    """
    Persistently store a fact, user preference, architectural decision,
    or coding workflow in MemAgent local memory.
    """
    svc = get_container()
    req = RememberRequest(
        content=content,
        category=category,
        entity_key=entity_key,
        source_agent=source_agent
    )
    from memagent.api.routes.memory import remember_endpoint
    res = await remember_endpoint(req, svc)
    return f"Memory stored (id: {res.id}). Conflicts resolved: {len(res.conflicts_resolved)}"

@mcp.tool()
async def recall_context(
    query: str,
    top_k: int = 5,
    category: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Search and retrieve relevant context and memories using CPU hybrid vector (LanceDB)
    and BM25 (SQLite FTS5) search with recency decay.
    """
    svc = get_container()
    req = RecallRequest(query=query, top_k=top_k, category=category)
    from memagent.api.routes.memory import recall_endpoint
    res = await recall_endpoint(req, svc)
    return [
        {
            "id": m.id,
            "content": m.content,
            "category": m.category,
            "confidence": m.confidence,
            "hybrid_score": m.hybrid_score,
            "decayed_score": m.decayed_score,
            "created_at": m.created_at.isoformat()
        }
        for m in res.memories
    ]

@mcp.tool()
async def get_procedural_workflow(pattern_name: str) -> Dict[str, Any]:
    """Retrieve an executable multi-step procedural workflow snippet by its pattern name."""
    svc = get_container()
    wf = await svc.procedural_store.get_workflow(pattern_name)
    if not wf:
        return {"error": f"Workflow '{pattern_name}' not found"}
    return wf.model_dump()

def main():
    """Main entrypoint for MCP stdio mode (Cursor / Claude Desktop)."""
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()
