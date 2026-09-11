from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse
from typing import List, Dict, Any, Optional
from elephantine.storage.sqlite_store import SqliteMetadataStore

router = APIRouter()
sqlite_store = SqliteMetadataStore()

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Elephantine | Memory Inspector & Live Graph</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        body { background-color: #0b0f17; color: #e2e8f0; font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
        .glass-panel { background: rgba(17, 24, 39, 0.75); backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.08); }
        .glass-card { background: rgba(30, 41, 59, 0.5); border: 1px solid rgba(255, 255, 255, 0.05); }
    </style>
</head>
<body class="min-h-screen flex flex-col">
    <header class="glass-panel sticky top-0 z-50 px-6 py-4 flex items-center justify-between border-b border-slate-800">
        <div class="flex items-center space-x-3">
            <span class="text-3xl">🐘</span>
            <div>
                <h1 class="text-xl font-bold tracking-tight text-white flex items-center gap-2">
                    ELEPHANTINE
                    <span class="text-xs font-mono uppercase bg-emerald-500/20 text-emerald-400 px-2 py-0.5 rounded border border-emerald-500/30">CPU-Native v0.1.0</span>
                </h1>
                <p class="text-xs text-slate-400">Local-First Cognitive Memory Inspector & Knowledge Graph</p>
            </div>
        </div>
        <div class="flex items-center space-x-4">
            <button onclick="fetchWorkspaces(); fetchStats(); fetchMemories();" class="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-sm font-medium border border-slate-700 transition flex items-center gap-2">
                <i class="fa-solid fa-arrows-rotate text-emerald-400"></i> Refresh
            </button>
            <a href="/docs" target="_blank" class="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-sm font-semibold text-white transition flex items-center gap-2">
                <i class="fa-solid fa-book"></i> API Docs
            </a>
        </div>
    </header>

    <main class="flex-1 max-w-7xl w-full mx-auto p-6 space-y-6">
        <!-- Live Engine Metrics KPI -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4" id="stats-grid">
            <div class="glass-card p-5 rounded-xl">
                <div class="text-slate-400 text-xs font-mono uppercase">Total Memories</div>
                <div class="text-3xl font-bold text-white mt-1" id="stat-total">-</div>
                <div class="text-xs text-slate-500 mt-1">Recorded across sessions</div>
            </div>
            <div class="glass-card p-5 rounded-xl">
                <div class="text-slate-400 text-xs font-mono uppercase">Active Facts</div>
                <div class="text-3xl font-bold text-emerald-400 mt-1" id="stat-active">-</div>
                <div class="text-xs text-slate-500 mt-1">Currently valid in context</div>
            </div>
            <div class="glass-card p-5 rounded-xl">
                <div class="text-slate-400 text-xs font-mono uppercase">Deprecated (LWW)</div>
                <div class="text-3xl font-bold text-amber-400 mt-1" id="stat-deprecated">-</div>
                <div class="text-xs text-slate-500 mt-1">Soft-deprecated via conflict resolution</div>
            </div>
            <div class="glass-card p-5 rounded-xl">
                <div class="text-slate-400 text-xs font-mono uppercase">Unique Entities & Size</div>
                <div class="text-3xl font-bold text-indigo-400 mt-1 flex items-baseline gap-2">
                    <span id="stat-entities">-</span>
                    <span class="text-sm font-normal text-slate-400" id="stat-size">(- KB)</span>
                </div>
                <div class="text-xs text-slate-500 mt-1">Knowledge graph clusters</div>
            </div>
