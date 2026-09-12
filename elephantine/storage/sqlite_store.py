import json
import sqlite3
import aiosqlite
import os
import uuid
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

            conn.execute("""
                CREATE TABLE IF NOT EXISTS proactive_triggers (
                    id TEXT PRIMARY KEY,
                    memory_id TEXT NOT NULL,
                    trigger_type TEXT NOT NULL,
                    condition_value TEXT NOT NULL,
                    target_agent TEXT NOT NULL DEFAULT 'default',
                    workspace_id TEXT NOT NULL DEFAULT 'default',
                    webhook_url TEXT,
                    created_at TIMESTAMP NOT NULL,
                    last_triggered_at TIMESTAMP,
                    next_trigger_at TIMESTAMP,
                    is_active INTEGER NOT NULL DEFAULT 1,
                    status TEXT NOT NULL DEFAULT 'active',
                    FOREIGN KEY(memory_id) REFERENCES memories(id) ON DELETE CASCADE
                );
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_proactive_due ON proactive_triggers(is_active, next_trigger_at);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_proactive_agent ON proactive_triggers(target_agent, workspace_id, status);")

            conn.execute("""
                CREATE TABLE IF NOT EXISTS memory_events (
                    event_id TEXT PRIMARY KEY,
                    memory_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    workspace_id TEXT NOT NULL DEFAULT 'default',
                    source_agent TEXT NOT NULL,
                    role_authority REAL NOT NULL DEFAULT 0.5,
                    content TEXT NOT NULL,
                    category TEXT NOT NULL,
                    entity_key TEXT,
                    metadata_json TEXT NOT NULL DEFAULT '{}',
                    timestamp TIMESTAMP NOT NULL,
                    superseded_by TEXT,
                    confidence REAL NOT NULL DEFAULT 1.0,
                    version INTEGER NOT NULL DEFAULT 1,
                    expires_at TIMESTAMP
                );
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_events_mem ON memory_events(memory_id, timestamp);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_events_ws_time ON memory_events(workspace_id, timestamp);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_events_type ON memory_events(event_type, timestamp);")

            # Safe migrations for existing tables
            for col_def in [("confidence", "REAL NOT NULL DEFAULT 1.0"), ("version", "INTEGER NOT NULL DEFAULT 1"), ("expires_at", "TIMESTAMP")]:
                try:
                    conn.execute(f"ALTER TABLE memory_events ADD COLUMN {col_def[0]} {col_def[1]};")
                except sqlite3.OperationalError:
                    pass

            # Immutable ledger engine enforcement: prevent any UPDATE or DELETE on memory_events
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS trg_memory_events_no_update
                BEFORE UPDATE ON memory_events
                BEGIN
                    SELECT RAISE(ABORT, 'memory_events table is immutable append-only');
                END;
            """)
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS trg_memory_events_no_delete
                BEFORE DELETE ON memory_events
                BEGIN
                    SELECT RAISE(ABORT, 'memory_events table is immutable append-only');
                END;
            """)

            # Backfill initial events from existing memories if ledger is empty
            conn.execute("""
                INSERT INTO memory_events (
                    event_id, memory_id, event_type, workspace_id, source_agent,
                    role_authority, content, category, entity_key, metadata_json, timestamp, superseded_by,
                    confidence, version, expires_at
                )
                SELECT
                    'backfill-' || m.id,
                    m.id,
                    CASE WHEN m.is_active = 1 THEN 'CREATED' ELSE 'SUPERSEDED' END,
                    m.workspace_id,
                    m.source_agent,
                    m.role_authority,
                    m.content,
                    m.category,
                    m.entity_key,
                    m.metadata_json,
                    m.created_at,
                    m.deprecated_by,
                    m.confidence,
                    m.version,
                    m.expires_at
                FROM memories m
                WHERE NOT EXISTS (SELECT 1 FROM memory_events LIMIT 1);
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS lancedb_outbox (
                    id TEXT PRIMARY KEY,
                    memory_id TEXT NOT NULL,
                    operation TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    processed_at TIMESTAMP,
                    status TEXT NOT NULL DEFAULT 'pending'
                );
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_outbox_pending ON lancedb_outbox(status, created_at);")
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
        import uuid
        event_id = str(uuid.uuid4())
        meta_json = json.dumps(metadata, ensure_ascii=False)
        async with aiosqlite.connect(str(self.db_path)) as db:
            await db.execute("PRAGMA foreign_keys=ON;")
            # 1. Insert into current state table
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
                meta_json,
                created_at.isoformat(),
                created_at.isoformat(),
                expires_at.isoformat() if expires_at else None,
                workspace_id,
                role_authority
            ))
            # 2. Record in Immutable Append-Only Event Ledger
            await db.execute("""
                INSERT INTO memory_events (
                    event_id, memory_id, event_type, workspace_id, source_agent,
                    role_authority, content, category, entity_key, metadata_json, timestamp,
                    confidence, version, expires_at
                ) VALUES (?, ?, 'CREATED', ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
            """, (
                event_id,
                memory_id,
                workspace_id,
                source_agent,
                role_authority,
                content,
                category,
                entity_key,
                meta_json,
                created_at.isoformat(),
                confidence,
                expires_at.isoformat() if expires_at else None
            ))
            # 3. Transactional Outbox for LanceDB Sync
            outbox_id = str(uuid.uuid4())
            outbox_payload = json.dumps({
                "memory_id": memory_id,
                "source_agent": source_agent,
                "category": category,
                "created_at_epoch": created_at.timestamp(),
                "workspace_id": workspace_id,
                "expires_at_epoch": expires_at.timestamp() if expires_at else 0.0
            }, ensure_ascii=False)
            await db.execute("""
                INSERT INTO lancedb_outbox (
                    id, memory_id, operation, payload_json, created_at, status
                ) VALUES (?, ?, 'UPSERT', ?, ?, 'pending')
            """, (outbox_id, memory_id, outbox_payload, created_at.isoformat()))
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
        import uuid
        now = datetime.now(timezone.utc).isoformat()
        event_id = str(uuid.uuid4())
        outbox_id = str(uuid.uuid4())
        async with aiosqlite.connect(str(self.db_path)) as db:
            db.row_factory = aiosqlite.Row
            c = await db.execute("SELECT * FROM memories WHERE id = ?", (memory_id,))
            mem = await c.fetchone()
            if mem:
                # Update current view
                await db.execute("""
                    UPDATE memories
                    SET is_active = 0, updated_at = ?, deprecated_by = ?
                    WHERE id = ?
                """, (now, new_memory_id, memory_id))
                # Record deprecation in event ledger
                await db.execute("""
                    INSERT INTO memory_events (
                        event_id, memory_id, event_type, workspace_id, source_agent,
                        role_authority, content, category, entity_key, metadata_json,
                        timestamp, superseded_by, confidence, version, expires_at
                    ) VALUES (?, ?, 'SUPERSEDED', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    event_id,
                    memory_id,
                    mem["workspace_id"],
                    mem["source_agent"],
                    mem["role_authority"],
                    mem["content"],
                    mem["category"],
                    mem["entity_key"],
                    mem["metadata_json"],
                    now,
                    new_memory_id,
                    mem["confidence"],
                    mem["version"],
                    mem["expires_at"]
                ))
                # Stage delete in LanceDB outbox
                await db.execute("""
                    INSERT INTO lancedb_outbox (
                        id, memory_id, operation, payload_json, created_at, status
                    ) VALUES (?, ?, 'DELETE', '{}', ?, 'pending')
                """, (outbox_id, memory_id, now))
            await db.commit()

    async def deactivate_memory(self, memory_id: str) -> bool:
        """Soft-deletes / deactivates a memory manually from WebUI/API."""
        import uuid
        now = datetime.now(timezone.utc).isoformat()
        event_id = str(uuid.uuid4())
        outbox_id = str(uuid.uuid4())
        async with aiosqlite.connect(str(self.db_path)) as db:
            db.row_factory = aiosqlite.Row
            c = await db.execute("SELECT * FROM memories WHERE id = ?", (memory_id,))
            mem = await c.fetchone()
            if not mem:
                return False
            cursor = await db.execute("""
                UPDATE memories
                SET is_active = 0, updated_at = ?
                WHERE id = ?
            """, (now, memory_id))
            # Record in event ledger
            await db.execute("""
                INSERT INTO memory_events (
                    event_id, memory_id, event_type, workspace_id, source_agent,
                    role_authority, content, category, entity_key, metadata_json,
                    timestamp, confidence, version, expires_at
                ) VALUES (?, ?, 'DEACTIVATED', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event_id,
                memory_id,
                mem["workspace_id"],
                mem["source_agent"],
                mem["role_authority"],
                mem["content"],
                mem["category"],
                mem["entity_key"],
                mem["metadata_json"],
                now,
                mem["confidence"],
                mem["version"],
                mem["expires_at"]
            ))
            # Stage delete in LanceDB outbox
            await db.execute("""
                INSERT INTO lancedb_outbox (
                    id, memory_id, operation, payload_json, created_at, status
                ) VALUES (?, ?, 'DELETE', '{}', ?, 'pending')
            """, (outbox_id, memory_id, now))
            await db.commit()
            return cursor.rowcount > 0

    async def record_expired_events(self, workspace_id: Optional[str] = None) -> int:
        """Finds active memories that have passed expires_at and logs EXPIRED events in ledger."""
        import uuid
        now_iso = datetime.now(timezone.utc).isoformat()
        async with aiosqlite.connect(str(self.db_path)) as db:
            db.row_factory = aiosqlite.Row
            query = """
                SELECT m.* FROM memories m
                WHERE m.is_active = 1
                  AND m.expires_at IS NOT NULL
                  AND m.expires_at <= ?
                  AND NOT EXISTS (
                      SELECT 1 FROM memory_events e
                      WHERE e.memory_id = m.id AND e.event_type = 'EXPIRED'
                  )
            """
            params = [now_iso]
            if workspace_id:
                query += " AND m.workspace_id = ?"
                params.append(workspace_id)
            cursor = await db.execute(query, tuple(params))
            expired_rows = await cursor.fetchall()
            for r in expired_rows:
                ev_id = str(uuid.uuid4())
                await db.execute("""
                    INSERT INTO memory_events (
                        event_id, memory_id, event_type, workspace_id, source_agent,
                        role_authority, content, category, entity_key, metadata_json,
                        timestamp, confidence, version, expires_at
                    ) VALUES (?, ?, 'EXPIRED', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    ev_id, r["id"], r["workspace_id"], r["source_agent"],
                    r["role_authority"], r["content"], r["category"], r["entity_key"],
                    r["metadata_json"], now_iso, r["confidence"], r["version"], r["expires_at"]
                ))
            if expired_rows:
                await db.commit()
            return len(expired_rows)

    async def get_memories_as_of(
        self,
        as_of_timestamp: str,
        workspace_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        True Time-Travel Query: reconstructs the exact active memories as they existed
        at as_of_timestamp using the immutable event ledger.
        """
        async with aiosqlite.connect(str(self.db_path)) as db:
            db.row_factory = aiosqlite.Row
            # All creations up to as_of that were not superseded/deactivated/expired before as_of
            query = """
                SELECT e.* FROM memory_events e
                WHERE e.event_type = 'CREATED'
                  AND e.timestamp <= ?
                  AND (e.expires_at IS NULL OR e.expires_at > ?)
                  AND NOT EXISTS (
                      SELECT 1 FROM memory_events d
                      WHERE d.memory_id = e.memory_id
                        AND d.event_type IN ('SUPERSEDED', 'DEACTIVATED', 'EXPIRED')
                        AND d.timestamp <= ?
                  )
            """
            params = [as_of_timestamp, as_of_timestamp, as_of_timestamp]
            if workspace_id:
                query += " AND e.workspace_id = ?"
                params.append(workspace_id)
            query += " ORDER BY e.timestamp DESC"
            cursor = await db.execute(query, tuple(params))
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def get_events_since(
        self,
        since_timestamp: str,
        workspace_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        True Audit Query: retrieves all memory mutations (CREATED, SUPERSEDED, DEACTIVATED)
        that occurred on or after since_timestamp.
        """
        async with aiosqlite.connect(str(self.db_path)) as db:
            db.row_factory = aiosqlite.Row
            query = "SELECT * FROM memory_events WHERE timestamp >= ?"
            params = [since_timestamp]
            if workspace_id:
                query += " AND workspace_id = ?"
                params.append(workspace_id)
            query += " ORDER BY timestamp ASC"
            cursor = await db.execute(query, tuple(params))
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def mark_outbox_processed(self, memory_id: str, operation: str = "UPSERT") -> None:
        now = datetime.now(timezone.utc).isoformat()
        async with aiosqlite.connect(str(self.db_path)) as db:
            await db.execute("""
                UPDATE lancedb_outbox
                SET status = 'processed', processed_at = ?
                WHERE memory_id = ? AND operation = ? AND status = 'pending'
            """, (now, memory_id, operation))
            await db.commit()

    async def get_pending_outbox(self) -> List[Dict[str, Any]]:
        async with aiosqlite.connect(str(self.db_path)) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM lancedb_outbox WHERE status = 'pending' ORDER BY created_at ASC")
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def search_bm25(
        self,
        query: str,
        top_k: int = 20,
        workspace_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        sanitized = " ".join([f'"{part}"' for part in query.replace('"', '').split() if part.isalnum()])
        if not sanitized:
            return []

        now_iso = datetime.now(timezone.utc).isoformat()
        conditions = ["memories_fts MATCH ?", "m.is_active = 1", "(m.expires_at IS NULL OR m.expires_at > ?)"]
        params: List[Any] = [sanitized, now_iso]

        if workspace_id:
            conditions.append("m.workspace_id = ?")
            params.append(workspace_id)

        params.append(top_k)
        where_clause = " AND ".join(conditions)

        async with aiosqlite.connect(str(self.db_path)) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(f"""
                SELECT m.*, bm25(memories_fts) as bm25_rank
                FROM memories_fts f
                JOIN memories m ON m.id = f.id
                WHERE {where_clause}
                ORDER BY bm25_rank ASC
                LIMIT ?
            """, params)
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
        Eliminates per-item lock contention under high concurrency and guarantees
        event ledger audit logging and transactional LanceDB outbox consistency.
        """
        if not items:
            return 0

        import uuid
        async with aiosqlite.connect(str(self.db_path)) as db:
            await db.execute("PRAGMA foreign_keys=ON;")
            mem_params = []
            event_params = []
            outbox_params = []
            for item in items:
                created_at = item.get("created_at") or datetime.now(timezone.utc)
                if isinstance(created_at, datetime):
                    created_at_str = created_at.isoformat()
                    created_at_epoch = created_at.timestamp()
                else:
                    created_at_str = str(created_at)
                    try:
                        created_at_epoch = datetime.fromisoformat(created_at_str.replace("Z", "+00:00")).timestamp()
                    except Exception:
                        created_at_epoch = datetime.now(timezone.utc).timestamp()

                expires_at = item.get("expires_at")
                if isinstance(expires_at, datetime):
                    expires_at_str = expires_at.isoformat()
                    expires_at_epoch = expires_at.timestamp()
                elif expires_at:
                    expires_at_str = str(expires_at)
                    try:
                        expires_at_epoch = datetime.fromisoformat(expires_at_str.replace("Z", "+00:00")).timestamp()
                    except Exception:
                        expires_at_epoch = 0.0
                else:
                    expires_at_str = None
                    expires_at_epoch = 0.0

                ws_id = item.get("workspace_id", "default")
                authority = float(item.get("role_authority", 0.5))
                category = item.get("category", "general")
                source_agent = item.get("source_agent", "unknown")
                meta_dict = item.get("metadata", {})
                meta_json = json.dumps(meta_dict, ensure_ascii=False)
                mem_id = item["memory_id"]
                content = item["content"]
                entity_key = item.get("entity_key")
                confidence = float(item.get("confidence", 1.0))

                mem_params.append((
                    mem_id, content, source_agent, entity_key, category, confidence,
                    meta_json, created_at_str, created_at_str, expires_at_str, ws_id, authority
                ))

                event_params.append((
                    str(uuid.uuid4()), mem_id, 'CREATED', ws_id, source_agent,
                    authority, content, category, entity_key, meta_json, created_at_str,
                    confidence, 1, expires_at_str
                ))

                outbox_payload = json.dumps({
                    "memory_id": mem_id,
                    "source_agent": source_agent,
                    "category": category,
                    "created_at_epoch": created_at_epoch,
                    "workspace_id": ws_id,
                    "expires_at_epoch": expires_at_epoch
                }, ensure_ascii=False)
                outbox_params.append((
                    str(uuid.uuid4()), mem_id, 'UPSERT', outbox_payload, created_at_str
                ))

            await db.executemany("""
                INSERT INTO memories (
                    id, content, source_agent, entity_key, category, confidence,
                    metadata_json, created_at, updated_at, expires_at, version, is_active,
                    workspace_id, role_authority
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 1, ?, ?)
            """, mem_params)

            await db.executemany("""
                INSERT INTO memory_events (
                    event_id, memory_id, event_type, workspace_id, source_agent,
                    role_authority, content, category, entity_key, metadata_json, timestamp,
                    confidence, version, expires_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, event_params)

            await db.executemany("""
                INSERT INTO lancedb_outbox (
                    id, memory_id, operation, payload_json, created_at, status
                ) VALUES (?, ?, ?, ?, ?, 'pending')
            """, outbox_params)

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

    # =========================================================================
    # PROACTIVE MEMORY TRIGGERS
    # =========================================================================

    async def create_proactive_trigger(
        self,
        trigger_id: str,
        memory_id: str,
        trigger_type: str,
        condition_value: str,
        target_agent: str = "default",
        workspace_id: str = "default",
        webhook_url: Optional[str] = None,
        next_trigger_at: Optional[datetime] = None
    ) -> str:
        """Stores a new proactive trigger attached to an existing memory."""
        now = datetime.now(timezone.utc)
        async with aiosqlite.connect(str(self.db_path)) as db:
            await db.execute("""
                INSERT INTO proactive_triggers (
                    id, memory_id, trigger_type, condition_value, target_agent,
                    workspace_id, webhook_url, created_at, next_trigger_at, is_active, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 'active')
            """, (
                trigger_id,
                memory_id,
                trigger_type,
                condition_value,
                target_agent,
                workspace_id,
                webhook_url,
                now.isoformat(),
                next_trigger_at.isoformat() if next_trigger_at else None
            ))
            await db.commit()
        return trigger_id

    async def get_due_proactive_triggers(self, current_time: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Finds active triggers whose next_trigger_at is past or due, joined with memory content."""
        if current_time is None:
            current_time = datetime.now(timezone.utc)
        curr_iso = current_time.isoformat()

        async with aiosqlite.connect(str(self.db_path)) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT pt.*, m.content as memory_content, m.category as memory_category, m.role_authority
                FROM proactive_triggers pt
                JOIN memories m ON pt.memory_id = m.id
                WHERE pt.is_active = 1 
                  AND pt.status = 'active'
                  AND pt.next_trigger_at IS NOT NULL 
                  AND pt.next_trigger_at <= ?
                ORDER BY pt.next_trigger_at ASC
            """, (curr_iso,))
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

    async def mark_trigger_fired(
        self,
        trigger_id: str,
        memory_id: str,
        target_agent: str,
        workspace_id: str,
        next_trigger_at: Optional[datetime] = None,
        is_recurring: bool = False
    ) -> str:
        """Updates last_triggered_at and stages alert in proactive_alerts table."""
        now = datetime.now(timezone.utc)
        new_status = "active" if is_recurring else "triggered"
        alert_id = str(uuid.uuid4())
        async with aiosqlite.connect(str(self.db_path)) as db:
            await db.execute("""
                UPDATE proactive_triggers
                SET last_triggered_at = ?,
                    next_trigger_at = ?,
                    status = ?
                WHERE id = ?
            """, (
                now.isoformat(),
                next_trigger_at.isoformat() if next_trigger_at else None,
                new_status,
                trigger_id
            ))
            await db.execute("""
                INSERT INTO proactive_alerts (
                    id, trigger_id, memory_id, target_agent, workspace_id, triggered_at, status
                ) VALUES (?, ?, ?, ?, ?, ?, 'pending')
            """, (
                alert_id,
                trigger_id,
                memory_id,
                target_agent,
                workspace_id,
                now.isoformat()
            ))
            await db.commit()
        return alert_id

    async def get_pending_triggers_for_agent(
        self,
        target_agent: str = "default",
        workspace_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Retrieves fired but unacknowledged alerts waiting for an agent."""
        async with aiosqlite.connect(str(self.db_path)) as db:
            db.row_factory = aiosqlite.Row
            if workspace_id:
                cursor = await db.execute("""
                    SELECT pa.id as alert_id, pa.triggered_at, pa.status as alert_status,
                           pt.id as id, pt.condition_value, pt.trigger_type, pt.next_trigger_at,
                           m.id as memory_id, m.content as memory_content, m.category as memory_category,
                           m.role_authority, pa.target_agent, pa.workspace_id
                    FROM proactive_alerts pa
                    JOIN proactive_triggers pt ON pa.trigger_id = pt.id
                    JOIN memories m ON pa.memory_id = m.id
                    WHERE (pa.target_agent = ? OR pa.target_agent = 'all' OR pa.target_agent = 'default')
                      AND pa.workspace_id = ?
                      AND pa.status = 'pending'
                    ORDER BY pa.triggered_at DESC
                """, (target_agent, workspace_id))
            else:
                cursor = await db.execute("""
                    SELECT pa.id as alert_id, pa.triggered_at, pa.status as alert_status,
                           pt.id as id, pt.condition_value, pt.trigger_type, pt.next_trigger_at,
                           m.id as memory_id, m.content as memory_content, m.category as memory_category,
                           m.role_authority, pa.target_agent, pa.workspace_id
                    FROM proactive_alerts pa
                    JOIN proactive_triggers pt ON pa.trigger_id = pt.id
                    JOIN memories m ON pa.memory_id = m.id
                    WHERE (pa.target_agent = ? OR pa.target_agent = 'all' OR pa.target_agent = 'default')
                      AND pa.status = 'pending'
                    ORDER BY pa.triggered_at DESC
                """, (target_agent,))
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

    async def acknowledge_trigger(self, trigger_or_alert_id: str) -> bool:
        """Marks a proactive alert as acknowledged by the agent (matches alert_id or trigger_id)."""
        async with aiosqlite.connect(str(self.db_path)) as db:
            cursor = await db.execute("""
                UPDATE proactive_alerts
                SET status = 'acknowledged'
                WHERE (id = ? OR trigger_id = ?) AND status = 'pending'
            """, (trigger_or_alert_id, trigger_or_alert_id))
            await db.commit()
            return cursor.rowcount > 0



