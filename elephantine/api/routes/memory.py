import re
import json
import uuid
import time
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from elephantine.config import settings
from elephantine.api.schemas import (
    RememberRequest,
    RememberResponse,
    RecallRequest,
    RecallResponse,
    RecalledMemory,
    ToolCallExecution,
    WorkflowSnippet,
    GraphTripletSchema,
    GraphQueryRequest,
    GraphQueryResponse,
    ConsolidateRequest,
    ConsolidateResponse,
    PruneResponse,
    ProactiveTriggerCreate,
    ProactiveTriggerResponse,
    ProactiveAlert
)
from elephantine.core.embedder import OnnxCpuEmbedder
from elephantine.core.extractor import TwoStageMemoryExtractor
from elephantine.core.graph_extractor import RuleBasedGraphExtractor
from elephantine.core.scoring import HybridScorer
from elephantine.core.conflict import ConflictResolver
from elephantine.storage.sqlite_store import SqliteMetadataStore
from elephantine.storage.lancedb_store import LanceDbVectorStore
from elephantine.core.auth_interface import TenantContext
from elephantine.api.middleware.auth import require_write_permission, require_read_permission

from elephantine.storage.procedural_store import ProceduralMemoryStore
from elephantine.core.buffer import AsyncMemoryWriteBuffer
from elephantine.core.consolidator import MemoryConsolidator
from elephantine.core.proactive import ProactiveEngine, parse_trigger_condition

router = APIRouter()

# Singletons / Dependency Container
class ServiceContainer:
    def __init__(self):
        self.sqlite_store = SqliteMetadataStore()
        self.lancedb_store = LanceDbVectorStore()
        self.procedural_store = ProceduralMemoryStore()
        self.embedder = OnnxCpuEmbedder()
        self.extractor = TwoStageMemoryExtractor()
        self.graph_extractor = RuleBasedGraphExtractor()
        self.scorer = HybridScorer()
        self.conflict_resolver = ConflictResolver(self.sqlite_store)
        self.write_buffer = AsyncMemoryWriteBuffer(self.sqlite_store, self.lancedb_store)
        self.consolidator = MemoryConsolidator(self.sqlite_store)
        self.proactive_engine = ProactiveEngine(self.sqlite_store)

_container: Optional[ServiceContainer] = None

def get_container() -> ServiceContainer:
    global _container
    if _container is None:
        _container = ServiceContainer()
    return _container

@router.post("/remember", response_model=RememberResponse)
async def remember_endpoint(
    req: RememberRequest,
    svc: ServiceContainer = Depends(get_container),
    _auth: TenantContext = Depends(require_write_permission)
):
    """
    1. Pre-filter / Heuristic Extraction.
    2. ONNX CPU Vectorization.
    3. Conflict detection and LWW Soft-deprecation.
    4. Atomic persistence in LanceDB and SQLite WAL.
    """
    extraction = svc.extractor.extract_structured(req.content, default_category=req.category)
    entity_key = req.entity_key or extraction["entity_key"]
    category = extraction["category"]
    content = extraction["cleaned_content"]

    vector = svc.embedder.embed_text(content)
    now = datetime.now(timezone.utc)
    created_at_epoch = now.timestamp()
    memory_id = str(uuid.uuid4())

    candidates = svc.lancedb_store.search_similar(vector, top_k=10)
    conflicts_resolved = await svc.conflict_resolver.detect_and_resolve_conflicts(
        new_memory_id=memory_id,
        entity_key=entity_key,
        category=category,
        similar_memories=candidates,
        workspace_id=req.workspace_id,
        role_authority=req.role_authority
    )

    # Sync LanceDB vector store so deprecated memories don't pollute dense search
    for deprecated_id in conflicts_resolved:
        svc.lancedb_store.delete_memory(deprecated_id)

    expires_at = now + timedelta(hours=req.ttl_hours) if req.ttl_hours else None
    await svc.sqlite_store.insert_memory(
        memory_id=memory_id,
        content=content,
        source_agent=req.source_agent,
        entity_key=entity_key,
        category=category,
        confidence=req.confidence if req.confidence < 1.0 else extraction["confidence"],
        metadata=req.metadata,
        created_at=now,
        expires_at=expires_at,
        workspace_id=req.workspace_id,
        role_authority=req.role_authority
    )

    svc.lancedb_store.add_vector(
        memory_id=memory_id,
        vector=vector,
        source_agent=req.source_agent,
        category=category,
        created_at_epoch=created_at_epoch
    )

    # Extract knowledge graph triplets and persist in SQLite
    triplets = svc.graph_extractor.extract_triplets(req.content)
    for trip in triplets:
        t_id = str(uuid.uuid4())
        await svc.sqlite_store.insert_triplet(
            triplet_id=t_id,
            subject=trip.subject,
            predicate=trip.predicate,
            object_=trip.object,
            source_memory_id=memory_id,
            confidence=trip.confidence
        )

    return RememberResponse(
        id=memory_id,
        status="stored",
        conflicts_resolved=conflicts_resolved,
        created_at=now,
        message=f"Memory committed successfully with {len(conflicts_resolved)} conflict(s) superseded."
    )

