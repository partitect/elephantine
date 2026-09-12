import asyncio
import sys
from typing import Any, Dict, List, Optional
from mcp.server.fastmcp import FastMCP
from elephantine.api.routes.memory import get_container
from elephantine.api.schemas import RememberRequest, RecallRequest, ToolCallExecution
from elephantine.core.project import detect_project_workspace

mcp = FastMCP("Elephantine")

@mcp.tool()
async def remember_fact(
    content: str,
    category: str = "general",
    entity_key: Optional[str] = None,
    source_agent: str = "cursor_agent",
    workspace_id: Optional[str] = None
) -> str:
    """
    Persistently store a fact, user preference, architectural decision,
    or coding workflow in Elephantine local memory.
    If workspace_id is omitted, it is automatically resolved from current git repository.
    """
    svc = get_container()
    resolved_workspace = workspace_id or detect_project_workspace()
    req = RememberRequest(
        content=content,
        category=category,
        entity_key=entity_key,
        source_agent=source_agent,
        workspace_id=resolved_workspace
    )
    from elephantine.api.routes.memory import remember_endpoint
    res = await remember_endpoint(req, svc)
    return f"Memory stored in project '{resolved_workspace}' (id: {res.id}). Conflicts resolved: {len(res.conflicts_resolved)}"

@mcp.tool()
async def recall_context(
    query: str,
    top_k: int = 5,
    category: Optional[str] = None,
    workspace_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Search and retrieve relevant context and memories using CPU hybrid vector (LanceDB)
    and BM25 (SQLite FTS5) search with recency decay.
    Scoped to the current project/workspace by default.
    """
    svc = get_container()
    resolved_workspace = workspace_id or detect_project_workspace()
    req = RecallRequest(
        query=query,
        top_k=top_k,
        category=category,
        workspace_id=resolved_workspace
    )
    from elephantine.api.routes.memory import recall_endpoint
    res = await recall_endpoint(req, svc)
    return [
        {
            "id": m.id,
            "content": m.content,
            "workspace_id": m.workspace_id,
            "category": m.category,
            "confidence": m.confidence,
            "hybrid_score": m.hybrid_score,
            "decayed_score": m.decayed_score,
            "created_at": m.created_at.isoformat()
        }
        for m in res.memories
    ]

@mcp.tool()
async def batch_remember(
    items: List[Dict[str, Any]],
    source_agent: str = "batch_agent",
    workspace_id: Optional[str] = None
) -> str:
    """
    Store multiple memories, facts, decisions, or preferences in a single batch.
    Each item in items can contain:
      - content (required): Textual description
      - category (optional): One of 13 types: fact, decision, preference, instruction, error, architecture, credential_ref, todo, bugfix, workflow, constraint, session_summary, general
      - entity_key (optional): Unique key for conflict resolution and superseding
      - ttl_hours (optional): Auto-expiry TTL in hours
      - role_authority (optional): 0.1 to 1.0 (default 0.5)
      - metadata (optional): Dict with provenance, file paths, tags
    """
    svc = get_container()
    resolved_workspace = workspace_id or detect_project_workspace()
    from elephantine.api.routes.memory import remember_endpoint

    stored_ids = []
    total_conflicts = 0
    for it in items:
        content = it.get("content", "").strip()
        if not content:
            continue
        req = RememberRequest(
            content=content,
            category=it.get("category", "general"),
            entity_key=it.get("entity_key"),
            source_agent=it.get("source_agent", source_agent),
            workspace_id=resolved_workspace,
            role_authority=float(it.get("role_authority", 0.5)),
            ttl_hours=it.get("ttl_hours"),
            metadata=it.get("metadata", {})
        )
        res = await remember_endpoint(req, svc)
        stored_ids.append(res.id)
        total_conflicts += len(res.conflicts_resolved)

    return f"Batch committed: {len(stored_ids)} memories stored in workspace '{resolved_workspace}'. {total_conflicts} older conflict(s) resolved."

@mcp.tool()
async def recall_as_of(
    query: str,
    as_of_iso: str,
    top_k: int = 5,
    category: Optional[str] = None,
    workspace_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Temporal recall: returns memory state exactly as it existed at a past timestamp.
    as_of_iso: ISO 8601 string, e.g. '2026-09-10T12:00:00Z'.
    """
    from datetime import datetime
    svc = get_container()
    resolved_workspace = workspace_id or detect_project_workspace()
    as_of_dt = datetime.fromisoformat(as_of_iso.replace("Z", "+00:00"))

    req = RecallRequest(
        query=query,
        top_k=top_k,
        category=category,
        workspace_id=resolved_workspace,
        as_of=as_of_dt
    )
    from elephantine.api.routes.memory import recall_endpoint
    res = await recall_endpoint(req, svc)
    return [
        {
            "id": m.id,
            "content": m.content,
            "workspace_id": m.workspace_id,
            "category": m.category,
            "confidence": m.confidence,
            "created_at": m.created_at.isoformat()
        }
        for m in res.memories
    ]

@mcp.tool()
async def recall_changed_since(
    query: str,
    since_iso: str,
    top_k: int = 10,
    category: Optional[str] = None,
    workspace_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Audit recall: returns memories created, updated, or superseded after a specific timestamp.
    since_iso: ISO 8601 string, e.g. '2026-09-11T00:00:00Z'.
    """
    from datetime import datetime
    svc = get_container()
    resolved_workspace = workspace_id or detect_project_workspace()
    since_dt = datetime.fromisoformat(since_iso.replace("Z", "+00:00"))

    req = RecallRequest(
        query=query,
        top_k=top_k,
        category=category,
        workspace_id=resolved_workspace,
        changed_since=since_dt
    )
    from elephantine.api.routes.memory import recall_endpoint
    res = await recall_endpoint(req, svc)
    return [
        {
            "id": m.id,
            "content": m.content,
            "workspace_id": m.workspace_id,
            "category": m.category,
            "created_at": m.created_at.isoformat()
        }
        for m in res.memories
    ]

@mcp.tool()
async def answer_query(
    question: str,
    top_k: int = 5,
    category: Optional[str] = None,
    workspace_id: Optional[str] = None
) -> str:
    """
    Direct synthesized memory answering: recalls relevant project context
    and returns a structured, factual answer with cited memories.
    """
    memories = await recall_context(
        query=question,
        top_k=top_k,
        category=category,
        workspace_id=workspace_id
    )
    if not memories:
        return "No relevant memories or facts found in project history for this query."

    from elephantine.core.gguf_extractor import LlamaCppEngine
    engine = LlamaCppEngine.get_instance()
    return engine.synthesize_answer(question, memories)

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
