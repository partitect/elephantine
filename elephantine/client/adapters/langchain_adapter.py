from typing import Any, Dict, List, Optional
from elephantine.client.client import ElephantineClient

class ElephantineLangChainMemory:
    """
    LangChain compatible memory adapter for Elephantine COGNITIVE Memory Engine.
    Seamlessly persists conversation context and injects relevant recalled memory.
    """
    def __init__(
        self,
        client: Optional[ElephantineClient] = None,
        base_url: str = "http://127.0.0.1:8765",
        workspace_id: str = "default",
        memory_key: str = "history",
        input_key: str = "input",
        source_agent: str = "langchain_agent",
        top_k: int = 3
    ):
        self.client = client or ElephantineClient(base_url=base_url)
        self.workspace_id = workspace_id
        self.memory_key = memory_key
        self.input_key = input_key
        self.source_agent = source_agent
        self.top_k = top_k

    @property
    def memory_variables(self) -> List[str]:
        return [self.memory_key]

    def load_memory_variables(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        query = inputs.get(self.input_key, "")
        if not query:
            return {self.memory_key: ""}

        res = self.client.recall(
            query=query,
            top_k=self.top_k,
            source_agent=self.source_agent,
            workspace_id=self.workspace_id
        )
        memories = res.get("memories", [])
        if not memories:
            return {self.memory_key: ""}

        formatted = "\n".join([f'- {m.get("content", "")}' for m in memories])
        return {self.memory_key: formatted}

    def save_context(self, inputs: Dict[str, Any], outputs: Dict[str, Any]) -> None:
        user_input = inputs.get(self.input_key, "").strip()
        agent_output = next(iter(outputs.values()), "").strip() if outputs else ""
        if user_input:
            self.client.remember(
                content=f"User: {user_input}",
                category="conversation",
                source_agent=self.source_agent,
                workspace_id=self.workspace_id
            )
        if agent_output:
            self.client.remember(
                content=f"Assistant: {agent_output}",
                category="conversation",
                source_agent=self.source_agent,
                workspace_id=self.workspace_id
            )

    def clear(self) -> None:
        pass