@router.post("/recall", response_model=RecallResponse)
async def recall_endpoint(
    req: RecallRequest,
    svc: ServiceContainer = Depends(get_container),
    _auth: TenantContext = Depends(require_read_permission)
):
    """
    1. Dense Vector search via LanceDB.
    2. BM25 search via SQLite FTS5.
    3. Hybrid scoring fusion & Exponential temporal decay.
    4. Batch SQLite metadata retrieval.
    """
    t0 = time.perf_counter()

    query_vector = svc.embedder.embed_text(req.query)

    dense_results = svc.lancedb_store.search_similar(
        query_vector=query_vector,
        top_k=settings.DENSE_SEARCH_TOP_K,
        source_agent=req.source_agent,
        category=req.category
    )

    bm25_results = await svc.sqlite_store.search_bm25(
        query=req.query,
        top_k=settings.BM25_SEARCH_TOP_K
    )

    ranked = svc.scorer.fuse_and_rank(
        dense_results=dense_results,
        bm25_results=bm25_results,
        alpha=req.alpha,
        use_time_decay=req.use_time_decay
    )

    # Batch fetch candidates metadata from SQLite in single query
    # Retrieve sufficient candidates so that active memories are found even when historical versions exist
    top_candidates = ranked[:max(100, req.top_k * 10)]
    top_ids = [item["id"] for item in top_candidates]
    metadata_map = await svc.sqlite_store.get_memories_batch(top_ids)

    final_memories = []
    for item in top_candidates:
        if len(final_memories) >= req.top_k:
            break
        meta = metadata_map.get(item["id"])
        if not meta or meta.get("is_active") != 1:
            continue

        if req.workspace_id and meta.get("workspace_id", "default") != req.workspace_id:
            continue
        if req.source_agent and meta.get("source_agent") != req.source_agent:
            continue
        if req.category and meta.get("category") != req.category:
            continue

        created_at = datetime.fromisoformat(meta["created_at"])
        final_memories.append(RecalledMemory(
            id=meta["id"],
            content=meta["content"],
            source_agent=meta["source_agent"],
            workspace_id=meta.get("workspace_id", "default"),
            role_authority=float(meta.get("role_authority", 0.5)),
            entity_key=meta.get("entity_key"),
            category=meta["category"],
            metadata=json.loads(meta.get("metadata_json", "{}")),
            confidence=meta.get("confidence", 1.0),
            vector_score=item["vector_score"],
            bm25_score=item["bm25_score"],
            hybrid_score=item["hybrid_score"],
            decayed_score=item["decayed_score"],
            created_at=created_at,
            version=meta.get("version", 1)
        ))

    # Re-rank final memories by role authority (higher authority wins) combined with relevance
    final_memories.sort(
        key=lambda m: (m.role_authority * 0.4) + (m.decayed_score * 0.6),
        reverse=True
    )
    final_memories = final_memories[:req.top_k]

    # Graph Memory Enrichment: check for entity triplets mentioned in query
    graph_triplets = []
    query_words = [w.strip().lower() for w in re.findall(r"\w+", req.query) if len(w) > 2]
    for w in query_words[:3]:
        neighborhood = await svc.sqlite_store.get_entity_neighborhood(w, max_hops=1)
        for trip in neighborhood:
            if not any(gt.id == trip["id"] for gt in graph_triplets):
                graph_triplets.append(GraphTripletSchema(
                    id=trip["id"],
                    subject=trip["subject"],
                    predicate=trip["predicate"],
                    object=trip["object"],
                    source_memory_id=trip.get("source_memory_id"),
                    confidence=trip.get("confidence", 1.0)
                ))

    latency_ms = round((time.perf_counter() - t0) * 1000.0, 2)
    return RecallResponse(
        query=req.query,
        total_found=len(final_memories),
        memories=final_memories,
        graph_triplets=graph_triplets,
        latency_ms=latency_ms
    )

