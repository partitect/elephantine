import json
import sqlite3
import aiosqlite
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from elephantine.config import settings

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
                    deprecated_by TEXT,
                    workspace_id TEXT NOT NULL DEFAULT 'default',
                    role_authority REAL NOT NULL DEFAULT 0.5
                );
            """)

            # Safe schema evolution / migration for existing databases
            cursor = conn.execute("PRAGMA table_info(memories);")
            cols = [row[1] for row in cursor.fetchall()]
            if "workspace_id" not in cols:
                conn.execute("ALTER TABLE memories ADD COLUMN workspace_id TEXT NOT NULL DEFAULT 'default';")
            if "role_authority" not in cols:
                conn.execute("ALTER TABLE memories ADD COLUMN role_authority REAL NOT NULL DEFAULT 0.5;")

            conn.execute("CREATE INDEX IF NOT EXISTS idx_memories_entity ON memories(entity_key, is_active);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_memories_source ON memories(source_agent, is_active);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_memories_workspace ON memories(workspace_id, is_active);")
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

            conn.execute("""
                CREATE TABLE IF NOT EXISTS graph_triplets (
                    id TEXT PRIMARY KEY,
                    subject TEXT NOT NULL,
                    predicate TEXT NOT NULL,
                    object TEXT NOT NULL,
                    source_memory_id TEXT,
                    confidence REAL NOT NULL DEFAULT 1.0,
                    created_at TIMESTAMP NOT NULL,
                    is_active INTEGER NOT NULL DEFAULT 1,
                    FOREIGN KEY(source_memory_id) REFERENCES memories(id) ON DELETE CASCADE
                );
            """)

            conn.execute("CREATE INDEX IF NOT EXISTS idx_graph_subj ON graph_triplets(subject, is_active);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_graph_obj ON graph_triplets(object, is_active);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_graph_pred ON graph_triplets(predicate, is_active);")
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
        expires_at: Optional[datetime] = None,
        workspace_id: str = "default",
        role_authority: float = 0.5
    ) -> None:
        async with aiosqlite.connect(str(self.db_path)) as db:
            await db.execute("PRAGMA foreign_keys=ON;")
            await db.execute("""
                INSERT INTO memories (
                    id, content, source_agent, entity_key, category, confidence,
                    metadata_json, created_at, updated_at, expires_at, version, is_active,
                    workspace_id, role_authority
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 1, ?, ?)
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
                expires_at.isoformat() if expires_at else None,
                workspace_id,
                role_authority
            ))
            await db.commit()

    async def get_active_by_entity(self, entity_key: str, workspace_id: Optional[str] = None) -> List[Dict[str, Any]]:
        if not entity_key:
            return []
        query = "SELECT * FROM memories WHERE entity_key = ? AND is_active = 1"
        params = [entity_key]
        if workspace_id:
            query += " AND workspace_id = ?"
            params.append(workspace_id)

        async with aiosqlite.connect(str(self.db_path)) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(query, tuple(params))
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

    async def deactivate_memory(self, memory_id: str) -> bool:
        """Soft-deletes / deactivates a memory manually from WebUI/API."""
        now = datetime.now(timezone.utc).isoformat()
        async with aiosqlite.connect(str(self.db_path)) as db:
            cursor = await db.execute("""
                UPDATE memories
                SET is_active = 0, updated_at = ?
                WHERE id = ?
            """, (now, memory_id))
            await db.commit()
            return cursor.rowcount > 0

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

    async def list_all_memories(
        self,
        limit: int = 50,
        offset: int = 0,
        include_inactive: bool = True,
        workspace_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        async with aiosqlite.connect(str(self.db_path)) as db:
            db.row_factory = aiosqlite.Row
            conditions = []
            params: List[Any] = []

            if not include_inactive:
                conditions.append("is_active = 1")
            if workspace_id:
                conditions.append("workspace_id = ?")
                params.append(workspace_id)

            where_clause = f"WHERE {' AND '.join(conditions)} " if conditions else ""
            query = f"SELECT * FROM memories {where_clause}ORDER BY created_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            cursor = await db.execute(query, tuple(params))
            rows = await cursor.fetchall()
            results = []
            for r in rows:
                d = dict(r)
                d["metadata"] = json.loads(d.get("metadata_json", "{}"))
                results.append(d)
            return results

    async def get_all_workspaces(self) -> List[str]:
        """Returns unique workspace/project IDs existing in the store."""
        async with aiosqlite.connect(str(self.db_path)) as db:
            cursor = await db.execute("SELECT DISTINCT workspace_id FROM memories WHERE workspace_id IS NOT NULL ORDER BY workspace_id ASC")
            rows = await cursor.fetchall()
            workspaces = [r[0] for r in rows if r[0]]
            return workspaces if workspaces else ["default"]

    async def get_engine_stats(self, workspace_id: Optional[str] = None) -> Dict[str, Any]:
        async with aiosqlite.connect(str(self.db_path)) as db:
            if workspace_id:
                c1 = await db.execute("SELECT COUNT(*) FROM memories WHERE workspace_id = ?", (workspace_id,))
                total = (await c1.fetchone())[0]
                c2 = await db.execute("SELECT COUNT(*) FROM memories WHERE is_active = 1 AND workspace_id = ?", (workspace_id,))
                active = (await c2.fetchone())[0]
                c3 = await db.execute("SELECT COUNT(DISTINCT entity_key) FROM memories WHERE entity_key IS NOT NULL AND is_active = 1 AND workspace_id = ?", (workspace_id,))
                entities = (await c3.fetchone())[0]
            else:
                c1 = await db.execute("SELECT COUNT(*) FROM memories")
                total = (await c1.fetchone())[0]
                c2 = await db.execute("SELECT COUNT(*) FROM memories WHERE is_active = 1")
                active = (await c2.fetchone())[0]
                c3 = await db.execute("SELECT COUNT(DISTINCT entity_key) FROM memories WHERE entity_key IS NOT NULL AND is_active = 1")
                entities = (await c3.fetchone())[0]

        db_size_bytes = os.path.getsize(self.db_path) if self.db_path.exists() else 0
        return {
            "total_memories": total,
            "active_memories": active,
            "deprecated_memories": total - active,
            "unique_entities": entities,
            "db_size_kb": round(db_size_bytes / 1024, 2)
        }

    async def insert_triplet(
        self,
        triplet_id: str,
        subject: str,
        predicate: str,
        object_: str,
        source_memory_id: Optional[str] = None,
        confidence: float = 1.0
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        async with aiosqlite.connect(str(self.db_path)) as db:
            await db.execute("""
                INSERT INTO graph_triplets (id, subject, predicate, object, source_memory_id, confidence, created_at, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1)
            """, (triplet_id, subject.strip().lower(), predicate.strip().lower(), object_.strip().lower(), source_memory_id, confidence, now))
            await db.commit()

    async def query_graph(
        self,
        subject: Optional[str] = None,
        predicate: Optional[str] = None,
        object_: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        conditions = ["is_active = 1"]
        params = []
        if subject:
            conditions.append("subject = ?")
            params.append(subject.strip().lower())
        if predicate:
            conditions.append("predicate = ?")
            params.append(predicate.strip().lower())
        if object_:
            conditions.append("object = ?")
            params.append(object_.strip().lower())

        where_clause = " AND ".join(conditions)
        query = f"SELECT * FROM graph_triplets WHERE {where_clause} ORDER BY confidence DESC LIMIT ?"
        params.append(limit)

        async with aiosqlite.connect(str(self.db_path)) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(query, tuple(params))
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

    async def get_entity_neighborhood(self, entity: str, max_hops: int = 2) -> List[Dict[str, Any]]:
        """
        Traverses knowledge graph starting from entity up to max_hops (1 or 2 hops).
        Returns connected edges and target nodes.
        """
        entity_norm = entity.strip().lower()
        visited_triplet_ids = set()
        results = []
        frontier = {entity_norm}

        for _ in range(max_hops):
            if not frontier:
                break
            placeholders = ",".join(["?"] * len(frontier))
            frontier_list = list(frontier)
            query = f"""
                SELECT * FROM graph_triplets
                WHERE (subject IN ({placeholders}) OR object IN ({placeholders}))
                  AND is_active = 1
            """
            async with aiosqlite.connect(str(self.db_path)) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute(query, frontier_list + frontier_list)
                rows = await cursor.fetchall()

            next_frontier = set()
            for r in rows:
                tid = r["id"]
                if tid not in visited_triplet_ids:
                    visited_triplet_ids.add(tid)
                    d = dict(r)
                    results.append(d)
                    next_frontier.add(d["subject"])
                    next_frontier.add(d["object"])

            frontier = next_frontier - {entity_norm}

        return results

    async def insert_memories_batch(self, items: List[Dict[str, Any]]) -> int:
        """
        High-throughput batch insertion inside a single atomic SQLite transaction.
        Eliminates per-item lock contention under high concurrency.
        """
        if not items:
            return 0

        async with aiosqlite.connect(str(self.db_path)) as db:
            await db.execute("PRAGMA foreign_keys=ON;")
            params = []
            for item in items:
                created_at = item.get("created_at") or datetime.now(timezone.utc)
                if isinstance(created_at, datetime):
                    created_at_str = created_at.isoformat()
                else:
                    created_at_str = str(created_at)

                expires_at = item.get("expires_at")
                expires_at_str = expires_at.isoformat() if isinstance(expires_at, datetime) else expires_at

                params.append((
                    item["memory_id"],
                    item["content"],
                    item.get("source_agent", "unknown"),
                    item.get("entity_key"),
                    item.get("category", "general"),
                    float(item.get("confidence", 1.0)),
                    json.dumps(item.get("metadata", {}), ensure_ascii=False),
                    created_at_str,
                    created_at_str,
                    expires_at_str,
                    item.get("workspace_id", "default"),
                    float(item.get("role_authority", 0.5))
                ))

            await db.executemany("""
                INSERT INTO memories (
                    id, content, source_agent, entity_key, category, confidence,
                    metadata_json, created_at, updated_at, expires_at, version, is_active,
                    workspace_id, role_authority
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 1, ?, ?)
            """, params)
            await db.commit()
            return len(items)

    async def prune_deprecated_memories(
        self,
        older_than_days: int = 30,
        workspace_id: Optional[str] = None
    ) -> int:
        """
        Prunes old, inactive/deprecated memories from the active index to reclaim space
        and prevent search pollution over long horizons.
        """
        async with aiosqlite.connect(str(self.db_path)) as db:
            query = """
                DELETE FROM memories
                WHERE is_active = 0
                  AND datetime(updated_at) < datetime('now', '-' || ? || ' days')
            """
            params: List[Any] = [older_than_days]
            if workspace_id:
                query += " AND workspace_id = ?"
                params.append(workspace_id)

            cursor = await db.execute(query, tuple(params))
            deleted_count = cursor.rowcount
            await db.commit()
            return deleted_count

    async def get_active_memories_for_consolidation(
        self,
        entity_key: str,
        workspace_id: str = "default"
    ) -> List[Dict[str, Any]]:
        """
        Fetches active memories for a given entity to consolidate/summarize into a single canonical memory.
        """
        async with aiosqlite.connect(str(self.db_path)) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT * FROM memories
                WHERE entity_key = ? AND workspace_id = ? AND is_active = 1
                ORDER BY created_at ASC
            """, (entity_key, workspace_id))
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

    async def get_all_graph_triplets(
        self,
        workspace_id: Optional[str] = None,
        limit: int = 200
    ) -> List[Dict[str, Any]]:
        """
        Retrieves graph triplets, optionally filtered by workspace_id of the source memory.
        """
        async with aiosqlite.connect(str(self.db_path)) as db:
            db.row_factory = aiosqlite.Row
            if workspace_id:
                cursor = await db.execute("""
                    SELECT gt.id, gt.subject, gt.predicate, gt.object, gt.source_memory_id, gt.confidence, gt.created_at, m.workspace_id
                    FROM graph_triplets gt
                    LEFT JOIN memories m ON gt.source_memory_id = m.id
                    WHERE gt.is_active = 1 AND (m.workspace_id = ? OR m.workspace_id IS NULL)
                    ORDER BY gt.created_at DESC
                    LIMIT ?
                """, (workspace_id, limit))
            else:
                cursor = await db.execute("""
                    SELECT gt.id, gt.subject, gt.predicate, gt.object, gt.source_memory_id, gt.confidence, gt.created_at, m.workspace_id
                    FROM graph_triplets gt
                    LEFT JOIN memories m ON gt.source_memory_id = m.id
                    WHERE gt.is_active = 1
                    ORDER BY gt.created_at DESC
                    LIMIT ?
                """, (limit,))
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]