--      </div>

        <!-- Controls: Search & Filters -->
        <div class="glass-panel p-4 rounded-xl flex flex-col md:flex-row gap-4 items-center justify-between">
            <div class="flex-1 relative w-full">
                <i class="fa-solid fa-magnifying-glass absolute left-3.5 top-3.5 text-slate-500"></i>
                <input type="text" id="filter-input" placeholder="Search memories, entity keys, namespaces..." oninput="filterMemories()" 
                    class="w-full bg-slate-900/90 border border-slate-700 rounded-lg pl-10 pr-4 py-2 text-sm text-slate-200 focus:outline-none focus:border-emerald-500 transition">
            </div>
            <div class="flex items-center space-x-4 w-full md:w-auto">
                <div class="flex items-center space-x-2">
                    <span class="text-xs text-slate-400 font-mono uppercase"><i class="fa-solid fa-folder-tree text-indigo-400 mr-1"></i>Project:</span>
                    <select id="filter-workspace" onchange="onWorkspaceChange()" class="bg-slate-900 border border-slate-700 text-slate-200 text-xs rounded-lg px-3 py-2 focus:outline-none focus:border-indigo-500 transition">
                        <option value="">All Projects (Global)</option>
                    </select>
                </div>
                <label class="flex items-center space-x-2 text-sm text-slate-300 cursor-pointer">
                    <input type="checkbox" id="filter-active-only" onchange="fetchMemories()" class="rounded border-slate-700 text-emerald-500 focus:ring-0">
                    <span>Hide Deprecated</span>
                </label>
            </div>
        </div>

        <!-- Memory Ledger Table -->
        <div class="glass-panel rounded-xl overflow-hidden shadow-28l">
            <div class="px-6 py-4 border-b border-slate-800 flex justify-between items-center">
                <h2 class="text-base font-semibold text-white flex items-center gap-2">
                    <i class="fa-solid fa-brain text-emerald-400"></i> Memory Ledger
                </h2>
                <span class="text-xs text-slate-400 font-mono" id="memory-count-label">Loaded 0 records</span>
            </div>
            <div class="overflow-x-auto">
                <table class="w-full text-left border-collapse">
                    <thead>
                        <tr class="border-b border-slate-800 bg-slate-900/50 text-xs font-mono text-slate-400 uppercase">
                            <th class="py-3 px-4">Status</th>
                            <th class="py-3 px-4">Entity Key</th>
                            <th class="py-3 px-4">Content / Extracted Fact</th>
                            <th class="py-3 px-4">Project / Agent</th>
                            <th class="py-3 px-4">Version</th>
                            <th class="py-3 px-4">Timestamp</th>
                            <th class="py-3 px-4 text-right">Actions</th>
                        </tr>
                    </thead>
                    <tbody id="memories-body" class="divide-y divide-slate-800/60 text-sm">
                        <tr>
                            <td colspan="7" class="py-8 text-center text-slate-500">
                                <i class="fa-solid fa-spinner fa-spin mr-2"></i> Loading memories from local store...
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    </main>

    <script>
        let allMemories = [];

        async function fetchWorkspaces() {
            try {
                const res = await fetch('/api/v1/workspaces');
                if (!res.ok) return;
                const list = await res.json();
                const sel = document.getElementById('filter-workspace');
                const curr = sel.value;
                sel.innerHTML = '<option value="">All Projects (Global)</option>' +
                    list.map(w => '<option value="' + escapeHtml(w) + '"' + (curr === w ? ' selected' : '') + '>' + escapeHtml(w) + '</option>').join('');
            } catch (err) {
                console.error('Error fetching workspaces:', err);
            }
        }

        async function onWorkspaceChange() {
            await fetchStats();
            await fetchMemories();
        }

        async function fetchStats() {
            try {
                const ws = document.getElementById('filter-workspace')?.value || '';
                const url = ws ? '/api/v1/stats?workspace_id=' + encodeURIComponent(ws) : '/api/v1/stats';
                const res = await fetch(url);
                if (!res.ok) throw new Error('HTTP ' + res.status);
                const data = await res.json();
                document.getElementById('stat-total').innerText = data.total_memories ?? 0;
                document.getElementById('stat-active').innerText = data.active_memories ?? 0;
                document.getElementById('stat-deprecated').innerText = data.deprecated_memories ?? 0;
                document.getElementById('stat-entities').innerText = data.unique_entities ?? 0;
                document.getElementById('stat-size').innerText = '(' + (data.db_size_kb ?? 0) + ' KB)';
            } catch (err) {
                console.error('Error fetching stats:', err);
            }
        }

        async function fetchMemories() {
            const tbody = document.getElementById('memories-body');
            try {
                const hideInactive = document.getElementById('filter-active-only')?.checked ?? false;
                const ws = document.getElementById('filter-workspace')?.value || '';
                let url = '/api/v1/memories?limit=100&include_inactive=' + (!hideInactive);
                if (ws) url += '&workspace_id=' + encodeURIComponent(ws);

                const res = await fetch(url);
                if (!res.ok) throw new Error('API returned status ' + res.status);
                allMemories = await res.json();
                renderMemories(allMemories);
            } catch (err) {
                console.error('Error fetching memories:', err);
                if (tbody) {
                    tbody.innerHTML = '<tr><td colspan="7" class="py-8 text-center text-rose-400 font-mono text-sm"><i class="fa-solid fa-triangle-exclamation mr-2"></i> Failed to load memories: ' + escapeHtml(err.message || String(err)) + '<br><button onclick="fetchMemories()" class="mt-3 px-3 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded border border-slate-700 text-xs">Retry</button></td></tr>';
                }
            }
        }

        function filterMemories() {
            const query = (document.getElementById('filter-input')?.value || '').toLowerCase().trim();
            if (!query) {
                renderMemories(allMemories);
                return;
            }
            const filtered = allMemories.filter(m => 
                (m.content && m.content.toLowerCase().includes(query)) ||
                (m.entity_key && m.entity_key.toLowerCase().includes(query)) ||
                (m.workspace_id && m.workspace_id.toLowerCase().includes(query)) ||
                (m.source_agent && m.source_agent.toLowerCase().includes(query)) ||
                (m.category && m.category.toLowerCase().includes(query))
            );
            renderMemories(filtered);
        }

        function renderMemories(items) {
            const tbody = document.getElementById('memories-body');
            const countLabel = document.getElementById('memory-count-label');
            if (countLabel) countLabel.innerText = 'Showing ' + items.length + ' records';
            
            if (!items || items.length === 0) {
                tbody.innerHTML = '<tr><td colspan="7" class="py-8 text-center text-slate-500">No memories found matching criteria.</td></tr>';
                return;
            }

            tbody.innerHTML = items.map(m => {
                const isActive = m.is_active === 1 || m.is_active === true;
                const statusBadge = isActive 
                    ? '<span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"><span class="w-1.5 h-1.5 rounded-full bg-emerald-400 mr-1.5"></span>Active</span>'
                    : '<span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-slate-700/50 text-slate-400 border border-slate-600/30"><span class="w-1.5 h-1.5 rounded-full bg-slate-500 mr-1.5"></span>Deprecated</span>';
                
                let dateStr = 'N/A';
                if (m.created_at) {
                    try {
                        const parsed = new Date(m.created_at);
                        dateStr = isNaN(parsed.getTime()) ? m.created_at : parsed.toLocaleString();
                    } catch (e) {
                        dateStr = m.created_at;
                    }
                }

                const entityKey = m.entity_key 
                    ? '<span class="font-mono text-xs text-indigo-300 bg-indigo-950/40 px-2 py-0.5 rounded border border-indigo-800/30">' + escapeHtml(m.entity_key) + '</span>' 
                    : '<span class="text-slate-600 text-xs italic">none</span>';

                const namespace = (m.workspace_id || m.source_agent)
                    ? '<span class="text-slate-300 font-mono text-xs">' + escapeHtml(m.workspace_id || '') + '</span>' + (m.source_agent ? ' <span class="text-slate-500 text-xs">(' + escapeHtml(m.source_agent) + ')</span>' : '')
                    : '<span class="text-slate-600 text-xs italic">default</span>';

                const version = m.version != null ? m.version : 1;

                return '<tr class="hover:bg-slate-800/40 transition">' +
                    '<td class="py-3 px-4">' + statusBadge + '</td>' +
                    '<td class="py-3 px-4">' + entityKey + '</td>' +
                    '<td class="py-3 px-4 font-medium text-slate-200 max-w-md break-words">' + escapeHtml(m.content || '') + '</td>' +
                    '<td class="py-3 px-4">' + namespace + '</td>' +
                    '<td class="py-3 px-4 font-mono text-xs text-slate-300">v' + version + '</td>' +
                    '<td class="py-3 px-4 text-xs text-slate-400 whitespace-nowrap">' + escapeHtml(dateStr) + '</td>' +
                    '<td class="py-3 px-4 text-right">' +
                        (isActive ? '<button data-id="' + m.id + '" onclick="deactivateMemory(this.dataset.id)" class="px-2 py-1 rounded bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/20 text-xs transition"><i class="fa-solid fa-ban"></i> Deprecate</button>' : '<span class="text-xs text-slate-600 italic">Archived</span>') +
                    '</td>' +
                '</tr>';
            }).join('');
        }

        async function deactivateMemory(id) {
            if (!confirm('Are you sure you want to deprecate memory [' + id + ']?')) return;
            try {
                const res = await fetch('/api/v1/memories/' + id, { method: 'DELETE' });
                if (res.ok) {
                    await fetchStats();
                    await fetchMemories();
                } else {
                    alert('Failed to deprecate memory.');
                }
            } catch (err) {
                console.error('Error deprecating memory:', err);
            }
        }

        function escapeHtml(text) {
            if (text == null) return '';
            return String(text).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#039;');
        }

        // Initialize immediately and on DOM load
        function init() {
            fetchWorkspaces();
            fetchStats();
            fetchMemories();
        }

        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', init);
        } else {
            init();
        }
    </script>
