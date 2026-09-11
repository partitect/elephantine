<div align="center">

# 🐘 Elephantine

### *大象永不遗忘。您的 AI 智能体也当如此。*

**专为自主 AI 智能体打造的零 GPU、本地优先、CPU 原生记忆层**

[![PyPI Version](https://img.shields.io/pypi/v/elephantine.svg?color=blue)](https://pypi.org/project/elephantine/)
[![CI & Quality Gate](https://github.com/partitect/elephantine/actions/workflows/ci.yml/badge.svg)](https://github.com/partitect/elephantine/actions/workflows/ci.yml)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](../LICENSE)
[![Python Version](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-brightgreen.svg)](https://python.org)
[![MCP Ready](https://img.shields.io/badge/MCP-Protocol%20Ready-blueviolet.svg)](https://modelcontextprotocol.io/)
[![CPU Native](https://img.shields.io/badge/Hardware-100%25%20CPU%20Native-orange.svg)](#基准测试与性能-benchmarks)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](#参与贡献)

<p align="center">
  <a href="#为什么选择-elephantine">为什么选择 Elephantine？</a> •
  <a href="#系统架构">架构</a> •
  <a href="#快速上手">快速上手</a> •
  <a href="#多智能体共享工作区">多智能体工作区</a> •
  <a href="#webui-控制面板--知识图谱">控制面板 & 图谱</a> •
  <a href="#一键式-ide--智能体配置-mcp">一键 IDE 配置</a> •
  <a href="#终端-cli-命令">终端 CLI</a> •
  <a href="#多语言-sdk-支持">SDK (Python & TS)</a> •
  <a href="#企业级-rbac--安全认证">企业级 RBAC</a> •
  <a href="#基准测试与性能-benchmarks">性能基准</a>
</p>

<p align="center">
  <b>语言 / Translations:</b>
  <a href="../README.md">English</a> |
  <a href="README_tr.md">Türkçe</a> |
  <a href="README_zh.md">简体中文</a> |
  <a href="README_es.md">Español</a> |
  <a href="README_ja.md">日本語</a>
</p>

---

<br/>

<a href="#webui-控制面板--知识图谱">
  <img src="../docs/assets/dashboard_mockup.svg" alt="Elephantine Memory Inspector Dashboard" width="100%" />
</a>

<br/>

</div>

## 🐘 设计理念

传说大象能在流沙变迁数十年后依然准确找到水源。而现代 AI 智能体，一旦上下文窗口（Context Window）滑落关闭，就会立即忘却您的偏好与决策。

**Elephantine** 为您的智能体赋予坚固、持久的记忆能力。专为通用消费级 CPU（2 vCPU / 4 GB RAM）从零构建，Elephantine **无需 GPU**、**无任何外部 API 调用**，通过嵌入式 LanceDB 与 SQLite 直接在本地宿主机磁盘存储，保障**零数据泄漏**。

---

## ⚡ 核心亮点

- 🏎 **100% CPU 原生执行**：基于 ONNX Runtime 及 AVX-512 SIMD 线程绑定优化，在 2 vCPU 服务器上实现低于 35ms 的召回延迟。无需 CUDA，无臃肿 PyTorch 依赖。
- 👥 **多智能体共享工作区**：跨团队（Coder、Tester、Architect）无缝共享记忆池（`workspace_id`），并通过**基于角色的权限共识**（`role_authority`）防止初级智能体篡改资深架构师的关键决策。
- 📊 **内置 WebUI 检查器 & 交互式知识图谱**：实时交互式控制面板（`/dashboard`），展现引擎核心 KPI、记忆台账以及基于 **Cytoscape.js** 的关系图谱可视化画布。
- 🦙 **进程内 GGUF SLM 提取**：内置轻量级 `llama-cpp-python`（`Qwen2.5-0.5B-Instruct`），纯本地实现结构化实体提取，无需运行独立后台大模型服务。
- 🕸 **图记忆与知识三元组**：原生主-谓-宾语义知识图谱（`/graph/query`），无缝整合进混合检索流程。
- ⚙️ **程序化记忆与工作流追踪**：记录工具调用历史及沉淀多步骤执行流程（`/procedural/track`）。
- 🔒 **本地优先与零泄漏**：嵌入式 LanceDB（Arrow/C++）向量引擎 + SQLite WAL 日志。数据永远保留在您的本地文件系统。
- 🔌 **通用智能体协议支持（MCP & REST）**：原生支持 **Google Antigravity**、**OpenAI Codex**、**Cursor Composer**、**GitHub Copilot**、**Windsurf** 和 **Claude Desktop**，提供一键自动 CLI 配置。
- 🛡️ **企业级 RBAC 与安全认证**：可配置的 `RoleBasedAuthEngine`，提供多级角色权限（`admin`, `architect`, `editor`, `viewer`）与 API Key / Bearer 鉴权支持。

---

<a id="为什么选择-elephantine"></a>
## ⚖️ 为什么选择 Elephantine？

| 功能 / 指标 | 云端记忆 / 托管 RAG | 传统向量数据库 | 🐘 **ELEPHANTINE** |
|---|---|---|---|
| **GPU 依赖** | 强制需要 / 云端计费 | 通常需要 | **零依赖（100% CPU 原生）** |
| **数据隐私** | 泄漏至第三方云服务 | 需托管独立服务器 | **100% 本地宿主机存储（嵌入式）** |
| **记忆维度** | 仅语义向量 | 仅向量嵌入 | **语义 + 程序化 + 知识图谱** |
| **多智能体协作** | 租户间隔离孤岛 | 无内置共识机制 | **工作区共享池 + 角色权限控制** |
| **冷启动内存** | 不适用（外部服务） | 1.5 GB - 4 GB+ | **< 400 MB** |
| **召回延迟（CPU）** | 120ms - 400ms（网络开销）| 50ms - 150ms | **~35ms (p50)** |
| **运维成本** | 每智能体 $20 - $200+/月 | 专用虚拟机费用 | **$0.00（直接运行于现有宿主机）** |
| **MCP 协议集成** | 需手写 API 胶水代码 | 需自建适配层 | **原生一键支持（stdio / sse）** |

---

<a id="系统架构"></a>
## 🏗️ 系统架构

<br/>

<div align="center">
  <img src="../docs/assets/architecture.png" alt="Elephantine 架构 - CPU 原生 AI 记忆基础设施" width="100%" />
</div>

<br/>

---

<a id="快速上手"></a>
## 🚀 快速上手与 CLI 安装

### 1. 安装 Elephantine CLI

通过主流 Python 包管理器安装 Elephantine 后，`elephantine` 命令会自动添加到系统终端 PATH：

```bash
# 推荐：使用 pipx 独立全局安装 CLI
pipx install elephantine

# 或使用 uv
uv tool install elephantine

# 或使用标准 pip
pip install elephantine
```

> [!TIP]
> 安装完成后，您可以在终端中直接调用所有命令（如 `elephantine start`、`elephantine install-antigravity`、`elephantine remember` 等）。如果环境 PATH 未生效，亦可通过 `python -m elephantine.cli <子命令>` 执行。

### 2. 启动引擎服务与 WebUI 控制面板
```bash
elephantine start --port 8765
```
在浏览器中打开 [http://localhost:8765/dashboard](http://localhost:8765/dashboard) 即可访问实时记忆检查器！

### 方式 B：源码安装（面向贡献者）
```bash
# 1. 克隆代码仓库
git clone https://github.com/partitect/elephantine.git
cd elephantine

# 2. 使用 uv 创建并激活虚拟环境
uv venv .venv
# Windows: .venv\Scripts\activate | Linux/macOS: source .venv/bin/activate
uv pip install -e ".[dev]"

# 3. 启动引擎服务与面板
elephantine start --port 8765
```

---

<a id="一键式-ide--智能体配置-mcp"></a>
## 🔌 一键式 IDE & 智能体配置 (MCP)

Elephantine 通过原生 **Model Context Protocol (MCP)** 无缝对接主流开发工具：

### ⚡ 1 秒极速 CLI 自动安装
在已安装 `elephantine` CLI 的环境下，无需手动寻找和编辑 JSON 文件，一键完成配置：


```bash
# Google Antigravity (AGY)
elephantine install-antigravity

# OpenAI Codex & GitHub Copilot
elephantine install-codex

# Cursor Composer & Editor
elephantine install-cursor

# Claude Desktop
elephantine install-claude

# VS Code 项目工作区 (.vscode/settings.json)
elephantine install-vscode
```

### 手动查看配置
亦可随时查看可供直接复制的配置内容：
```bash
elephantine config-antigravity
elephantine config-codex
elephantine config-cursor
elephantine config-claude
```

---

<a id="终端-cli-命令"></a>
## 💻 终端直接执行 CLI 命令

无需编写代码或打开浏览器，直接在终端中记录与检索记忆：

```bash
# 1. 记录记忆（指定工作区与权威权重）
elephantine remember "数据库必须严格采用安装了 pgvector 扩展的 PostgreSQL 16。" \
  --workspace phoenix-core \
  --category architecture \
  --authority 1.0

# 2. 混合检索召回记忆
elephantine recall "我们采用哪种数据库引擎？" \
  --workspace phoenix-core \
  --top-k 3
```

---

<a id="多智能体共享工作区"></a>
## 👥 多智能体共享工作区

通过持久化记忆池和层级权限防护机制，协调各智能体（如 Coder、Tester、Architect）高效协作：

```python
from elephantine.client import ElephantineClient

# 连接至本地 Elephantine 守护进程
client = ElephantineClient("http://127.0.0.1:8765")

# 1. 首席架构师设定技术底线 (Authority: 1.0)
client.remember(
    content="数据库必须严格采用安装了 pgvector 扩展的 PostgreSQL 16。",
    category="architecture",
    entity_key="project:db_engine",
    workspace_id="phoenix-core",
    role_authority=1.0
)

# 2. 初级开发智能体尝试变更数据库 (Authority: 0.3)
# -> 被角色权限共识机制拒绝（低权限无法覆盖高权限结论）
client.remember(
    content="为了简便，我们把数据库换成 SQLite 吧。",
    category="architecture",
    entity_key="project:db_engine",
    workspace_id="phoenix-core",
    role_authority=0.3
)

# 3. 测试智能体调取工作区记忆（加权权威重排）
results = client.recall(
    query="我们当前采用哪种数据库引擎？",
    workspace_id="phoenix-core"
)

# 最终确保 PostgreSQL 16 得到维持：
# [architecture] (Authority: 1.0) -> 数据库必须严格采用安装了 pgvector 扩展的 PostgreSQL 16...
```

---

<a id="webui-控制面板--知识图谱"></a>
## 🖥️ WebUI 控制面板 & 交互式知识图谱

访问 `http://localhost:8765/dashboard` 即可体验轻量级记忆检查器：

- **实时记忆台账**：审查活跃与已弃用记忆，查看版本迭代计数与覆盖状态。
- **🕸 交互式知识图谱 (Cytoscape.js)**：提供力导向（CoSE）、圆形与同心圆布局，交互式展现抽取出的实体三元组网络。
- **点击穿透详情**：轻触任一节点或连线关系，侧边栏即刻呈现关联上下文与置信度。
- **权限与冲突追踪**：监控基于角色的修改记录及 LWW（最后写入胜出）弃用链。

---

<a id="多语言-sdk-支持"></a>
## 💻 多语言 SDK 支持

### 1. Python SDK & LangChain 集成
```python
import asyncio
from elephantine.client import AsyncElephantineClient, ElephantineLangChainMemory

async def main():
    async with AsyncElephantineClient("http://127.0.0.1:8765") as client:
        await client.remember(
            content="用户偏好使用带有异步执行器的 pytest 进行测试。",
            category="preference",
            entity_key="dev:test_runner",
            workspace_id="dev-team",
            role_authority=0.8
        )

        res = await client.recall(
            query="测试运行器偏好",
            workspace_id="dev-team",
            top_k=3
        )
        print("召回结果:", res)

    # LangChain 记忆适配器
    chain_memory = ElephantineLangChainMemory(
        base_url="http://127.0.0.1:8765",
        workspace_id="dev-team"
    )
    chain_memory.save_context({"input": "你好"}, {"output": "我已经记住您的偏好了！"})

if __name__ == "__main__":
    asyncio.run(main())
```

### 2. TypeScript / Node.js SDK (`@elephantine/sdk`)
位于 `sdks/typescript/` 目录：

```typescript
import { ElephantineClient } from '@elephantine/sdk';

const client = new ElephantineClient('http://127.0.0.1:8765');

// 存储记忆
await client.remember({
  content: '生产环境发布时间固定在每周二 10:00 UTC。',
  category: 'devops',
  workspaceId: 'infra-team',
  roleAuthority: 0.9
});

// 召回记忆
const res = await client.recall({
  query: '发布时间安排',
  workspaceId: 'infra-team'
});
console.log(res.memories);
```

---

<a id="企业级-rbac--安全认证"></a>
## 🛡️ 企业级 RBAC 与安全认证

针对多团队协作与生产环境部署，Elephantine 提供模块化权限控制体系：

* **预设角色**：
  - `admin`：完全无限制权限（`read`, `write`, `delete`, `admin`）。
  - `architect`：可在全部类别中执行读取、写入和删除。
  - `editor`：可读写活跃记忆。
  - `viewer`：只读召回权限。写入和删除操作将被拦截并返回 HTTP 403 Forbidden。
* **Token 令牌认证**：
  - 环境变量设置 `ELEPHANTINE_AUTH_ENABLED=true` 启用。
  - 支持 `X-API-Key: <key>` 标头及 `Authorization: Bearer <key>` 访问。
  - 默认社区模式（`AUTH_ENABLED=false`）零配置运行，即启即用。

---

<a id="基准测试与性能-benchmarks"></a>
## 📈 基准测试与性能 (Benchmarks)

在通用 **Ubuntu 24.04 VDS（2 vCPU / 4 GB RAM，无 GPU）** 环境下实测：

| 操作项 | 评估指标 | 实测数值 |
|---|---|---|
| **冷启动 RSS 内存** | 空闲状态常驻内存占用 | **310 MB** |
| **完整引擎工作集** | 高并发活跃负载下 | **< 680 MB** |
| **嵌入向量推理 (CPU)** | 归一化 384 维向量 | **14.2 ms** |
| **稠密向量搜索** | LanceDB 余弦相似度检索 | **9.1 ms** |
| **稀疏 BM25 搜索** | SQLite FTS5 全文索引 | **3.2 ms** |
| **混合 `/recall` (p50)** | 端到端全流程延迟 | **36.3 ms** |
| **混合 `/recall` (p95)** | 端到端全流程延迟 | **42.8 ms** |

---

## 🗺️ 发展路线图 (Roadmap)

- [x] **v0.1.0**: 社区核心 MVP（LanceDB + SQLite WAL + ONNX Runtime）。
- [x] **v0.1.1**: 幻觉接地验证器（Hallucination Grounding Validator）与 Pydantic 规范校验。
- [x] **v0.1.2**: 适用于 Cursor 和 Claude Desktop 的原生 FastMCP stdio/SSE 服务。
- [x] **v0.2.0**: 进程内嵌入式 GGUF SLM 提取（基于 llama.cpp 的 `Qwen2.5-0.5B-Instruct`）。
- [x] **v0.2.5**: 图记忆与实体三元组提取（`/graph/query`）。
- [x] **v0.3.0**: 轻量级 WebUI 记忆检查器与时间旅行图可视化工具。
- [x] **v0.3.5**: 多智能体共享工作区与基于角色的权限共识（`workspace_id`, `role_authority`）。
- [x] **v0.3.8**: 一键 IDE 安装器（Antigravity, Codex, Cursor, Claude, VS Code）与 Cytoscape.js 图谱可视化。
- [x] **v0.4.0**: TypeScript / Node.js SDK 与企业级 RBAC 安全鉴权体系。
- [ ] **v1.0.0**: 跨智能体 CRDT 分布式共识与多节点集群同步。

---

<a id="参与贡献"></a>
## 🤝 参与贡献

热烈欢迎系统工程师、AI 研究人员与智能体开发者共同参与建设！

```bash
git clone https://github.com/partitect/elephantine.git
cd elephantine
uv venv .venv
uv pip install -e ".[dev]"
pytest -v tests/
```

---

## 🌟 Star 历史趋势

<div align="center">

[![Star History Chart](https://api.star-history.com/svg?repos=partitect/elephantine&type=Date)](https://star-history.com/#partitect/elephantine&Date)

</div>

---

<div align="center">

**大象永不遗忘。您的 AI 智能体也当如此。**

由 [Partitect](https://github.com/partitect) 及开源社区携手 ❤️ 倾力打造。

</div>
