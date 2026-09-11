<div align="center">

# 🐘 Elephantine

### *Filler Asla Unutmaz. Yapay Zekâ Ajanlarınız da Unutmayacak.*

**Otonom Yapay Zekâ Ajanları için Sıfır-GPU, Yerel-Öncelikli, CPU-Native Hafıza Katmanı**

[![PyPI Version](https://img.shields.io/pypi/v/elephantine.svg?color=blue)](https://pypi.org/project/elephantine/)
[![CI & Quality Gate](https://github.com/partitect/elephantine/actions/workflows/ci.yml/badge.svg)](https://github.com/partitect/elephantine/actions/workflows/ci.yml)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](../LICENSE)
[![Python Version](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-brightgreen.svg)](https://python.org)
[![MCP Ready](https://img.shields.io/badge/MCP-Protocol%20Ready-blueviolet.svg)](https://modelcontextprotocol.io/)
[![CPU Native](https://img.shields.io/badge/Hardware-100%25%20CPU%20Native-orange.svg)](#performans--kıyaslama-benchmarks)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](#katkıda-bulunma)

<p align="center">
  <a href="#neden-elephantine">Neden Elephantine?</a> •
  <a href="#mimari">Mimari</a> •
  <a href="#hızlı-başlangıç">Hızlı Başlangıç</a> •
  <a href="#çoklu-ajan-ortak-çalışma-alanı">Çoklu Ajan Alanı</a> •
  <a href="#webui-kontrol-paneli">Dashboard</a> •
  <a href="#ide--ajan-kurulumu-mcp">Cursor, Codex & Claude</a> •
  <a href="#python-sdk--langchain-entegrasyonu">Python SDK</a> •
  <a href="#performans--kıyaslama-benchmarks">Kıyaslamalar</a>
</p>

<p align="center">
  <b>Diller / Translations:</b>
  <a href="../README.md">English</a> |
  <a href="README_tr.md">Türkçe</a> |
  <a href="README_zh.md">简体中文</a> |
  <a href="README_es.md">Español</a> |
  <a href="README_ja.md">日本語</a>
</p>

---

<br/>

<a href="#webui-kontrol-paneli">
  <img src="../docs/assets/dashboard_mockup.svg" alt="Elephantine Memory Inspector Dashboard" width="100%" />
</a>

<br/>

</div>

## 🐘 Felsefe

Efsaneye göre filler, değişen çöl kumları arasında onlarca yıl önceki su kaynaklarını dahi hatırlar. Günümüz yapay zekâ ajanları ise bağlam penceresi (context window) kapandığı anda tüm tercihlerinizi ve kararlarınızı unutur.

**Elephantine**, ajanlarınıza kalıcı, sarsılmaz bir hafıza kazandırır. Standart CPU altyapıları (2 vCPU / 4 GB RAM) için sıfırdan inşa edilen Elephantine, **sıfır GPU** gerektirir, **harici API çağrısı yapmaz** ve embedded LanceDB ile SQLite kullanarak **verilerinizin ana makineden asla dışarı sızmamasını** sağlar.

---

## ⚡ Öne Çıkan Özellikler

- 🏎 **%100 CPU-Native Çalışma**: AVX-512 SIMD thread optimizasyonlu ONNX Runtime ile 2 vCPU sunucularda 35ms altı geri çağırma (recall) gecikmesi. CUDA veya PyTorch yükü yok.
- 👥 **Çoklu Ajan Ortak Çalışma Alanı**: Ekipler (Coder, Tester, Architect) arasında paylaşımlı hafıza havuzu (`workspace_id`) ve stajyer/küçük ajanların kıdemli mimari kararları ezmesini önleyen **Rol Tabanlı Otorite Konsensüsü** (`role_authority`).
- 📊 **Dahili WebUI Inspector**: Canlı motor metriklerini, hafıza kayıtlarını, çelişki geçmişini ve bilgi grafiğini gösteren gerçek zamanlı web paneli (`/dashboard`).
- 🦙 **Gömülü GGUF SLM Çıkarımı**: Harici LLM sunucusuna gerek kalmadan, gömülü `llama-cpp-python` (`Qwen2.5-0.5B-Instruct`) ile yerel yapısal hafıza çıkarımı.
- 🕸 **Grafik Bellek (Knowledge Graph)**: Hibrit arama hattına entegre, özne-yüklem-nesne semantik ilişkileri (`/graph/query`).
- 🔒 **Yerel-Öncelikli & Sıfır Veri Sızıntısı**: Embedded LanceDB (Arrow/C++) vektör deposu + SQLite WAL. Verileriniz asla diskinizden ayrılmaz.
- 🔌 **Evrensel Ajan Desteği (MCP & REST)**: **OpenAI Codex**, **Cursor Composer**, **GitHub Copilot**, **Windsurf** ve **Claude Desktop** ile tek tıkla doğrudan entegrasyon.

---

<a id="neden-elephantine"></a>
## ⚖️ Neden Elephantine?

| Özellik / Metrik | Bulut Bellek / Hosted RAG | Geleneksel Vektör DB'ler | 🐘 **ELEPHANTINE** |
|---|---|---|---|
| **GPU Bağımlılığı** | Zorunlu / Bulut faturalı | Sıklıkla gerekli | **Sıfır (%100 CPU-Native)** |
| **Veri Gizliliği** | 3. parti buluta sızar | Barındırılan sunucular | **%100 Yerel / Makinede (Embedded)** |
| **Hafıza Boyutları** | Yalnızca anlamsal | Yalnızca vektör embedding | **Anlamsal + Prosedürel + Grafik** |
| **Çoklu Ajan Ekipleri** | Paylaşımlı tenant izolasyonu | Yerleşik konsensüs yok | **Çalışma Alanı Havuzu + Rol Otoritesi** |
| **Soğuk Başlangıç RAM** | Yok (Harici servis) | 1.5 GB - 4 GB+ | **< 400 MB** |
| **Geri Çağırma Gecikmesi** | 120ms - 400ms (Ağ gecikmesi) | 50ms - 150ms | **~35ms (p50)** |
| **İşletme Maliyeti** | Ajan başı $20 - $200+/ay | Özel VM maliyetleri | **$0.00 (Mevcut sunucuda çalışır)** |
| **MCP Entegrasyonu** | Manuel API ara katmanı | Özel sarmalayıcı gerekli | **Yerel Tek Tıkla (stdio / sse)** |

---

<a id="mimari"></a>
## 🏗️ Mimari

<br/>

<div align="center">
  <img src="../docs/assets/architecture.png" alt="Elephantine Mimarisi - CPU-Native Yapay Zeka Hafıza Altyapısı" width="100%" />
</div>

<br/>

---

<a id="hızlı-başlangıç"></a>
## 🚀 Hızlı Başlangıç (30 Saniyede)

### Seçenek A: pip ile Kurulum (Önerilen)
```bash
pip install elephantine

# Motor sunucusunu ve gösterge panelini başlatın
elephantine start --port 8765
```

### Seçenek B: Kaynak Koddan (Geliştiriciler İçin)
```bash
# 1. Depoyu klonlayın
git clone https://github.com/partitect/elephantine.git
cd elephantine

# 2. uv ile sanal ortam oluşturun
uv venv .venv
# Windows: .venv\Scripts\activate | Linux/macOS: source .venv/bin/activate
uv pip install -e ".[dev]"

# 3. Motor sunucusunu ve paneli başlatın
elephantine start --port 8765
```

Canlı Hafıza Müfettişini (Memory Inspector) görüntülemek için tarayıcınızda [http://localhost:8765/dashboard](http://localhost:8765/dashboard) adresini açın!

---

<a id="çoklu-ajan-ortak-çalışma-alanı"></a>
## 👥 Çoklu Ajan Ortak Çalışma Alanı

Ajan ekiplerini (örneğin Yazılımcı, Test Uzmanı, Mimar) kalıcı bellek havuzları ve hiyerarşik otorite korumasıyla koordine edin:

```python
from elephantine.client import ElephantineClient

# Yerel Elephantine arka plan servisine bağlanın
client = ElephantineClient("http://127.0.0.1:8765")

# 1. Baş Mimar mimari temeli belirler (Otorite: 1.0)
client.remember(
    content="Veritabanı kesinlikle pgvector uzantılı PostgreSQL 16 olmalıdır.",
    category="architecture",
    entity_key="project:db_engine",
    workspace_id="phoenix-core",
    role_authority=1.0
)

# 2. Junior Geliştirici veritabanını değiştirmeye çalışır (Otorite: 0.3)
# -> Rol Otorite Konsensüsü tarafından REDDEDİLİR (düşük otoriteye karşı korumalı)
client.remember(
    content="Basitlik olsun diye proje veritabanını SQLite yapalım.",
    category="architecture",
    entity_key="project:db_engine",
    workspace_id="phoenix-core",
    role_authority=0.3
)

# 3. Test Ajanı çalışma alanı anılarını çağırır (Otorite ağırlıklı yeniden sıralama)
results = client.recall(
    query="Hangi veritabanı motorunu kullanıyoruz?",
    workspace_id="phoenix-core"
)

# PostgreSQL 16 garantili olarak korunur:
# [architecture] (Otorite: 1.0) -> Veritabanı kesinlikle PostgreSQL 16 olmalıdır...
```

---

<a id="webui-kontrol-paneli"></a>
## 🖥️ WebUI Kontrol Paneli (Dashboard)

Elephantine, `http://localhost:8765/dashboard` adresinde çalışan yerleşik, hafif bir Hafıza Müfettişi içerir:

- **Gerçek Zamanlı Bellek Defteri**: Aktif ve kullanımdan kaldırılmış (deprecated) kayıtları, revizyon sayılarını inceleyin.
- **Otorite ve Çelişki Takibi**: Rol tabanlı değişiklikleri ve LWW (Son-Yazan-Kazanır) zincirlerini izleyin.
- **Bilgi Grafiği Görüntüleyici**: Çıkarılan özne-yüklem-nesne ilişki üçlülerini gezin.
- **Canlı Arama ve Filtreleme**: Hibrit yoğun (dense) + BM25 aramalarını etkileşimli olarak test edin.

---

<a id="ide--ajan-kurulumu-mcp"></a>
## 🔌 Cursor, OpenAI Codex & Claude Desktop Kurulumu

Elephantine, yerel **Model Context Protocol (MCP)** ve yüksek hızlı yerel REST uç noktaları aracılığıyla tüm büyük IDE'lere ve masaüstü yapay zekâ istemcilerine bağlanır.

### 1. OpenAI Codex & GitHub Copilot (VS Code)
VS Code ve OpenAI Codex destekli ortamlar için:
1. Kopyalamaya hazır ayarları görmek için `elephantine config-codex` komutunu çalıştırın.
2. `.vscode/settings.json` dosyanıza (veya MCP yapılandırmanıza) ekleyin:
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
*Veya doğrudan Codex/Copilot betiklerinizden `http://127.0.0.1:8765/recall` REST API'sini çağırın.*

### 2. Cursor Kurulumu
1. **Cursor Settings** -> **Features** -> **MCP Servers** -> **Add New MCP Server** yolunu izleyin.
2. Bilgileri girin:
   - **Name**: `elephantine`
   - **Type**: `command`
   - **Command**: `elephantine mcp`

### 3. Claude Desktop Kurulumu
`elephantine config-claude` komutunu çalıştırın veya `claude_desktop_config.json` dosyanıza ekleyin:

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

<a id="python-sdk--langchain-entegrasyonu"></a>
## 💻 Python SDK & LangChain Entegrasyonu

Elephantine, senkron ve asenkron istemcilerin yanı sıra yerel LangChain hafıza adaptörü sunar:

```python
import asyncio
from elephantine.client import AsyncElephantineClient, ElephantineLangChainMemory

async def main():
    async with AsyncElephantineClient("http://127.0.0.1:8765") as client:
        # Semantik varlık hizalaması ile kaydetme
        await client.remember(
            content="Kullanıcı asenkron test çalıştırıcıları ile pytest tercih ediyor.",
            category="preference",
            entity_key="dev:test_runner",
            workspace_id="dev-team",
            role_authority=0.8
        )

        # Zaman sönümlemesi ve çalışma alanı filtrelemesi ile çağırma
        res = await client.recall(
            query="test çalıştırıcı tercihleri",
            workspace_id="dev-team",
            top_k=3
        )
        print("Hatırlanan:", res)

    # LangChain Hafıza Adaptörü
    chain_memory = ElephantineLangChainMemory(
        base_url="http://127.0.0.1:8765",
        workspace_id="dev-team"
    )
    chain_memory.save_context({"input": "Merhaba"}, {"output": "Tercihlerinizi hatırlıyorum!"})

if __name__ == "__main__":
    asyncio.run(main())
```

---

<a id="performans--kıyaslama-benchmarks"></a>
## 📈 Performans & Kıyaslama (Benchmarks)

Standart **Ubuntu 24.04 VDS (2 vCPU / 4 GB RAM, GPU Yok)** üzerinde test edilmiştir:

| İşlem | Metrik | Değer |
|---|---|---|
| **Soğuk Başlangıç RSS Bellek** | Boşta Bellek Ayak İzi | **310 MB** |
| **Tam Motor Çalışma Kümesi** | Aktif Yük Altında | **< 680 MB** |
| **Embedder Çıkarımı (CPU)** | Normalize 384 boyutlu vektör | **14.2 ms** |
| **Yoğun Vektör Araması** | LanceDB kosinüs benzerliği | **9.1 ms** |
| **Seyrek BM25 Araması** | SQLite FTS5 indeksi | **3.2 ms** |
| **Hibrit `/recall` (p50)** | Uçtan Uca Gecikme | **36.3 ms** |
| **Hibrit `/recall` (p95)** | Uçtan Uca Gecikme | **42.8 ms** |

---

## 🗺️ Yol Haritası (Roadmap)

- [x] **v0.1.0**: Topluluk Çekirdeği MVP (LanceDB + SQLite WAL + ONNX Runtime).
- [x] **v0.1.1**: Halüsinasyon Temellendirme Doğrulayıcısı & Pydantic Şema Denetleyicisi.
- [x] **v0.1.2**: Cursor ve Claude Desktop için yerel FastMCP stdio/SSE sunucusu.
- [x] **v0.2.0**: Gömülü GGUF SLM çıkarımı (llama.cpp ile `Qwen2.5-0.5B-Instruct`).
- [x] **v0.2.5**: Grafik Bellek & Varlık Üçlüsü Çıkarımı (`/graph/query`).
- [x] **v0.3.0**: Hafif WebUI Hafıza Müfettişi & Zaman Yolculuğu Grafik Görselleştiricisi.
- [x] **v0.3.5**: Çoklu Ajan Ortak Çalışma Alanı & Rol Tabanlı Otorite Konsensüsü (`workspace_id`, `role_authority`).
- [ ] **v1.0.0**: Kurumsal Çok Kiracılı RBAC & Ajanlar Arası CRDT Konsensüsü.

---

<a id="katkıda-bulunma"></a>
## 🤝 Katkıda Bulunma

Sistem mühendislerinin, yapay zekâ araştırmacılarının ve ajan geliştiricilerinin katkılarını memnuniyetle bekliyoruz!

```bash
git clone https://github.com/partitect/elephantine.git
cd elephantine
uv venv .venv
uv pip install -e ".[dev]"
pytest -v tests/
```

---

## 🌟 Yıldız Geçmişi

<div align="center">

[![Star History Chart](https://api.star-history.com/svg?repos=partitect/elephantine&type=Date)](https://star-history.com/#partitect/elephantine&Date)

</div>

---

<div align="center">

**Filler Asla Unutmaz. Yapay Zekâ Ajanlarınız da Unutmayacak.**

[Partitect](https://github.com/partitect) ve Açık Kaynak Topluluğu tarafından ❤️ ile inşa edilmiştir.

</div>
