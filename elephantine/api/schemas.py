"""Pydantic schemas for MemAgent API & Internal Primitives."""
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class MemoryItemBase(BaseModel):
    content: str = Field(..., description="The textual content or fact of the memory")
    source_agent: str = Field(default="default", description="Originating agent or system id")
    entity_key: Optional[str] = Field(default=None, description="Optional key for entity alignment e.g. user_preference:theme")
    category: str = Field(default="general", description="Category: fact, preference, procedural, episodic")
    workspace_id: str = Field(default="default", description="Shared workspace / team ID for multi-agent collaboration")
    role_authority: float = Field(default=0.5, ge=0.0, le=1.0, description="Role authority weight (Senior/Lead=1.0, Reviewer=0.8, Coder=0.6, Junior=0.4)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional custom key-value metadata")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Extraction confidence score")
    ttl_hours: Optional[float] = Field(default=None, description="Optional TTL in hours before expiry")

class RememberRequest(MemoryItemBase):
    custom_id: Optional[str] = Field(default=None, description="Optional caller-supplied memory ID (for lossless migrations)")
    created_at: Optional[datetime] = Field(default=None, description="Optional historical creation timestamp (for lossless migrations)")

class RememberResponse(BaseModel):
    id: str
    status: str = "stored"
    conflicts_resolved: List[str] = Field(default_factory=list, description="IDs of older memories deprecated due to conflict")
    created_at: datetime
    message: str = "Memory committed successfully"

class RecallRequest(BaseModel):
    query: str = Field(..., description="Query string to search memory with")
    workspace_id: Optional[str] = Field(default=None, description="Filter memories by workspace / team ID")
    source_agent: Optional[str] = Field(default=None, description="Filter memories by specific agent")
    category: Optional[str] = Field(default=None, description="Filter memories by category")
    top_k: int = Field(default=5, ge=1, le=50, description="Maximum items to recall")
    use_time_decay: bool = Field(default=True, description="Apply exponential temporal recency decay")
    alpha: float = Field(default=0.7, ge=0.0, le=1.0, description="Weight between dense vector and sparse BM25")
    as_of: Optional[datetime] = Field(default=None, description="Temporal recall: return memories valid as of this point in time")
    changed_since: Optional[datetime] = Field(default=None, description="Audit recall: return memories created or updated since this timestamp")

class RecalledMemory(BaseModel):
    id: str
    content: str
    source_agent: str
    workspace_id: str = "default"
    role_authority: float = 0.5
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

class GraphTripletSchema(BaseModel):
    id: str
    subject: str
    predicate: str
    object: str
    source_memory_id: Optional[str] = None
    confidence: float = 1.0

class GraphQueryRequest(BaseModel):
    entity: str
    max_hops: int = 2

class GraphQueryResponse(BaseModel):
    entity: str
    triplets: List[GraphTripletSchema]
    total_triplets: int

class RecallResponse(BaseModel):
    query: str
    total_found: int
    memories: List[RecalledMemory]
    graph_triplets: List[GraphTripletSchema] = Field(default_factory=list)
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

class ConsolidateRequest(BaseModel):
    entity_key: str
    workspace_id: str = "default"

class ConsolidateResponse(BaseModel):
    status: str
    canonical_id: Optional[str] = None
    entity_key: str
    consolidated_count: int = 0
    canonical_content: Optional[str] = None

class PruneResponse(BaseModel):
    pruned_count: int
    older_than_days: int
    workspace_id: Optional[str] = None
    message: str

# Proactive Memory Trigger Schemas
class ProactiveTriggerCreate(BaseModel):
    memory_id: Optional[str] = None
    content: Optional[str] = None
    trigger_type: str = Field(default="datetime", description="'datetime', 'interval', 'weekly', 'daily', 'event'")
    condition_value: str = Field(..., description="e.g. '2026-09-12T17:00:00Z', 'every:30m', 'weekly:FRI:17:00'")
    target_agent: str = Field(default="default", description="Agent ID to notify or 'all'")
    workspace_id: str = Field(default="default", description="Workspace isolation scope")
    webhook_url: Optional[str] = Field(default=None, description="Optional HTTP webhook URL to POST alert to")

class ProactiveAlert(BaseModel):
    trigger_id: str
    memory_id: str
    content: str
    category: str = "general"
    workspace_id: str = "default"
    target_agent: str = "default"
    role_authority: float = 0.5
    condition: str
    triggered_at: datetime
    is_recurring: bool = False
    next_trigger_at: Optional[datetime] = None

class ProactiveTriggerResponse(BaseModel):
    trigger_id: str
    memory_id: str
    status: str = "created"
    next_trigger_at: Optional[datetime] = None
    message: str = "Proactive trigger registered successfully"

