<p align="center">
  <img src="../docs/assets/elephantine_banner.png" alt="ELEPHANTINE: Remember - Recall - Answer" width="100%" />
</p>

<div align="center">

# 🐘 Elephantine

### *Filler Asla Unutmaz. Yapay Zekâ Ajanlarınız da Unutmayacak.*

**Otonom Yapay Zekâ Ajanları için Sıfır-GPU, Yerel-Öncelikli, CPU-Native Hafıza Katmanı**

[![PyPI Version](https://img.shields.io/pypi/v/elephantine.svg?color=blue)](https://pypi.org/project/elephantine/)
[![CI & Quality Gate](https://github.com/partitect/elephantine/actions/workflows/ci.yml/badge.svg)](https://github.com/partitect/elephantine/actions/workflows/ci.yml)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](../LICENSE)
[![Python Version](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.13-brightgreen.svg)](https://python.org)
[![MCP Ready](https://img.shields.io/badge/MCP-Protocol%20Ready-blueviolet.svg)](https://modelcontextprotocol.io/)
[![CPU Native](https://img.shields.io/badge/Hardware-100%25%20CPU%20Native-orange.svg)](#performans--kıyaslama-benchmarks)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](#katkıda-bulunma)

<p align="center">
  <a href="#neden-elephantine">Neden Elephantine?</a> •
  <a href="#mimari">Mimari</a> •
  <a href="#hızlı-başlangıç">Hızlı Başlangıç</a> •
  <a href="#çoklu-ajan-ortak-çalışma-alanı">Çoklu Ajan Alanı</a> •
  <a href="#webui-kontrol-paneli--bilgi-grafiği">Dashboard & Grafik</a> •
  <a href="#tek-tıkla-ide--ajan-kurulumu-mcp">1-Tıkla IDE Kurulumu</a> •
  <a href="#terminal-cli-komutları">Terminal CLI</a> •
  <a href="#sdks--entegrasyonlar">SDK'lar (Python & TS)</a> •
  <a href="#kurumsal-rbac--güvenlik">Kurumsal RBAC</a> •
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

</div>

## 🐘 Felsefe

Efsaneye göre filler, değişen çöl kumları arasında onlarca yıl önceki su kaynaklarını dahi hatırlar. Günümüz yapay zekâ ajanları ise bağlam penceresi (context window) kapandığı anda tüm tercihlerinizi ve kararlarınızı unutur.

**Elephantine**, ajanlarınıza kalıcı, sarsılmaz bir hafıza kazandırır. Standart CPU altyapıları (2 vCPU / 4 GB RAM) için sıfırdan inşa edilen Elephantine, **sıfır GPU** gerektirir, **harici API çağrısı yapmaz** ve embedded LanceDB ile SQLite kullanarak **verilerinizin ana makineden asla dışarı sızmamasını** sağlar.

---

## ⚡ Öne Çıkan Özellikler

- 🏎 **%100 CPU-Native Çalışma**: AVX-512 SIMD thread optimizasyonlu ONNX Runtime ile 2 vCPU sunucularda 35ms altı geri çağırma (recall) gecikmesi. CUDA veya PyTorch yükü yok.
- 👥 **Çoklu Ajan Ortak Çalışma Alanı**: Ekipler (Coder, Tester, Architect) arasında paylaşımlı hafıza havuzu (`workspace_id`) ve stajyer/küçük ajanların kıdemli mimari kararları ezmesini önleyen **Rol Tabanlı Otorite Konsensüsü** (`role_authority`).
- 📊 **Dahili WebUI Inspector & Bilgi Grafiği**: Canlı motor metriklerini, hafıza defterini ve **Cytoscape.js interaktif bilgi grafiğini** gösteren gerçek zamanlı web paneli (`/dashboard`).
- 🦙 **Gömülü GGUF SLM Çıkarımı**: Harici LLM sunucusuna gerek kalmadan, gömülü `llama-cpp-python` (`Qwen2.5-0.5B-Instruct`) ile yerel yapısal hafıza çıkarımı.
- 🕸 **Grafik Bellek (Knowledge Graph)**: Hibrit arama hattına entegre, özne-yüklem-nesne semantik ilişkileri (`/graph/query`).
- ⚙️ **Prosedürel Bellek & İş Akışı Takibi**: Araç çalıştırma geçmişlerini ve öğrenilen çok adımlı prosedürleri kaydeder (`/procedural/track`).
- 🔒 **Yerel-Öncelikli & Sıfır Veri Sızıntısı**: Embedded LanceDB (Arrow/C++) vektör deposu + SQLite WAL. Verileriniz asla diskinizden ayrılmaz.
- 🔌 **Evrensel Ajan Desteği (MCP & REST)**: **Google Antigravity**, **OpenAI Codex**, **Cursor Composer**, **GitHub Copilot**, **Windsurf** ve **Claude Desktop** ile tek komutla otomatik CLI kurulumu.
- 🛡️ **Kurumsal RBAC & Güvenlik**: Esnek `RoleBasedAuthEngine` ile ayrıntılı rol izinleri (`admin`, `architect`, `editor`, `viewer`) ve API Key / Bearer token doğrulaması.

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
## 🚀 Hızlı Başlangıç & CLI Kurulumu

### 1. Elephantine CLI'yi Yükleyin

Elephantine'i tercih ettiğiniz Python paket yöneticisiyle kurduğunuzda, `elephantine` komutu terminalinizde otomatik olarak küresel kullanıma hazır hale gelir:

```bash
# Önerilen: pipx ile bağımsız küresel CLI kurulumu
pipx install elephantine

# Veya uv ile
uv tool install elephantine

# Veya standart pip ile
pip install elephantine
```

> [!TIP]
> Kurulum tamamlandıktan sonra tüm komutlara (`elephantine start`, `elephantine install-antigravity`, `elephantine remember` vb.) doğrudan terminalinizden erişebilirsiniz. Terminal ortam değişkenlerinizde (PATH) bir sorun olursa komutları alternatif olarak `python -m elephantine.cli <komut>` şeklinde de çalıştırabilirsiniz.

### 2. Motor Sunucusunu ve Web Panelini Başlatın
```bash
elephantine start --port 8765
```
Canlı Hafıza Müfettişini görüntülemek için tarayıcınızda [http://localhost:8765/dashboard](http://localhost:8765/dashboard) adresini açın!

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

---

<a id="tek-tıkla-ide--ajan-kurulumu-mcp"></a>
## 🔌 Tek Tıkla IDE & Ajan Kurulumu (MCP)

Elephantine, yerel **Model Context Protocol (MCP)** ve yüksek hızlı REST uç noktalarıyla tüm büyük ortamlara bağlanır.

### ⚡ 1 Saniyede Otomatik CLI Kurulumu
`elephantine` CLI kurulu olduğunda, elle JSON yapılandırması aramadan tek bir komutla favori ortamınıza kurulum yapabilirsiniz:


```bash
# Google Antigravity (AGY)
elephantine install-antigravity

# OpenAI Codex & GitHub Copilot
elephantine install-codex

# Cursor Composer & Editör
elephantine install-cursor

# Claude Desktop
elephantine install-claude

# VS Code Çalışma Alanı (.vscode/settings.json)
elephantine install-vscode
```

### Manuel Yapılandırma Görüntüleme
İstediğiniz zaman hazır kopyalanabilir ayarları görüntüleyebilirsiniz:
```bash
elephantine config-antigravity
elephantine config-codex
elephantine config-cursor
elephantine config-claude
```

---

<a id="terminal-cli-komutları"></a>
## 💻 Doğrudan Terminal CLI Komutları

Kod yazmadan veya web arayüzünü açmadan terminalden doğrudan bellek ekleyin ve arayın:

```bash
# 1. Belirli bir çalışma alanı ve otorite ile bellek kaydetme
elephantine remember "PostgreSQL 16 veritabanı pgvector uzantısıyla kullanılmalıdır." \
  --workspace phoenix-core \
  --category architecture \
  --authority 1.0

# 2. Hibrit yoğun + BM25 araması ile çağırma
elephantine recall "hangi veritabanını kullanıyoruz?" \
  --workspace phoenix-core \
  --top-k 3
```

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

<a id="webui-kontrol-paneli--bilgi-grafiği"></a>
## 🖥️ WebUI Kontrol Paneli & İnteraktif Bilgi Grafiği

Elephantine, `http://localhost:8765/dashboard` adresinde çalışan yerleşik bir Hafıza Müfettişi içerir:

- **Gerçek Zamanlı Bellek Defteri**: Aktif ve kullanımdan kaldırılmış (deprecated) kayıtları, revizyon sayılarını inceleyin.
- **🕸 İnteraktif Bilgi Grafiği (Cytoscape.js)**: Çıkarılan semantik varlıkları ve özne-yüklem-nesne üçlülerini kuvvet odaklı (CoSE), dairesel ve eşmerkezli ağlar halinde canlı gezin.
- **Canlı İnceleme**: Herhangi bir düğüme veya ilişki okuna tıklayarak güven skorunu, kaynak bellek ayrıntılarını canlı görüntüleyin.
- **Otorite ve Çelişki Takibi**: Rol tabanlı değişiklikleri ve LWW (Son-Yazan-Kazanır) zincirlerini izleyin.

---

<a id="sdks--entegrasyonlar"></a>
## 💻 SDK'lar & Entegrasyonlar

### 1. Python SDK & LangChain Entegrasyonu
```python
import asyncio
from elephantine.client import AsyncElephantineClient, ElephantineLangChainMemory

async def main():
    async with AsyncElephantineClient("http://127.0.0.1:8765") as client:
        await client.remember(
            content="Kullanıcı asenkron test çalıştırıcıları ile pytest tercih ediyor.",
            category="preference",
            entity_key="dev:test_runner",
            workspace_id="dev-team",
            role_authority=0.8
        )

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

### 2. TypeScript / Node.js SDK (`@elephantine/sdk`)
`sdks/typescript/` dizininde hazır bulunmaktadır:

```typescript
import { ElephantineClient } from '@elephantine/sdk';

const client = new ElephantineClient('http://127.0.0.1:8765');

// Belleğe kaydetme
await client.remember({
  content: 'Canlı dağıtımlar Salı günleri saat 10:00 UTC yapılacaktır.',
  category: 'devops',
  workspaceId: 'infra-team',
  roleAuthority: 0.9
});

// Bellekten çağırma
const res = await client.recall({
  query: 'dağıtım takvimi',
  workspaceId: 'infra-team'
});
console.log(res.memories);
```

---

<a id="kurumsal-rbac--güvenlik"></a>
## 🛡️ Kurumsal RBAC & Güvenlik

Çok kullanıcılı ekipler ve kurumsal ortamlar için modüler Rol Tabanlı Erişim Kontrolü:

* **Tanımlı Roller**:
  - `admin`: Tam sınırsız erişim (`read`, `write`, `delete`, `admin`).
  - `architect`: Tüm kategorilerde okuma, yazma ve silme.
  - `editor`: Bellek okuma ve yazma.
  - `viewer`: Salt-okunur (read-only) çağırma erişimi. Yazma ve silme denemeleri HTTP 403 Forbidden ile engellenir.
* **Token Kimlik Doğrulaması**:
  - `ELEPHANTINE_AUTH_ENABLED=true` ile aktif edilir.
  - İstekler `X-API-Key: <key>` veya `Authorization: Bearer <key>` başlığıyla doğrulanır.
  - Varsayılan Topluluk modu (`AUTH_ENABLED=false`) sıfır konfigürasyon ile tam yerel hızda çalışır.

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
- [x] **v0.3.8**: 1-Tıkla IDE Kurulumu (Antigravity, Codex, Cursor, Claude, VS Code) & Cytoscape.js İnteraktif Grafik.
- [x] **v0.4.0**: TypeScript / Node.js SDK & Kurumsal RBAC Güvenlik Katmanı.
- [ ] **v1.0.0**: Ajanlar Arası CRDT Dağıtık Konsensüsü & Çok Düğümlü Senkronizasyon.

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

<a id="kurumsal-ve-bulut-destegi"></a>
## 💼 Kurumsal, Bulut ve Ticari Destek

Otonom yapay zekâ ajanları inşa ediyor ve gizlilik odaklı, kurumsal seviyede bir hafıza katmanı mı arıyorsunuz?

| Paket / Hizmet | Hedef Kitle | Özellikler | İletişim |
|---|---|---|---|
| **Community Edition** | Geliştiriciler | Apache 2.0 açık kaynak, %100 yerel ve harici bağımlılıksız | [Dokümantasyon](#hızlı-başlangıç--cli-kurulumu) |
| **Elephantine Cloud** | Uzaktan Çalışan Ekipler | Cihazlar arası hafıza senkronizasyonu, yönetilen API, otomatik yedekleme | [Bulut Bekleme Listesine Katıl](mailto:contact@partitect.com?subject=Elephantine%20Cloud%20Waitlist) |
| **Enterprise Edition** | Kurumlar, Sağlık, Finans, Savunma | Şirket içi (On-Premise) kurulum, SOC2/KVKK uyum raporları, SAML/SSO, Özel SLA | [Kurumsal İletişim](mailto:contact@partitect.com?subject=Elephantine%20Kurumsal%20Talep) |
| **Özel Ajan Danışmanlığı** | Yazılım & AI Ajansları | Özel Bilgi Grafiği (Knowledge Graph) çıkarma, dahili sistem entegrasyonu | [Mimari Görüşmesi Planla](mailto:contact@partitect.com?subject=Elephantine%20Mimari%20Danismanlik) |

> [!TIP]
> **Özel bir SLA, kurumunuza özel hafıza modeli veya on-premise kurulum desteği mi gerekiyor?**  
> Mühendislik ekibimizle doğrudan iletişime geçin: [contact@partitect.com](mailto:contact@partitect.com).

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
