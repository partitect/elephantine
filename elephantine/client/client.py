import httpx
from typing import Any, Dict, List, Optional

class ElephantineClient:
    """
    Synchronous Python Client for Elephantine COGNITIVE CPU-Native Memory Engine.
    """
    def __init__(self, base_url: str = "http://127.0.0.1:8765", timeout: float = 10.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client = httpx.Client(base_url=self.base_url, timeout=self.timeout)

    def close(self):
        self._client.close()

    def __enter__(self) -> "ElephantineClient":
        return self

    def __exit__(self, xc_type, xc_val, xc_tb):
        self.close()

    def remember(
        self,
        content: str,
        category: str = "general",
        source_agent: str = "default",
        entity_key: Optional[str] = None,
        workspace_id: str = "default",
        role_authority: float = 0.5,
        ttl_hours: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        payload = {
            "content": content,
            "category": category,
            "source_agent": source_agent,
            "entity_key": entity_key,
            "workspace_id": workspace_id,
            "role_authority": role_authority,
            "ttl_hours": ttl_hours,
            "metadata": metadata or {}
        }
        resp = self._client.post("/remember", json=payload)
        resp.raise_for_status()
        return resp.json()

    def recall(
        self,
        query: str,
        top_k: int = 5,
        workspace_id: Optional[str] = None,
        source_agent: Optional[str] = None,
        category: Optional[str] = None,
        alpha: float = 0.7,
        use_time_decay: bool = True
    ) -> Dict[str, Any]:
        payload = {
            "query": query,
            "top_k": top_k,
            "workspace_id": workspace_id,
            "source_agent": source_agent,
            "category": category,
            "alpha": alpha,
            "use_time_decay": use_time_decay
        }
        resp = self._client.post("/recall", json=payload)
        resp.raise_for_status()
        return resp.json()

    def query_graph(self, entity: str, max_hops: int = 2) -> Dict[str, Any]:
        resp = self._client.post("/graph/query", json={"entity": entity, "max_hops": max_hops})
        resp.raise_for_status()
        return resp.json()

    def get_stats(self) -> Dict[str, Any]:
        resp = self._client.get("/api/v1/stats")
        resp.raise_for_status()
        return resp.json()

    def create_trigger(
        self,
        condition: str,
        content: Optional[str] = None,
        memory_id: Optional[str] = None,
        trigger_type: str = "datetime",
        target_agent: str = "default",
        workspace_id: str = "default",
        webhook_url: Optional[str] = None
    ) -> Dict[str, Any]:
        payload = {
            "condition_value": condition,
            "content": content,
            "memory_id": memory_id,
            "trigger_type": trigger_type,
            "target_agent": target_agent,
            "workspace_id": workspace_id,
            "webhook_url": webhook_url
        }
        resp = self._client.post("/proactive/triggers", json=payload)
        resp.raise_for_status()
        return resp.json()

    def get_pending_alerts(
        self,
        target_agent: str = "default",
        workspace_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        params = {"target_agent": target_agent}
        if workspace_id:
            params["workspace_id"] = workspace_id
        resp = self._client.get("/proactive/pending", params=params)
        resp.raise_for_status()
        return resp.json()

    def acknowledge_alert(self, trigger_id: str) -> Dict[str, Any]:
        resp = self._client.post(f"/proactive/acknowledge/{trigger_id}")
        resp.raise_for_status()
        return resp.json()


class AsyncElephantineClient:
    """
    Asynchronous Python Client for Elephantine COGNITIVE CPU-Native Memory Engine.
    """
    def __init__(self, base_url: str = "http://127.0.0.1:8765", timeout: float = 10.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client = httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout)

    async def close(self):
        await self._client.aclose()

    async def __aenter__(self) -> "AsyncElephantineClient":
        return self

    async def __aexit__(self, xc_type, xc_val, xc_tb):
        await self.close()

    async def remember(
        self,
        content: str,
        category: str = "general",
        source_agent: str = "default",
        entity_key: Optional[str] = None,
        workspace_id: str = "default",
        role_authority: float = 0.5,
        ttl_hours: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        payload = {
            "content": content,
            "category": category,
            "source_agent": source_agent,
            "entity_key": entity_key,
            "workspace_id": workspace_id,
            "role_authority": role_authority,
            "ttl_hours": ttl_hours,
            "metadata": metadata or {}
        }
        resp = await self._client.post("/remember", json=payload)
        resp.raise_for_status()
        return resp.json()

    async def recall(
        self,
        query: str,
        top_k: int = 5,
        workspace_id: Optional[str] = None,
        source_agent: Optional[str] = None,
        category: Optional[str] = None,
        alpha: float = 0.7,
        use_time_decay: bool = True
    ) -> Dict[str, Any]:
        payload = {
            "query": query,
            "top_k": top_k,
            "workspace_id": workspace_id,
            "source_agent": source_agent,
            "category": category,
            "alpha": alpha,
            "use_time_decay": use_time_decay
        }
        resp = await self._client.post("/recall", json=payload)
        resp.raise_for_status()
        return resp.json()

    async def query_graph(self, entity: str, max_hops: int = 2) -> Dict[str, Any]:
        resp = await self._client.post("/graph/query", json={"entity": entity, "max_hops": max_hops})
        resp.raise_for_status()
        return resp.json()

    async def create_trigger(
        self,
        condition: str,
        content: Optional[str] = None,
        memory_id: Optional[str] = None,
        trigger_type: str = "datetime",
        target_agent: str = "default",
        workspace_id: str = "default",
        webhook_url: Optional[str] = None
    ) -> Dict[str, Any]:
        payload = {
            "condition_value": condition,
            "content": content,
            "memory_id": memory_id,
            "trigger_type": trigger_type,
            "target_agent": target_agent,
            "workspace_id": workspace_id,
            "webhook_url": webhook_url
        }
        resp = await self._client.post("/proactive/triggers", json=payload)
        resp.raise_for_status()
        return resp.json()

    async def get_pending_alerts(
        self,
        target_agent: str = "default",
        workspace_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        params = {"target_agent": target_agent}
        if workspace_id:
            params["workspace_id"] = workspace_id
        resp = await self._client.get("/proactive/pending", params=params)
        resp.raise_for_status()
        return resp.json()

    async def acknowledge_alert(self, trigger_id: str) -> Dict[str, Any]:
        resp = await self._client.post(f"/proactive/acknowledge/{trigger_id}")
        resp.raise_for_status()
        return resp.json()