@router.post("/graph/query", response_model=GraphQueryResponse)
async def query_graph_endpoint(
    req: GraphQueryRequest,
    svc: ServiceContainer = Depends(get_container)
):
    """Multi-hop knowledge graph neighborhood traversal for an entity."""
    triplets_raw = await svc.sqlite_store.get_entity_neighborhood(req.entity, max_hops=req.max_hops)
    formatted = [
        GraphTripletSchema(
            id=r["id"],
            subject=r["subject"],
            predicate=r["predicate"],
            object=r["object"],
            source_memory_id=r.get("source_memory_id"),
            confidence=r.get("confidence", 1.0)
        )
        for r in triplets_raw
    ]
    return GraphQueryResponse(
        entity=req.entity,
        triplets=formatted,
        total_triplets=len(formatted)
    )

@router.post("/procedural/track")
async def track_tool_call(
    call: ToolCallExecution,
    svc: ServiceContainer = Depends(get_container)
):
    call_id = await svc.procedural_store.record_tool_call(call)
    return {"status": "recorded", "call_id": call_id}

@router.get("/procedural/session/{session_id}")
async def get_session_tool_calls(
    session_id: str,
    svc: ServiceContainer = Depends(get_container)
):
    history = await svc.procedural_store.get_session_history(session_id)
    return {"session_id": session_id, "executions": history}

@router.post("/procedural/workflow")
async def save_workflow(
    workflow: WorkflowSnippet,
    svc: ServiceContainer = Depends(get_container)
):
    wf_id = await svc.procedural_store.save_or_update_workflow(
        pattern_name=workflow.pattern_name,
        description=workflow.description,
        steps=workflow.step_sequence,
        success=True
    )
    return {"status": "saved", "workflow_id": wf_id}

@router.get("/procedural/workflow/{pattern_name}")
async def get_workflow(
    pattern_name: str,
    svc: ServiceContainer = Depends(get_container)
):
    wf = await svc.procedural_store.get_workflow(pattern_name)
    if not wf:
        raise HTTPException(status_code=404, detail=f"Workflow pattern '{pattern_name}' not found")
    return wf

@router.post("/memories/consolidate", response_model=ConsolidateResponse)
async def consolidate_memories_endpoint(
    req: ConsolidateRequest,
    svc: ServiceContainer = Depends(get_container)
):
    """
    Consolidates fragmented facts for an entity into a unified canonical summary,
    preventing long-term memory bloat.
    """
    res = await svc.consolidator.consolidate_entity(
        entity_key=req.entity_key,
        workspace_id=req.workspace_id
    )
    if not res:
        return ConsolidateResponse(
            status="no_consolidation_needed",
            entity_key=req.entity_key,
            consolidated_count=0
        )
    return ConsolidateResponse(
        status="consolidated",
        canonical_id=res["canonical_id"],
        entity_key=res["entity_key"],
        consolidated_count=res["consolidated_count"],
        canonical_content=res["canonical_content"]
    )

@router.post("/memories/prune", response_model=PruneResponse)
async def prune_memories_endpoint(
    older_than_days: int = Query(default=30, ge=1),
    workspace_id: Optional[str] = Query(default=None),
    svc: ServiceContainer = Depends(get_container)
):
    """
    Prunes deprecated/superseded memories older than N days from storage.
    """
    pruned_count = await svc.consolidator.prune_all_inactive(
        older_than_days=older_than_days,
        workspace_id=workspace_id
    )
    return PruneResponse(
        pruned_count=pruned_count,
        older_than_days=older_than_days,
        workspace_id=workspace_id,
        message=f"Pruned {pruned_count} deprecated memories older than {older_than_days} days."
    )

# =============================================================================
# PROACTIVE MEMORY TRIGGER ENDPOINTS
# =============================================================================

