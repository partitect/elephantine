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
    <script src="https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.28.1/cytoscape.min.js"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        body { background-color: #0b0f17; color: #e2e8f0; font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
        .glass-panel { background: rgba(17, 24, 39, 0.75); backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.08); }
        .glass-card { background: rgba(30, 41, 59, 0.5); border: 1px solid rgba(255, 255, 255, 0.05); }
        #cy { width: 100%; height: 580px; background: rgba(15, 23, 42, 0.6); border-radius: 0.75rem; }
    </style>
</head>
<body class="min-h-screen flex flex-col">
    <header class="glass-panel sticky top-0 z-50 px-6 py-4 flex items-center justify-between border-b border-slate-800">
        <div class="flex items-center space-x-3">
            <span class="text-3xl">🐘</span>
            <div>
                <h1 class="text-xl font-bold tracking-tight text-white flex items-center gap-2">
                    ELEPHANTINE
                    <span class="text-xs font-mono uppercase bg-emerald-500/20 text-emerald-400 px-2 py-0.5 rounded border border-emerald-500/30">CPU-Native v0.3.5</span>
                </h1>
                <p class="text-xs text-slate-400">Local-First Cognitive Memory Inspector & Knowledge Graph</p>
            </div>
        </div>
        <div class="flex items-center space-x-3">
            <button onclick="refreshAll();" class="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-sm font-medium border border-slate-700 transition flex items-center gap-2">
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
        </div>

        <!-- Tab Selector & Controls -->
        <div class="glass-panel p-4 rounded-xl flex flex-col md:flex-row gap-4 items-center justify-between">
            <div class="flex items-center space-x-2">
                <button id="tab-btn-memories" onclick="switchTab('memories')" class="px-4 py-2 rounded-lg bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 text-sm font-semibold flex items-center gap-2 transition">
                    <i class="fa-solid fa-brain"></i> Memories Ledger
                </button>
                <button id="tab-btn-graph" onclick="switchTab('graph')" class="px-4 py-2 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-slate-300 border border-slate-700 text-sm font-semibold flex items-center gap-2 transition">
                    <i class="fa-solid fa-diagram-project text-indigo-400"></i> Interactive Knowledge Graph
                </button>
            </div>

            <div class="flex items-center space-x-4 w-full md:w-auto">
                <div class="flex items-center space-x-2">
                    <span class="text-xs text-slate-400 font-mono uppercase"><i class="fa-solid fa-folder-tree text-indigo-400 mr-1"></i>Project:</span>
                    <select id="filter-workspace" onchange="onWorkspaceChange()" class="bg-slate-900 border border-slate-700 text-slate-200 text-xs rounded-lg px-3 py-2 focus:outline-none focus:border-indigo-500 transition">
                        <option value="">All Projects (Global)</option>
                    </select>
                </div>
                <label id="hide-dep-container" class="flex items-center space-x-2 text-sm text-slate-300 cursor-pointer">
                    <input type="checkbox" id="filter-active-only" onchange="fetchMemories()" class="rounded border-slate-700 text-emerald-500 focus:ring-0">
                    <span>Hide Deprecated</span>
                </label>
            </div>
        </div>

        <!-- TAB 1: Memory Ledger Table -->
        <div id="view-memories" class="space-y-4">
            <div class="relative w-full">
                <i class="fa-solid fa-magnifying-glass absolute left-3.5 top-3.5 text-slate-500"></i>
                <input type="text" id="filter-input" placeholder="Search memories, entity keys, namespaces..." oninput="filterMemories()" 
                    class="w-full bg-slate-900/90 border border-slate-700 rounded-lg pl-10 pr-4 py-2 text-sm text-slate-200 focus:outline-none focus:border-emerald-500 transition">
            </div>

            <div class="glass-panel rounded-xl overflow-hidden shadow-2xl">
                <div class="px-6 py-4 border-b border-slate-800 flex justify-between items-center">
                    <h2 class="text-base font-semibold text-white flex items-center gap-2">
                        <i class="fa-solid fa-list-check text-emerald-400"></i> Memory Records
                    </h2>
                    <span class="text-xs text-slate-400 font-mono" id="memory-count-label">Loaded 0 records</span>
                </div>
                <div class="overflow-x-auto">
                    <table class="w-full text-left border-collapse text-sm">
                        <thead>
                            <tr class="border-b border-slate-800 text-slate-400 font-mono text-xs uppercase bg-slate-900/40">
                                <th class="py-3 px-4">Status</th>
                                <th class="py-3 px-4">Entity Key</th>
                                <th class="py-3 px-4">Content</th>
                                <th class="py-3 px-4">Project / Agent</th>
                                <th class="py-3 px-4">Version</th>
                                <th class="py-3 px-4">Created At</th>
                                <th class="py-3 px-4 text-right">Actions</th>
                            </tr>
                        </thead>
                        <tbody id="memories-body" class="divide-y divide-slate-800/60 font-sans">
                            <tr>
                                <td colspan="7" class="py-8 text-center text-slate-500">Loading memories...</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- TAB 2: Interactive Knowledge Graph View -->
        <div id="view-graph" class="space-y-4 hidden">
            <div class="glass-panel p-4 rounded-xl flex flex-wrap items-center justify-between gap-3">
                <div class="flex items-center space-x-2">
                    <span class="text-xs font-mono uppercase text-slate-400">Layout:</span>
                    <button onclick="applyGraphLayout('cose')" class="px-3 py-1 bg-slate-800 hover:bg-slate-700 text-xs rounded border border-slate-700 text-slate-200">Force (CoSE)</button>
                    <button onclick="applyGraphLayout('circle')" class="px-3 py-1 bg-slate-800 hover:bg-slate-700 text-xs rounded border border-slate-700 text-slate-200">Circle</button>
                    <button onclick="applyGraphLayout('concentric')" class="px-3 py-1 bg-slate-800 hover:bg-slate-700 text-xs rounded border border-slate-700 text-slate-200">Concentric</button>
                </div>
                <div class="flex items-center space-x-2">
                    <button onclick="cy && cy.fit(50)" class="px-3 py-1 bg-slate-800 hover:bg-slate-700 text-xs rounded border border-slate-700 text-slate-200"><i class="fa-solid fa-compress mr-1"></i>Fit</button>
                    <button onclick="cy && cy.zoom(cy.zoom() * 1.2)" class="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-xs rounded border border-slate-700 text-slate-200"><i class="fa-solid fa-plus"></i></button>
                    <button onclick="cy && cy.zoom(cy.zoom() * 0.8)" class="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-xs rounded border border-slate-700 text-slate-200"><i class="fa-solid fa-minus"></i></button>
                    <span id="graph-count-label" class="text-xs font-mono text-indigo-400 ml-2">0 relations</span>
                </div>
            </div>

            <div class="grid grid-cols-1 lg:grid-cols-4 gap-4">
                <div class="lg:col-span-3 glass-panel p-2 rounded-xl relative">
                    <div id="cy"></div>
                </div>
                <div class="lg:col-span-1 glass-panel p-4 rounded-xl space-y-3">
                    <h3 class="text-sm font-semibold text-white flex items-center gap-2 border-b border-slate-800 pb-2">
                        <i class="fa-solid fa-circle-info text-indigo-400"></i> Inspector
                    </h3>
                    <div id="graph-inspector" class="text-xs text-slate-400 space-y-2">
                        <p class="italic">Click on any node or connection arrow in the graph to inspect entity attributes and source relations.</p>
                    </div>
                </div>
            </div>
        </div>
    </main>

    <script>
        let allMemories = [];
        let currentWorkspace = '';
        let currentTab = 'memories';
        let cy = null;

        function switchTab(tab) {
            currentTab = tab;
            const tabMem = document.getElementById('tab-btn-memories');
            const tabGraph = document.getElementById('tab-btn-graph');
            const viewMem = document.getElementById('view-memories');
            const viewGraph = document.getElementById('view-graph');

            if (tab === 'memories') {
                tabMem.className = 'px-4 py-2 rounded-lg bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 text-sm font-semibold flex items-center gap-2 transition';
                tabGraph.className = 'px-4 py-2 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-slate-300 border border-slate-700 text-sm font-semibold flex items-center gap-2 transition';
                viewMem.classList.remove('hidden');
                viewGraph.classList.add('hidden');
            } else {
                tabGraph.className = 'px-4 py-2 rounded-lg bg-indigo-500/20 text-indigo-400 border border-indigo-500/30 text-sm font-semibold flex items-center gap-2 transition';
                tabMem.className = 'px-4 py-2 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-slate-300 border border-slate-700 text-sm font-semibold flex items-center gap-2 transition';
                viewMem.classList.add('hidden');
                viewGraph.classList.remove('hidden');
                fetchGraphData();
            }
        }

        async function fetchWorkspaces() {
            try {
                const res = await fetch('/api/v1/workspaces');
                const workspaces = await res.json();
                const select = document.getElementById('filter-workspace');
                const prev = select.value;
                select.innerHTML = '<option value="">All Projects (Global)</option>';
                workspaces.forEach(ws => {
                    const opt = document.createElement('option');
                    opt.value = ws;
                    opt.textContent = ws;
                    select.appendChild(opt);
                });
                select.value = prev;
            } catch (err) {
                console.error('Error fetching workspaces:', err);
            }
        }

        function onWorkspaceChange() {
            currentWorkspace = document.getElementById('filter-workspace').value;
            fetchStats();
            fetchMemories();
            if (currentTab === 'graph') {
                fetchGraphData();
            }
        }

        async function fetchStats() {
            try {
                let url = '/api/v1/stats';
                if (currentWorkspace) url += '?workspace_id=' + encodeURIComponent(currentWorkspace);
                const res = await fetch(url);
                const data = await res.json();
                
                document.getElementById('stat-total').innerText = (data.total_memories || 0).toLocaleString();
                document.getElementById('stat-active').innerText = (data.active_memories || 0).toLocaleString();
                document.getElementById('stat-deprecated').innerText = (data.deprecated_memories || 0).toLocaleString();
                document.getElementById('stat-entities').innerText = (data.unique_entities || 0).toLocaleString();
                document.getElementById('stat-size').innerText = '(' + (data.db_size_kb || 0).toLocaleString() + ' KB)';
            } catch (err) {
                console.error('Error fetching stats:', err);
            }
        }

        async function fetchMemories() {
            const activeOnly = document.getElementById('filter-active-only').checked;
            try {
                let url = '/api/v1/memories?limit=250&include_inactive=' + (!activeOnly);
                if (currentWorkspace) url += '&workspace_id=' + encodeURIComponent(currentWorkspace);
                const res = await fetch(url);
                allMemories = await res.json();
                filterMemories();
            } catch (err) {
                console.error('Error fetching memories:', err);
                document.getElementById('memories-body').innerHTML = '<tr><td colspan="7" class="py-8 text-center text-rose-500">Failed to load memories.</td></tr>';
            }
        }

        function filterMemories() {
            const q = (document.getElementById('filter-input').value || '').toLowerCase().trim();
            if (!q) {
                renderMemories(allMemories);
                return;
            }
            const filtered = allMemories.filter(m => 
                (m.content && m.content.toLowerCase().includes(q)) ||
                (m.entity_key && m.entity_key.toLowerCase().includes(q)) ||
                (m.source_agent && m.source_agent.toLowerCase().includes(q)) ||
                (m.category && m.category.toLowerCase().includes(q)) ||
                (m.workspace_id && m.workspace_id.toLowerCase().includes(q))
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

        async function fetchGraphData() {
            try {
                let url = '/api/v1/graph/all?limit=300';
                if (currentWorkspace) url += '&workspace_id=' + encodeURIComponent(currentWorkspace);
                const res = await fetch(url);
                const data = await res.json();
                
                const countLabel = document.getElementById('graph-count-label');
                if (countLabel) countLabel.innerText = data.total_triplets + ' relations (' + (data.nodes ? data.nodes.length : 0) + ' nodes)';
                renderGraph(data.nodes || [], data.edges || []);
            } catch (err) {
                console.error('Error fetching graph data:', err);
            }
        }

        function renderGraph(nodes, edges) {
            const container = document.getElementById('cy');
            if (!container) return;

            const elements = [];
            nodes.forEach(n => {
                elements.push({
                    data: { id: n.id, label: n.label, type: n.type }
                });
            });

            edges.forEach(e => {
                elements.push({
                    data: { id: e.id, source: e.source, target: e.target, label: e.label, confidence: e.confidence }
                });
            });

            if (cy) {
                cy.destroy();
            }

            cy = cytoscape({
                container: container,
                elements: elements,
                style: [
                    {
                        selector: 'node',
                        style: {
                            'background-color': '#6366f1',
                            'label': 'data(label)',
                            'color': '#f8fafc',
                            'font-size': '11px',
                            'text-valign': 'center',
                            'text-halign': 'center',
                            'width': '38px',
                            'height': '38px',
                            'border-width': 2,
                            'border-color': '#818cf8',
                            'text-outline-width': 2,
                            'text-outline-color': '#0f172a'
                        }
                    },
                    {
                        selector: 'node[type = "subject"]',
                        style: {
                            'background-color': '#10b981',
                            'border-color': '#34d399'
                        }
                    },
                    {
                        selector: 'edge',
                        style: {
                            'width': 2,
                            'line-color': '#475569',
                            'target-arrow-color': '#94a3b8',
                            'target-arrow-shape': 'triangle',
                            'curve-style': 'bezier',
                            'label': 'data(label)',
                            'font-size': '9px',
                            'color': '#94a3b8',
                            'text-rotation': 'autorotate',
                            'text-margin-y': -8,
                            'text-background-opacity': 0.8,
                            'text-background-color': '#0f172a',
                            'text-background-padding': 2
                        }
                    },
                    {
                        selector: ':selected',
                        style: {
                            'border-width': 3,
                            'border-color': '#f59e0b',
                            'line-color': '#f59e0b',
                            'target-arrow-color': '#f59e0b'
                        }
                    }
                ],
                layout: {
                    name: 'cose',
                    animate: false,
                    padding: 30
                }
            });

            cy.on('tap', 'node', function(evt) {
                const node = evt.target;
                const d = node.data();
                const insp = document.getElementById('graph-inspector');
                insp.innerHTML = 
                    '<div class="space-y-2">' +
                    '<div class="text-xs uppercase font-mono text-indigo-400">Node Entity</div>' +
                    '<div class="text-base font-bold text-white">' + escapeHtml(d.label) + '</div>' +
                    '<div class="text-xs text-slate-400">Type: <span class="text-emerald-400 font-mono">' + escapeHtml(d.type || 'entity') + '</span></div>' +
                    '<div class="text-xs text-slate-400">Connected relations: <span class="font-bold text-white">' + node.connectedEdges().length + '</span></div>' +
                    '</div>';
            });

            cy.on('tap', 'edge', function(evt) {
                const edge = evt.target;
                const d = edge.data();
                const insp = document.getElementById('graph-inspector');
                insp.innerHTML = 
                    '<div class="space-y-2">' +
                    '<div class="text-xs uppercase font-mono text-emerald-400">Relationship Triplet</div>' +
                    '<div class="p-2 rounded bg-slate-900 border border-slate-800 text-xs font-mono">' +
                    '<span class="text-emerald-400">' + escapeHtml(d.source) + '</span> ' +
                    '<span class="text-indigo-400">[' + escapeHtml(d.label) + ']</span> ' +
                    '<span class="text-amber-400">' + escapeHtml(d.target) + '</span>' +
                    '</div>' +
                    '<div class="text-xs text-slate-400">Confidence: <span class="text-white">' + (d.confidence != null ? d.confidence : 1.0) + '</span></div>' +
                    '</div>';
            });
        }

        function applyGraphLayout(name) {
            if (!cy) return;
            cy.layout({ name: name, animate: true, animationDuration: 400 }).run();
        }

        function escapeHtml(text) {
            if (text == null) return '';
            return String(text).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#039;');
        }

        function refreshAll() {
            fetchWorkspaces();
            fetchStats();
            if (currentTab === 'memories') {
                fetchMemories();
            } else {
                fetchGraphData();
            }
        }

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
    """Serves the embedded Tailwind SPA Memory Inspector & Knowledge Graph visualizer."""
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

@router.get("/api/v1/graph/all")
async def get_graph_all(
    workspace_id: Optional[str] = Query(None),
    limit: int = Query(200, ge=1, le=1000)
):
    """Returns knowledge graph triplets formatted for Cytoscape.js network visualizer."""
    triplets = await sqlite_store.get_all_graph_triplets(workspace_id=workspace_id, limit=limit)
    nodes_map: Dict[str, Dict[str, Any]] = {}
    edges: List[Dict[str, Any]] = []

    for t in triplets:
        s = t["subject"]
        o = t["object"]
        p = t["predicate"]

        if s not in nodes_map:
            nodes_map[s] = {"id": s, "label": s, "type": "subject"}
        if o not in nodes_map:
            nodes_map[o] = {"id": o, "label": o, "type": "object"}

        edges.append({
            "id": t["id"],
            "source": s,
            "target": o,
            "label": p,
            "confidence": t.get("confidence", 1.0),
            "source_memory_id": t.get("source_memory_id")
        })

    return {
        "nodes": list(nodes_map.values()),
        "edges": edges,
        "total_triplets": len(triplets)
    }

@router.delete("/api/v1/memories/{memory_id}")
async def deprecate_memory(memory_id: str):
    """Soft-deprecates an active memory item via Last-Write-Wins logic."""
    success = await sqlite_store.deactivate_memory(memory_id)
    if not success:
        raise HTTPException(status_code=404, detail="Memory item not found or already inactive.")
    return {"status": "success", "id": memory_id, "is_active": 0}
