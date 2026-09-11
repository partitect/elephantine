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
  <a href="#webui-控制面板">控制面板</a> •
  <a href="#ide--智能体配置-mcp">Cursor, Codex & Claude</a> •
  <a href="#python-sdk--langchain-集成">Python SDK</a> •
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

<a href="#webui-控制面板">
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
- 📊 **内置 WebUI 检查器**：实时交互式控制面板（`/dashboard`），展现引擎核心 KPI、记忆台账、冲突演进历史及实体关系图谱。
- 🦙 **进程内 GGUF SLM 提取**：内置轻量级 `llama-cpp-python`（`Qwen2.5-0.5B-Instruct`），纯本地实现结构化实体提取，无需运行独立后台大模型服务。
- 🕸 **图记忆与知识三元组**：原生主-谓-宾语义知识图谱（`/graph/query`），无缝整合进混合检索流程。
- 🔒 **本地优先与零泄漏**：嵌入式 LanceDB（Arrow/C++）向量引擎 + SQLite WAL 日志。数据永远保留在您的本地文件系统。
- 🔌 **通用智能体协议支持（MCP & REST）**：开箱即用支持 **OpenAI Codex**、**Cursor Composer**、**GitHub Copilot**、**Windsurf** 和 **Claude Desktop**。

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
## 🚀 快速上手（30 秒）

### 方式 A：通过 pip 安装（推荐）
```bash
pip install elephantine

# 启动引擎服务与控制面板
elephantine start --port 8765
```

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

在浏览器中打开 [http://localhost:8765/dashboard](http://localhost:8765/dashboard) 即可访问实时记忆检查器！

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

<a id="webui-控制面板"></a>
## 🖥️ WebUI 控制面板

Elephantine 内置轻量级记忆检查器，访问地址为 `http://localhost:8765/dashboard`：

- **实时记忆台账**：审查活跃与已弃用记忆，查看版本迭代计数与覆盖状态。
- **权限与冲突追踪**：监控基于角色的修改记录及 LWW（最后写入胜出）弃用链。
- **知识图谱查看器**：交互式浏览抽取出的主-谓-宾关联三元组。
- **实时搜索与筛选**：交互式测试稠密向量 + BM25 混合检索效果。

---

<a id="ide--智能体配置-mcp"></a>
## 🔌 Cursor, OpenAI Codex & Claude Desktop 配置

Elephantine 通过原生 **Model Context Protocol (MCP)** 和高速本地 REST 端点，无缝对接各类智能体 IDE 与桌面 AI 工具。

### 1. OpenAI Codex & GitHub Copilot (VS Code)
针对 VS Code 智能体工作流及 Codex 环境：
1. 运行 `elephantine config-codex` 查看配置信息。
2. 在 `.vscode/settings.json`（或 MCP 配置文件）中添加：
```json
{
  "mcpServers": {
    "elephantine": {
      "command": "elephantine",
      "args": ["mcp"]
    }
  }
}
```
*或直接在脚本中调用本地 REST 检索端点：`http://127.0.0.1:8765/recall`。*

### 2. Cursor 配置
1. 打开 **Cursor Settings** -> **Features** -> **MCP Servers** -> **Add New MCP Server**。
2. 填写信息：
   - **Name**: `elephantine`
   - **Type**: `command`
   - **Command**: `elephantine mcp`

### 3. Claude Desktop 配置
运行 `elephantine config-claude` 或在 `claude_desktop_config.json` 中添加：

```json
{
  "mcpServers": {
    "elephantine": {
      "command": "elephantine",
      "args": ["mcp"]
    }
  }
}
```

---

<a id="python-sdk--langchain-集成"></a>
## 💻 Python SDK & LangChain 集成

Elephantine 提供同步与异步客户端，并原生集成 LangChain 记忆组件：

```python
import asyncio
from elephantine.client import AsyncElephantineClient, ElephantineLangChainMemory

async def main():
    async with AsyncElephantineClient("http://127.0.0.1:8765") as client:
        # 记录记忆并对齐语义实体
        await client.remember(
            content="用户偏好使用带有异步执行器的 pytest 进行测试。",
            category="preference",
            entity_key="dev:test_runner",
            workspace_id="dev-team",
            role_authority=0.8
        )

        # 调取记忆（支持时间衰减与工作区隔离）
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
- [ ] **v1.0.0**: 企业级多租户 RBAC 与跨智能体 CRDT 分布式共识。

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
