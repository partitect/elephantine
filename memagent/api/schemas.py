"""Pydantic schemas for MemAgent API & Internal Primitives."""
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class MemoryItemBase(BaseModel):
    content: str = Field(..., description="The textual content or fact of the memory")
    source_agent: str = Field(default="default", description="Originating agent or system id")
    entity_key: Optional[str] = Field(default=None, description="Optional key for entity alignment e.g. user_preference:theme")
    category: str = Field(default="general", description="Category: fact, preference, procedural, episodic")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional custom key-value metadata")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Extraction confidence score")
    ttl_hours: Optional[float] = Field(default=None, description="Optional TTL in hours before expiry")

class RememberRequest(MemoryItemBase):
    pass

class RememberResponse(BaseModel):
    id: str
    status: str = "stored"
    conflicts_resolved: List[str] = Field(default_factory=list, description="IDs of older memories deprecated due to conflict")
    created_at: datetime
    message: str = "Memory committed successfully"

class RecallRequest(BaseModel):
    query: str = Field(..., description="Query string to search memory with")
    source_agent: Optional[str] = Field(default=None, description="Filter memories by specific agent")
    category: Optional[str] = Field(default=None, description="Filter memories by category")
    top_k: int = Field(default=5, ge=1, le=50, description="Maximum items to recall")
    use_time_decay: bool = Field(default=True, description="Apply exponential temporal recency decay")
    alpha: float = Field(default=0.7, ge=0.0, le=1.0, description="Weight between dense vector and sparse BM25")

class RecalledMemory(BaseModel):
    id: str
    content: str
    source_agent: str
    entity_key: Optional[str]
    category: str
    metadata: Dict[str, Any]
    confidence: float
    vector_score: float
    bm25_score: float
    hybrid_score: float
    decayed_score: float
    created_at: datetime
    version: int

class RecallResponse(BaseModel):
    query: str
    total_found: int
    memories: List[RecalledMemory]
    latency_ms: float

class ToolCallExecution(BaseModel):
    session_id: str
    agent_id: str = "default"
    tool_name: str
    tool_input: Dict[str, Any]
    tool_output: Optional[Dict[str, Any]] = None
    status: str = "success"
    error_message: Optional[str] = None
    execution_time_ms: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class WorkflowSnippet(BaseModel):
    id: str
    pattern_name: str
    description: str
    step_sequence: List[Dict[str, Any]]
    success_count: int = 1
    failure_count: int = 0
    last_used: datetime
