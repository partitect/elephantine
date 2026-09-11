import json
import sqlite3
import aiosqlite
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from memagent.config import settings

class SqliteMetadataStore:
    """
    SQLite Embedded Metadata & Graph / Temporal Engine.
    Configured with WAL mode, foreign keys, and FTS5 for hybrid full-text indexing.
    """
    def __init__(self, db_path: Path = settings.sqlite_path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db_sync()

    def _init_db_sync(self):
        """Synchronous migration / table creation on startup."""
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("PRAGMA foreign_keys=ON;")

        with conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    source_agent TEXT NOT NULL,
                    entity_key TEXT,
                    category TEXT NOT NULL DEFAULT 'general',
                    confidence REAL NOT NULL DEFAULT 1.0,
                    metadata_json TEXT NOT NULL DEFAULT '{}',
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL,
                    expires_at TIMESTAMP,
                    version INTEGER NOT NULL DEFAULT 1,
                    is_active INTEGER NOT NULL DEFAULT 1,
                    deprecated_by TEXT
                );
            """)

            conn.execute("CREATE INDEX IF NOT EXISTS idx_memories_entity ON memories(entity_key, is_active);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_memories_source ON memories(source_agent, is_active);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_memories_created ON memories(created_at);")

            conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts USING fts5(
                    id UNINDEXED,
                    content,
                    tokenize = 'porter unicode61'
                );
            """)

            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS trg_memories_ai AFTER INSERT ON memories BEGIN
                    INSERT INTO memories_fts(id, content) VALUES (new.id, new.content);
                END;
            """)
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS trg_memories_ad AFTER DELETE ON memories BEGIN
                    DELETE FROM memories_fts WHERE id = old.id;
                END;
            """)
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS trg_memories_au AFTER UPDATE ON memories BEGIN
                    DELETE FROM memories_fts WHERE id = old.id;
                    INSERT INTO memories_fts(id, content) VALUES (new.id, new.content);
                END;
            """)
        conn.close()

    async def insert_memory(
        self,
        memory_id: str,
        content: str,
        source_agent: str,
        entity_key: Optional[str],
        category: str,
        confidence: float,
        metadata: Dict[str, Any],
        created_at: datetime,
        expires_at: Optional[datetime] = None
    ) -> None:
        async with aiosqlite.connect(str(self.db_path)) as db:
            await db.execute("PRAGMA foreign_keys=ON;")
            await db.execute("""
                INSERT INTO memories (
                    id, content, source_agent, entity_key, category, confidence,
                    metadata_json, created_at, updated_at, expires_at, version, is_active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 1)
            """, (
                memory_id,
                content,
                source_agent,
                entity_key,
                category,
                confidence,
                json.dumps(metadata, ensure_ascii=False),
                created_at.isoformat(),
                created_at.isoformat(),
                expires_at.isoformat() if expires_at else None
            ))
            await db.commit()

    async def get_active_by_entity(self, entity_key: str) -> List[Dict[str, Any]]:
        if not entity_key:
            return []
        async with aiosqlite.connect(str(self.db_path)) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT * FROM memories WHERE entity_key = ? AND is_active = 1
            """, (entity_key,))
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def deprecate_memory(self, memory_id: str, new_memory_id: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        async with aiosqlite.connect(str(self.db_path)) as db:
            await db.execute("""
                UPDATE memories
                SET is_active = 0, updated_at = ?, deprecated_by = ?
                WHERE id = ?
            """, (now, new_memory_id, memory_id))
            await db.commit()

    async def search_bm25(self, query: str, top_k: int = 20) -> List[Dict[str, Any]]:
        sanitized = " ".join([f'"{part}"' for part in query.replace('"', '').split() if part.isalnum()])
        if not sanitized:
            return []

        async with aiosqlite.connect(str(self.db_path)) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(f"""
                SELECT m.*, bm25(memories_fts) as bm25_rank
                FROM memories_fts f
                JOIN memories m ON m.id = f.id
                WHERE memories_fts MATCH ? AND m.is_active = 1
                ORDER BY bm25_rank ASC
                LIMIT ?
            """, (sanitized, top_k))
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def get_memories_batch(self, memory_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        if not memory_ids:
            return {}
        placeholders = ",".join(["?"] * len(memory_ids))
        async with aiosqlite.connect(str(self.db_path)) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(f"SELECT * FROM memories WHERE id IN ({placeholders})", memory_ids)
            rows = await cursor.fetchall()
            return {row["id"]: dict(row) for row in rows}

    async def get_memory_by_id(self, memory_id: str) -> Optional[Dict[str, Any]]:
        res = await self.get_memories_batch([memory_id])
        return res.get(memory_id)