</body>
</html>
"""

@router.get("/dashboard", response_class=HTMLResponse)
async def serve_dashboard():
    """Serves the embedded Tailwind SPA Memory Inspector dashboard."""
    return HTMLResponse(content=DASHBOARD_HTML)

@router.get("/api/v1/workspaces", response_model=List[str])
async def get_workspaces():
    """Returns list of distinct workspaces/projects in the memory store."""
    return await sqlite_store.get_all_workspaces()

@router.get("/api/v1/stats")
async def get_stats(workspace_id: Optional[str] = Query(None)):
    """Returns aggregated memory engine metrics and DB storage footprint."""
    return await sqlite_store.get_engine_stats(workspace_id=workspace_id)

@router.get("/api/v1/memories", response_model=List[Dict[str, Any]])
async def list_memories(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    include_inactive: bool = Query(True),
    workspace_id: Optional[str] = Query(None)
):
    """Lists memories for inspection with pagination and active/deprecated filter."""
    return await sqlite_store.list_all_memories(
        limit=limit,
        offset=offset,
        include_inactive=include_inactive,
        workspace_id=workspace_id
    )

@router.delete("/api/v1/memories/{memory_id}")
async def deprecate_memory(memory_id: str):
    """Soft-deprecates an active memory item via Last-Write-Wins logic."""
    success = await sqlite_store.deactivate_memory(memory_id)
    if not success:
        raise HTTPException(status_code=404, detail="Memory item not found or already inactive.")
    return {"status": "success", "id": memory_id, "is_active": 0}
