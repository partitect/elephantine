# 🚀 Elephantine Launch & Viral Growth Kit

This document contains ready-to-copy launch posts, social media templates, benchmark figures, and curator PR descriptions to drive viral growth and stars for [Elephantine](https://github.com/partitect/elephantine).

---

## 1. Hacker News (Show HN)

- **Target URL**: https://news.ycombinator.com/submit
- **Title**: Show HN: Elephantine – A zero-GPU, local-first memory layer for AI agents (CPU-native, MCP)
- **URL**: https://github.com/partitect/elephantine

### First Comment (Maker Comment):
`markdown
Hi HN! We built Elephantine (https://github.com/partitect/elephantine) because we got tired of AI agents forgetting user preferences the second their context window slides shut, or racking up hefty cloud vector-DB bills.

Most existing agent memory frameworks push you toward hosted vector databases, cloud embeddings, or heavyweight GPU setups. We wanted something that:
1. Runs 100% on commodity CPUs (2 vCPU / 4 GB RAM servers or local laptops).
2. Has zero external API dependencies and zero data leakage (embedded LanceDB C++ vector store + SQLite WAL).
3. Plugs directly into developer IDEs via the Model Context Protocol (FastMCP for Cursor Composer and Claude Desktop).
4. Supports Multi-Agent Shared Workspaces where agent teams (Coder, Tester, Architect) can share persistent memory without junior agents overwriting senior architectural decisions (Role-Based Authority Consensus).

Key technical choices:
- Vector Search: Embedded LanceDB (Arrow/C++) with normalized 384-dim embeddings via ONNX Runtime and AVX-512 thread pinning (~14ms CPU embedding latency).
- Hybrid Retrieval: Dense vector cosine similarity + SQLite FTS5 BM25 keyword matching + exponential time decay + role authority weighting.
- P95 Recall Latency: ~42ms end-to-end on pure CPU.
- Built-in WebUI Inspector: A dashboard at :8765/dashboard to inspect active vs deprecated memories and conflict resolution chains in real-time.

It's open source under Apache 2.0:
pip install elephantine
elephantine start

Would love your thoughts, feedback, and questions on the architecture!
`

---

## 2. Reddit Communities

### A. r/LocalLLaMA (Highest Conversion)
- **Title**: I built a local-first, zero-GPU persistent memory layer for autonomous agents (sub-35ms recall on CPU, MCP ready)
- **Post Body**:
`markdown
Hey everyone! One of the biggest challenges with local LLM agents (using Ollama, llama.cpp, or vLLM) is long-term memory. Cloud memory providers leak data and cost money, while running another full embedding GPU service eats up valuable VRAM that your main model needs.

So I built **Elephantine** (https://github.com/partitect/elephantine): an open-source, local-first memory layer designed specifically to run on CPU with zero GPU allocation.

### Highlights:
- **Zero-GPU Footprint**: Uses ONNX Runtime with AVX-512 SIMD thread pinning for all-MiniLM-L6-v2 embeddings. Only ~14ms per embedding on CPU.
- **Embedded Storage**: LanceDB (C++/Arrow) for vectors + SQLite WAL for metadata and BM25 full-text search. No external servers to configure.
- **Multi-Agent Workspace**: Shared memory pool (workspace_id) across agent swarms with Role Authority Consensus (`role_authority` 0.0 - 1.0) so junior agents cannot overwrite lead architect guidelines.
- **Native MCP**: Runs as a FastMCP stdio/SSE server for instant Cursor Composer, Google Antigravity, and Claude Desktop integration.
- **WebUI Inspector**: Built-in dashboard at http://localhost:8765/dashboard to inspect memory ledgers, graph triplets, and deprecation history.

Benchmarks on a basic 2 vCPU / 4 GB RAM VPS:
- Cold start RAM: ~310 MB
- End-to-end hybrid recall (p50): ~36ms
- End-to-end hybrid recall (p95): ~42ms

Repo: https://github.com/partitect/elephantine
License: Apache 2.0
Quickstart: pip install elephantine && elephantine start

Feedback and PRs are super welcome!
```

### B. r/Cursor & r/ClaudeAI
- **Title**: How to give Cursor Composer and Claude Desktop permanent persistent memory with zero API cost (MCP)
- **Focus**: Show how easy it is to add to claude_desktop_config.json and Cursor MCP settings, then ask questions across different days and observe persistent context retention.

---

## 3. X (Twitter / 𝕏) Launch Thread

**Post 1 (Hook + Media):**
> Elephants never forget. Neither should your AI agents. 🐘
>
> Introducing Elephantine: An open-source, zero-GPU, local-first memory layer for autonomous AI agents.
>
> ⚡ Sub-35ms recall on 2 vCPU
> 🔒 100% local (LanceDB + SQLite WAL)
> 🔌 Native Cursor, Antigravity & Claude Desktop MCP
> 👥 Multi-agent team memory
>
> [Attach docs/assets/elephantine_banner.png]
> 🧵👇

**Post 2:**
> Why Elephantine?
>
> Most agent memory stacks force you into hosted cloud vector DBs or heavy GPU clusters.
>
> Elephantine runs on any commodity CPU using ONNX Runtime with AVX-512 thread pinning + embedded LanceDB C++ vector storage.
> Zero GPU needed. Zero data leakage.

**Post 3:**
> It also solves multi-agent memory conflict:
>
> With Role-Based Authority Consensus, your Lead Architect agent can set database baselines, and junior coder agents cannot overwrite them.
>
> Plus, test it interactively via the built-in WebUI Memory Inspector!

**Post 4:**
> 100% Open Source (Apache 2.0).
>
> 📦 pip install elephantine
> 🚀 elephantine start
>
> Star the repo on GitHub: https://github.com/partitect/elephantine

---

## 4. Awesome Lists PR Submissions

### Submit to awesome-mcp-servers:
- **Repository**: https://github.com/punkpeye/awesome-mcp-servers or https://github.com/modelcontextprotocol/servers
- **Section**: Memory / Storage or Agent Tools
- **Entry**:
```markdown
- [Elephantine](https://github.com/partitect/elephantine) - Zero-GPU, local-first, CPU-native cognitive memory layer for AI agents with hybrid search and multi-agent shared workspaces.
```

### Submit to awesome-ai-agents:
```markdown
- [Elephantine](https://github.com/partitect/elephantine) - Local-first persistent memory engine for autonomous AI agents with role-authority consensus and sub-35ms CPU recall.
```