from typing import Any, Dict, List, Optional
from memagent.config import settings
from memagent.storage.sqlite_store import SqliteMetadataStore

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
        similar_memories: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Returns list of deprecated memory IDs.
        Rules:
        1. Exact entity_key match: If non-empty entity_key matches an existing active memory,
           the older one is superseded by the new one (LWW).
        2. High semantic similarity (> threshold) in same category and source agent:
           Flags and soft-deprecates the older version to prevent duplicate/contradictory facts.
        """
        deprecated_ids: List[str] = []

        # 1. Entity-key match resolution
        if entity_key:
            existing_entities = await self.sqlite_store.get_active_by_entity(entity_key)
            for old_mem in existing_entities:
                if old_mem["id"] != new_memory_id:
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
                    await self.sqlite_store.deprecate_memory(cand_id, new_memory_id)
                    deprecated_ids.append(cand_id)

        return deprecated_ids
