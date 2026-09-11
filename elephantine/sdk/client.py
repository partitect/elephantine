from typing import Any, Dict, List, Optional
import httpx

class MemAgentClient:
    """
    Lightweight Async Python SDK for interacting with the MemAgent engine.
    """
    def __init__(self, base_url: str = "http://127.0.0.1:8765"):
        self.base_url = base_url.rstrip("/")

    async def remember(
        self,
        content: str,
        category: str = "general",
        entity_key: Optional[str] = None,
        source_agent: str = "agent",
        metadata: Optional[Dict[str, Any]] = None,
        ttl_hours: Optional[float] = None
    ) -> Dict[str, Any]:
        async with httpx.AsyncClient(base_url=self.base_url, timeout=10.0) as client:
            resp = await client.post("/remember", json={
                "content": content,
                "category": category,
                "entity_key": entity_key,
                "source_agent": source_agent,
                "metadata": metadata or {},
                "ttl_hours": ttl_hours
            })
            resp.raise_for_status()
            return resp.json()

    async def recall(
        self,
        query: str,
        top_k: int = 5,
        category: Optional[str] = None,
        source_agent: Optional[str] = None,
        alpha: float = 0.7,
        use_time_decay: bool = True
    ) -> Dict[str, Any]:
        async with httpx.AsyncClient(base_url=self.base_url, timeout=10.0) as client:
            resp = await client.post("/recall", json={
                "query": query,
                "top_k": top_k,
                "category": category,
                "source_agent": source_agent,
                "alpha": alpha,
                "use_time_decay": use_time_decay
            })
            resp.raise_for_status()
            return resp.json()

    async def track_tool_call(
        self,
        session_id: str,
        tool_name: str,
        tool_input: Dict[str, Any],
        tool_output: Optional[Dict[str, Any]] = None,
        status: str = "success",
        error_message: Optional[str] = None,
        execution_time_ms: float = 0.0,
        agent_id: str = "default"
    ) -> Dict[str, Any]:
        async with httpx.AsyncClient(base_url=self.base_url, timeout=10.0) as client:
            resp = await client.post("/procedural/track", json={
                "session_id": session_id,
                "agent_id": agent_id,
                "tool_name": tool_name,
                "tool_input": tool_input,
                "tool_output": tool_output,
                "status": status,
                "error_message": error_message,
                "execution_time_ms": execution_time_ms
            })
            resp.raise_for_status()
            return resp.json()
