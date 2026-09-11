import json
import sqlite3
import aiosqlite
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from memagent.config import settings
from memagent.api.schemas import ToolCallExecution, WorkflowSnippet

class ProceduralMemoryStore:
    """
    Tracks tool call execution sequences, parameters, status, and resolutions.
    Extracts multi-step execution graphs into reusable workflow snippets.
    """
    def __init__(self, db_path: Path = settings.sqlite_path):
        self.db_path = Path(db_path)
        self._init_tables()

    def _init_tables(self):
        conn = sqlite3.connect(str(self.db_path))
        with conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tool_executions (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    agent_id TEXT NOT NULL,
                    tool_name TEXT NOT NULL,
                    tool_input_json TEXT NOT NULL,
                    tool_output_json TEXT,
                    status TEXT NOT NULL,
                    error_message TEXT,
                    execution_time_ms REAL NOT NULL,
                    timestamp TIMESTAMP NOT NULL
                );
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_tool_exec_session ON tool_executions(session_id, timestamp);")

            conn.execute("""
                CREATE TABLE IF NOT EXISTS workflows (
                    id TEXT PRIMARY KEY,
                    pattern_name TEXT UNIQUE NOT NULL,
                    description TEXT NOT NULL,
                    step_sequence_json TEXT NOT NULL,
                    success_count INTEGER NOT NULL DEFAULT 1,
                    failure_count INTEGER NOT NULL DEFAULT 0,
                    last_used TIMESTAMP NOT NULL
                );
            """)
        conn.close()

    async def record_tool_call(self, execution: ToolCallExecution) -> str:
        call_id = str(uuid.uuid4())
        async with aiosqlite.connect(str(self.db_path)) as db:
            await db.execute("""
                INSERT INTO tool_executions (
                    id, session_id, agent_id, tool_name, tool_input_json,
                    tool_output_json, status, error_message, execution_time_ms, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                call_id,
                execution.session_id,
                execution.agent_id,
                execution.tool_name,
                json.dumps(execution.tool_input, ensure_ascii=False),
                json.dumps(execution.tool_output, ensure_ascii=False) if execution.tool_output else None,
                execution.status,
                execution.error_message,
                execution.execution_time_ms,
                execution.timestamp.isoformat()
            ))
            await db.commit()
        return call_id

    async def get_session_history(self, session_id: str) -> List[Dict[str, Any]]:
        async with aiosqlite.connect(str(self.db_path)) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT * FROM tool_executions
                WHERE session_id = ?
                ORDER BY timestamp ASC
            """, (session_id,))
            rows = await cursor.fetchall()
            results = []
            for r in rows:
                d = dict(r)
                d["tool_input"] = json.loads(d["tool_input_json"])
                d["tool_output"] = json.loads(d["tool_output_json"]) if d["tool_output_json"] else None
                results.append(d)
            return results

    async def save_or_update_workflow(self, pattern_name: str, description: str, steps: List[Dict[str, Any]], success: bool = True) -> str:
        workflow_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        async with aiosqlite.connect(str(self.db_path)) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT id, success_count, failure_count FROM workflows WHERE pattern_name = ?", (pattern_name,))
            row = await cursor.fetchone()
            if row:
                wf_id = row["id"]
                s_count = row["success_count"] + (1 if success else 0)
                f_count = row["failure_count"] + (0 if success else 1)
                await db.execute("""
                    UPDATE workflows
                    SET success_count = ?, failure_count = ?, last_used = ?, step_sequence_json = ?
                    WHERE id = ?
                """, (s_count, f_count, now, json.dumps(steps, ensure_ascii=False), wf_id))
                await db.commit()
                return wf_id
            else:
                await db.execute("""
                    INSERT INTO workflows (
                        id, pattern_name, description, step_sequence_json, success_count, failure_count, last_used
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    workflow_id,
                    pattern_name,
                    description,
                    json.dumps(steps, ensure_ascii=False),
                    1 if success else 0,
                    0 if success else 1,
                    now
                ))
                await db.commit()
                return workflow_id

    async def get_workflow(self, pattern_name: str) -> Optional[WorkflowSnippet]:
        async with aiosqlite.connect(str(self.db_path)) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM workflows WHERE pattern_name = ?", (pattern_name,))
            row = await cursor.fetchone()
            if not row:
                return None
            return WorkflowSnippet(
                id=row["id"],
                pattern_name=row["pattern_name"],
                description=row["description"],
                step_sequence=json.loads(row["step_sequence_json"]),
                success_count=row["success_count"],
                failure_count=row["failure_count"],
                last_used=datetime.fromisoformat(row["last_used"])
            )
