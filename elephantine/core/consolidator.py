import logging
import uuid
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from elephantine.storage.sqlite_store import SqliteMetadataStore

logger = logging.getLogger(__name__)

class MemoryConsolidator:
    def __init__(self, sqlite_store: SqliteMetadataStore):
        self.sqlite_store = sqlite_store

    async def consolidate_entity(self, entity_key: str, workspace_id: str = 'default', source_agent: str = 'consolidator') -> Optional[Dict[str, Any]]:
        memories = await self.sqlite_store.get_active_memories_for_consolidation(entity_key=entity_key, workspace_id=workspace_id)
        if len(memories) <= 1:
            return None
        contents = [m['content'] for m in memories]
        merged_fact = ' ; '.join(contents)
        canonical_content = 'Consolidated profile for ' + entity_key + ': ' + merged_fact
        max_authority = max(float(m.get('role_authority', 0.5)) for m in memories)
        new_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        await self.sqlite_store.insert_memory(
            memory_id=new_id,
            content=canonical_content,
            source_agent=source_agent,
            entity_key=entity_key,
            category='consolidated',
            confidence=1.0,
            metadata={'consolidated_ids': [m['id'] for m in memories]},
            created_at=now,
            workspace_id=workspace_id,
            role_authority=max_authority
        )
        for m in memories:
            await self.sqlite_store.deprecate_memory(m['id'], new_id)
        return {
            'canonical_id': new_id,
            'entity_key': entity_key,
            'consolidated_count': len(memories),
            'canonical_content': canonical_content
        }

    async def prune_all_inactive(self, older_than_days: int = 30, workspace_id: Optional[str] = None) -> int:
        return await self.sqlite_store.prune_deprecated_memories(
            older_than_days=older_than_days,
            workspace_id=workspace_id
        )
