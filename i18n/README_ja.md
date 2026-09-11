<div align="center">

# 🐘 Elephantine

### *象は決して忘れない。あなたのAIエージェントも同じです。*

**自律型AIエージェントのためのGPU不要・ローカルファースト・CPUネイティブ記憶レイヤー**

[![PyPI Version](https://img.shields.io/pypi/v/elephantine.svg?color=blue)](https://pypi.org/project/elephantine/)
[![CI & Quality Gate](https://github.com/partitect/elephantine/actions/workflows/ci.yml/badge.svg)](https://github.com/partitect/elephantine/actions/workflows/ci.yml)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](../LICENSE)
[![Python Version](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-brightgreen.svg)](https://python.org)
[![MCP Ready](https://img.shields.io/badge/MCP-Protocol%20Ready-blueviolet.svg)](https://modelcontextprotocol.io/)
[![CPU Native](https://img.shields.io/badge/Hardware-100%25%20CPU%20Native-orange.svg)](#ベンチマークと性能評価-benchmarks)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](#コントリビューション)

<p align="center">
  <a href="#なぜ-elephantine-なのか">なぜ Elephantine なのか？</a> •
  <a href="#アーキテクチャ">アーキテクチャ</a> •
  <a href="#クイックスタート">クイックスタート</a> •
  <a href="#マルチエージェント共有ワークスペース">共有ワークスペース</a> •
  <a href="#webui-ダッシュボード">ダッシュボード</a> •
  <a href="#ide--エージェント設定-mcp">Cursor, Codex & Claude</a> •
  <a href="#python-sdk--langchain-統合">Python SDK</a> •
  <a href="#ベンチマークと性能評価-benchmarks">ベンチマーク</a>
</p>

<p align="center">
  <b>言語 / Translations:</b>
  <a href="../README.md">English</a> |
  <a href="README_tr.md">Türkçe</a> |
  <a href="README_zh.md">简体中文</a> |
  <a href="README_es.md">Español</a> |
  <a href="README_ja.md">日本語</a>
</p>

---

<br/>

<a href="#webui-ダッシュボード">
  <img src="../docs/assets/dashboard_mockup.svg" alt="Elephantine Memory Inspector Dashboard" width="100%" />
</a>

<br/>

</div>

## 🐘 開発思想

伝説によれば、象は何十年も流動する砂漠の中でかつてあった水場を決して忘れないと言われています。一方、現代のAIエージェントはコンテキストウィンドウ（Context Window）が閉じた瞬間に、ユーザーの好みやこれまでの決定事項をすべて忘れてしまいます。

**Elephantine** は、エージェントに永続的で揺るぎない記憶を提供します。一般的な標準CPU（2 vCPU / 4 GB RAM）向けにゼロから設計された Elephantine は、**GPUを一切必要とせず**、**外部APIへの通信も行わず**、組み込みの LanceDB と SQLite を使用してホストディスクに直接永続化することで**データ漏洩ゼロ**を保証します。

---

## ⚡ 主な特徴

- 🏎 **100% CPUネイティブ実行**: ONNX Runtime と AVX-512 SIMD スレッド最適化により、2 vCPU サーバー環境で 35ms 未満のリコールレイテンシを実現。CUDA不要、重厚な PyTorch 依存もありません。
- 👥 **マルチエージェント共有ワークスペース**: 開発チーム（Coder、Tester、Architect）間でメモリプール（`workspace_id`）をシームレスに共有。**ロールベース権限コンセンサス**（`role_authority`）により、ジュニアエージェントがシニアアーキテクトの設計判断を誤って上書きすることを防止します。
- 📊 **組み込み WebUI インスペクター**: リアルタイムダッシュボード（`/dashboard`）により、エンジンKPI、記憶台帳、衝突履歴、ナレッジグラフの関係性を可視化。
- 🦙 **インプロセス GGUF SLM 抽出**: 外部LLMサーバーを立てることなく、組み込み `llama-cpp-python`（`Qwen2.5-0.5B-Instruct`）によりローカルで構造化エンティティ抽出を実行。
- 🕸 **グラフメモリと知識トリプレット**: 主語-述語-目的語の意味的知識グラフ（`/graph/query`）をハイブリッド検索パイプラインに直接統合。
- 🔒 **ローカルファースト＆ゼロデータ漏洩**: 組み込み LanceDB（Arrow/C++）ベクトルストア + SQLite WAL。データがホストマシンのファイルシステム外に出ることはありません。
- 🔌 **ユニバーサルエージェント対応（MCP & REST）**: **OpenAI Codex**、**Cursor Composer**、**GitHub Copilot**、**Windsurf**、**Claude Desktop** と追加設定なしでネイティブ接続。

---

<a id="なぜ-elephantine-なのか"></a>
## ⚖️ なぜ Elephantine なのか？

| 機能 / 指標 | クラウドメモリ / 外部RAG | 従来のベクトルDB | 🐘 **ELEPHANTINE** |
|---|---|---|---|
| **GPU 依存度** | 必須 / クラウド従量課金 | 頻繁に要求される | **不要（100% CPUネイティブ）** |
| **データプライバシー** | サードパーティクラウドへ流出 | 専用ホストサーバーが必要 | **100% ローカル完結（組み込み型）** |
| **記憶の次元** | 意味ベクトルのみ | ベクトル埋め込みのみ | **意味論 + 手順的 + 知識グラフ** |
| **マルチエージェント協調** | テナント間サイロ化 | 内蔵コンセンサスなし | **ワークスペース共有 + ロール権限制御** |
| **コールドスタートメモリ** | 対象外（外部通信） | 1.5 GB - 4 GB以上 | **< 400 MB** |
| **検索レイテンシ (CPU)** | 120ms - 400ms（通信遅延） | 50ms - 150ms | **~35ms (p50)** |
| **運用コスト** | 1エージェントあたり月額 $20 - $200+ | 専用VMの維持費用 | **$0.00（既存サーバーで動作）** |
| **MCP 統合** | 手作業のグルーコードが必要 | カスタムラッパーが必要 | **ネイティブ 1クリック対応（stdio / sse）** |

---

<a id="アーキテクチャ"></a>
## 🏗️ アーキテクチャ

<br/>

<div align="center">
  <img src="../docs/assets/architecture.png" alt="Elephantine アーキテクチャ - CPUネイティブ AI メモリインフラストラクチャ" width="100%" />
</div>

<br/>

---

<a id="クイックスタート"></a>
## 🚀 クイックスタート（30秒で開始）

### 方法 A: pip によるインストール（推奨）
```bash
pip install elephantine

# エンジンサーバーとダッシュボードの起動
elephantine start --port 8765
```

### 方法 B: ソースコードから（開発者向け）
```bash
# 1. リポジトリのクローン
git clone https://github.com/partitect/elephantine.git
cd elephantine

# 2. uv による仮想環境の構築
uv venv .venv
# Windows: .venv\Scripts\activate | Linux/macOS: source .venv/bin/activate
uv pip install -e ".[dev]"

# 3. エンジンサーバーの起動
elephantine start --port 8765
```

ブラウザで [http://localhost:8765/dashboard](http://localhost:8765/dashboard) を開くと、ライブメモリインスペクターが表示されます！

---

<a id="マルチエージェント共有ワークスペース"></a>
## 👥 マルチエージェント共有ワークスペース

永続的なメモリプールと階層的権限保護により、複数のエージェント（例：Coder、Tester、Architect）を協調動作させます：

```python
from elephantine.client import ElephantineClient

# ローカルの Elephantine デーモンへ接続
client = ElephantineClient("http://127.0.0.1:8765")

# 1. 主席アーキテクトが設計方針を決定 (Authority: 1.0)
client.remember(
    content="データベースは必ず pgvector 拡張を導入した PostgreSQL 16 を使用すること。",
    category="architecture",
    entity_key="project:db_engine",
    workspace_id="phoenix-core",
    role_authority=1.0
)

# 2. ジュニア開発エージェントが簡易化のために変更を試みる (Authority: 0.3)
# -> ロール権限コンセンサスにより拒絶されます（下位権限からの上書き保護）
client.remember(
    content="簡単にするためにデータベースを SQLite に変更しましょう。",
    category="architecture",
    entity_key="project:db_engine",
    workspace_id="phoenix-core",
    role_authority=0.3
)

# 3. テスターエージェントがワークスペースの記憶を取得（権限加重リランキング）
results = client.recall(
    query="現在使用しているデータベースエンジンは何ですか？",
    workspace_id="phoenix-core"
)

# PostgreSQL 16 が確実に保持されていることが保証されます：
# [architecture] (Authority: 1.0) -> データベースは必ず PostgreSQL 16 を使用すること...
```

---

<a id="webui-ダッシュボード"></a>
## 🖥️ WebUI ダッシュボード

Elephantine には、`http://localhost:8765/dashboard` でアクセスできる軽量なメモリインスペクターが標準搭載されています：

- **リアルタイム記憶台帳**: 有効な記憶と非推奨（deprecated）になった記憶、リビジョン履歴を一覧表示。
- **権限と衝突の追跡**: ロールベースの変更履歴や LWW（Last-Write-Wins）の世代チェーンを監視。
- **ナレッジグラフビューア**: 抽出された主語-述語-目的語のエンティティ関係トリプレットを探索。
- **ライブ検索＆フィルタ**: 密ベクトルと BM25 のハイブリッド検索をインタラクティブにテスト。

---

<a id="ide--エージェント設定-mcp"></a>
## 🔌 Cursor, OpenAI Codex & Claude Desktop 設定

Elephantine は、ネイティブの **Model Context Protocol (MCP)** および高速ローカル REST エンドポイントを介して、主要なエージェント対応IDEやデスクトップAIクライアントに接続します。

### 1. OpenAI Codex & GitHub Copilot (VS Code)
VS Code や OpenAI Codex を利用する環境の場合：
1. `elephantine config-codex` を実行して設定スニペットを表示します。
2. `.vscode/settings.json`（または MCP 設定ファイル）に追加します：
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
*またはスクリプトからローカル REST API（`http://127.0.0.1:8765/recall`）を直接呼び出すことも可能です。*

### 2. Cursor の設定
1. **Cursor Settings** -> **Features** -> **MCP Servers** -> **Add New MCP Server** を開きます。
2. 以下を入力します：
   - **Name**: `elephantine`
   - **Type**: `command`
   - **Command**: `elephantine mcp`

### 3. Claude Desktop の設定
`elephantine config-claude` を実行するか、`claude_desktop_config.json` に以下を記述します：

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

<a id="python-sdk--langchain-統合"></a>
## 💻 Python SDK & LangChain 統合

Elephantine は同期および非同期クライアントと、LangChain 向けメモリ統合を提供します：

```python
import asyncio
from elephantine.client import AsyncElephantineClient, ElephantineLangChainMemory

async def main():
    async with AsyncElephantineClient("http://127.0.0.1:8765") as client:
        # 意味的エンティティ整合性を保ちながら保存
        await client.remember(
            content="ユーザーは非同期テストランナーを備えた pytest を好む。",
            category="preference",
            entity_key="dev:test_runner",
            workspace_id="dev-team",
            role_authority=0.8
        )

        # 時間減衰とワークスペース分離を適用して検索
        res = await client.recall(
            query="テストランナーの好み",
            workspace_id="dev-team",
            top_k=3
        )
        print("検索結果:", res)

    # LangChain メモリアダプター
    chain_memory = ElephantineLangChainMemory(
        base_url="http://127.0.0.1:8765",
        workspace_id="dev-team"
    )
    chain_memory.save_context({"input": "こんにちは"}, {"output": "あなたの好みを記憶しました！"})

if __name__ == "__main__":
    asyncio.run(main())
```

---

<a id="ベンチマークと性能評価-benchmarks"></a>
## 📈 ベンチマークと性能評価 (Benchmarks)

汎用 **Ubuntu 24.04 VDS (2 vCPU / 4 GB RAM, GPUなし)** 環境での測定値：

| 操作 | 評価指標 | 実測値 |
|---|---|---|
| **コールドスタート RSS メモリ** | アイドル時の常駐メモリ | **310 MB** |
| **エンジン全機能ワーキングセット** | アクティブ負荷動作時 | **< 680 MB** |
| **埋め込みモデル推論 (CPU)** | 正規化 384次元ベクトル | **14.2 ms** |
| **密ベクトル検索** | LanceDB コサイン類似度 | **9.1 ms** |
| **スパース BM25 検索** | SQLite FTS5 インデックス | **3.2 ms** |
| **ハイブリッド `/recall` (p50)** | エンドツーエンド レイテンシ | **36.3 ms** |
| **ハイブリッド `/recall` (p95)** | エンドツーエンド レイテンシ | **42.8 ms** |

---

## 🗺️ ロードマップ (Roadmap)

- [x] **v0.1.0**: コミュニティコア MVP（LanceDB + SQLite WAL + ONNX Runtime）。
- [x] **v0.1.1**: ハルシネーショングランディング検証機構 & Pydantic スキーマ検証器。
- [x] **v0.1.2**: Cursor および Claude Desktop 向けネイティブ FastMCP stdio/SSE サーバー。
- [x] **v0.2.0**: インプロセス組み込み GGUF SLM 抽出（llama.cpp による `Qwen2.5-0.5B-Instruct`）。
- [x] **v0.2.5**: グラフメモリおよびエンティティ関係トリプレット抽出（`/graph/query`）。
- [x] **v0.3.0**: 軽量 WebUI メモリインスペクター & タイムトラベルグラフ可視化ツール。
- [x] **v0.3.5**: マルチエージェント共有ワークスペース & ロールベース権限コンセンサス（`workspace_id`, `role_authority`）。
- [ ] **v1.0.0**: エンタープライズ向けマルチテナント RBAC & エージェント間 CRDT 分散合意。

---

<a id="コントリビューション"></a>
## 🤝 コントリビューション

システムエンジニア、AI研究者、エージェント開発者の皆様からのご参加を心より歓迎いたします！

```bash
git clone https://github.com/partitect/elephantine.git
cd elephantine
uv venv .venv
uv pip install -e ".[dev]"
pytest -v tests/
```

---

## 🌟 Star 履歴

<div align="center">

[![Star History Chart](https://api.star-history.com/svg?repos=partitect/elephantine&type=Date)](https://star-history.com/#partitect/elephantine&Date)

</div>

---

<div align="center">

**象は決して忘れない。あなたのAIエージェントも同じです。**

[Partitect](https://github.com/partitect) およびオープンソースコミュニティにより ❤️ を込めて構築されました。

</div>