@router.post("/proactive/triggers", response_model=ProactiveTriggerResponse)
async def create_proactive_trigger_endpoint(
    req: ProactiveTriggerCreate,
    svc: ServiceContainer = Depends(get_container)
):
    """
    Registers a proactive memory trigger. If content is provided without memory_id,
    persists a memory item first and attaches the trigger to it.
    """
    memory_id = req.memory_id
    now = datetime.now(timezone.utc)

    if not memory_id:
        if not req.content:
            raise HTTPException(status_code=422, detail="Either 'memory_id' or 'content' must be provided.")
        memory_id = str(uuid.uuid4())
        vec = svc.embedder.embed_text(req.content)
        await svc.sqlite_store.insert_memory(
            memory_id=memory_id,
            content=req.content,
            source_agent=req.target_agent,
            entity_key=None,
            category="proactive",
            confidence=1.0,
            metadata={"trigger_condition": req.condition_value},
            created_at=now,
            workspace_id=req.workspace_id,
            role_authority=0.8
        )
        svc.lancedb_store.add_vector(
            memory_id=memory_id,
            vector=vec,
            source_agent=req.target_agent,
            category="proactive",
            created_at_epoch=now.timestamp()
        )

    next_trigger_at, _ = parse_trigger_condition(
        req.trigger_type,
        req.condition_value,
        reference_time=now
    )

    t_id = str(uuid.uuid4())
    await svc.sqlite_store.create_proactive_trigger(
        trigger_id=t_id,
        memory_id=memory_id,
        trigger_type=req.trigger_type,
        condition_value=req.condition_value,
        target_agent=req.target_agent,
        workspace_id=req.workspace_id,
        webhook_url=req.webhook_url,
        next_trigger_at=next_trigger_at
    )

    return ProactiveTriggerResponse(
        trigger_id=t_id,
        memory_id=memory_id,
        status="created",
        next_trigger_at=next_trigger_at,
        message="Proactive memory trigger registered successfully."
    )

@router.get("/proactive/pending", response_model=List[ProactiveAlert])
async def get_pending_proactive_alerts(
    target_agent: str = Query(default="default"),
    workspace_id: Optional[str] = Query(default=None),
    svc: ServiceContainer = Depends(get_container)
):
    """
    Fetches unacknowledged proactive alerts for an agent (pull-based check-in).
    """
    triggers = await svc.sqlite_store.get_pending_triggers_for_agent(
        target_agent=target_agent,
        workspace_id=workspace_id
    )
    alerts = []
    for t in triggers:
        alerts.append(ProactiveAlert(
            trigger_id=t["id"],
            memory_id=t["memory_id"],
            content=t["memory_content"],
            category=t.get("memory_category", "general"),
            workspace_id=t["workspace_id"],
            target_agent=t["target_agent"],
            role_authority=float(t.get("role_authority", 0.5)),
            condition=t["condition_value"],
            triggered_at=datetime.fromisoformat(t["last_triggered_at"]) if t.get("last_triggered_at") else datetime.now(timezone.utc),
            is_recurring=bool(t.get("next_trigger_at")),
            next_trigger_at=datetime.fromisoformat(t["next_trigger_at"]) if t.get("next_trigger_at") else None
        ))
    return alerts

@router.post("/proactive/acknowledge/{trigger_id}")
async def acknowledge_proactive_alert(
    trigger_id: str,
    svc: ServiceContainer = Depends(get_container)
):
    """
    Marks a proactive trigger alert as acknowledged by the receiving agent.
    """
    success = await svc.sqlite_store.acknowledge_trigger(trigger_id)
    if not success:
        raise HTTPException(status_code=404, detail="Alert not found or already acknowledged.")
    return {"status": "acknowledged", "trigger_id": trigger_id}

@router.get("/proactive/stream")
async def stream_proactive_alerts(
    svc: ServiceContainer = Depends(get_container)
):
    """
    Server-Sent Events (SSE) stream allowing agents to listen in real time for proactive alerts.
    """
    from fastapi.responses import StreamingResponse

    async def event_generator():
        q = svc.proactive_engine.subscribe_listener()
        try:
            while True:
                alert = await q.get()
                yield f"data: {json.dumps(alert, ensure_ascii=False)}\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            svc.proactive_engine.unsubscribe_listener(q)

    return StreamingResponse(event_generator(), media_type="text/event-stream")

