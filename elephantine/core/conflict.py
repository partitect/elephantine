from typing import Any, Dict, List, Optional
from elephantine.config import settings
from elephantine.storage.sqlite_store import SqliteMetadataStore

class ConflictResolver:
    """
    Identifies contradictory or superseding facts using entity-key alignment
    and semantic similarity, applying Last-Write-Wins (LWW) with soft-deprecation.
    """
    def __init__(self, sqlite_store: SqliteMetadataStore, similarity_threshold: float = settings.SEMANTIC_SIMILARITY_THRESHOLD):
        self.sqlite_store = sqlite_store
        self.similarity_threshold = similarity_threshold

    async def detect_and_resolve_conflicts(
        self,
        new_memory_id: str,
        entity_key: Optional[str],
        category: str,
        similar_memories: List[Dict[str, Any]],
        workspace_id: str = "default",
        role_authority: float = 0.5
    ) -> List[str]:
        """
        Returns list of deprecated memory IDs.
        Rules:
        1. Role Authority Consensus: A new memory can only supersede an existing active memory
           if new_authority >= existing_authority.
        2. Exact entity_key match within the same workspace_id.
        3. High semantic similarity (> threshold) within the same category and workspace.
        """
        deprecated_ids: List[str] = []

        # 1. Entity-key match resolution
        if entity_key:
            existing_entities = await self.sqlite_store.get_active_by_entity(entity_key, workspace_id=workspace_id)
            for old_mem in existing_entities:
                if old_mem["id"] != new_memory_id:
                    old_auth = float(old_mem.get("role_authority", 0.5))
                    # Only supersede if incoming authority is equal or higher
                    if role_authority >= old_auth:
                        await self.sqlite_store.deprecate_memory(old_mem["id"], new_memory_id)
                        deprecated_ids.append(old_mem["id"])

        # 2. Semantic collision resolution (e.g. "User lives in Berlin" vs "User moved to Munich")
        for candidate in similar_memories:
            cand_id = candidate["id"]
            if cand_id == new_memory_id or cand_id in deprecated_ids:
                continue

            sim = candidate.get("cosine_similarity", 0.0)
            cand_cat = candidate.get("category", "")
            
            # If high semantic collision in the same category
            if sim >= self.similarity_threshold and cand_cat == category:
                old_mem = await self.sqlite_store.get_memory_by_id(cand_id)
                if old_mem and old_mem.get("is_active") == 1:
                    # Check workspace matching
                    if old_mem.get("workspace_id", "default") == workspace_id:
                        old_auth = float(old_mem.get("role_authority", 0.5))
                        if role_authority >= old_auth:
                            await self.sqlite_store.deprecate_memory(cand_id, new_memory_id)
                            deprecated_ids.append(cand_id)

        return deprecated_ids
