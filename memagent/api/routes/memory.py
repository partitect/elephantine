import re
import json
import uuid
import time
from datetime import datetime, timezone, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from memagent.config import settings
from memagent.api.schemas import (
    RememberRequest,
    RememberResponse,
    RecallRequest,
    RecallResponse,
    RecalledMemory,
    ToolCallExecution,
    WorkflowSnippet,
    GraphTripletSchema,
    GraphQueryRequest,
    GraphQueryResponse
)
from memagent.core.embedder import OnnxCpuEmbedder
from memagent.core.extractor import TwoStageMemoryExtractor
from memagent.core.graph_extractor import RuleBasedGraphExtractor
from memagent.core.scoring import HybridScorer
from memagent.core.conflict import ConflictResolver
from memagent.storage.sqlite_store import SqliteMetadataStore
from memagent.storage.lancedb_store import LanceDbVectorStore
from memagent.storage.procedural_store import ProceduralMemoryStore

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

_container: Optional[ServiceContainer] = None

def get_container() -> ServiceContainer:
    global _container
    if _container is None:
        _container = ServiceContainer()
    return _container

@router.post("/remember", response_model=RememberResponse)
async def remember_endpoint(
    req: RememberRequest,
    svc: ServiceContainer = Depends(get_container)
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
        similar_memories=candidates
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
        expires_at=expires_at
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
    svc: ServiceContainer = Depends(get_container)
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

        if req.source_agent and meta.get("source_agent") != req.source_agent:
            continue
        if req.category and meta.get("category") != req.category:
            continue

        created_at = datetime.fromisoformat(meta["created_at"])
        final_memories.append(RecalledMemory(
            id=meta["id"],
            content=meta["content"],
            source_agent=meta["source_agent"],
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
