<div align="center">

# ?? Elephantine

### *Filler Asla Unutmaz. Yapay Zeka Ajanlar?n?z da Unutmayacak.*

**Otonom Yapay Zeka Ajanlar? i?in GPU-Gerektirmeyen, Yerel-?ncelikli, CPU-Native Haf?za Katman?**

[![PyPI Version](https://img.shields.io/pypi/v/elephantine.svg?color=blue)](https://pypi.org/project/elephantine/)
[![CI & Quality Gate](https://github.com/partitect/elephantine/actions/workflows/ci.yml/badge.svg)](https://github.com/partitect/elephantine/actions/workflows/ci.yml)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-brightgreen.svg)](https://python.org)
[![MCP Ready](https://img.shields.io/badge/MCP-Protocol%20Ready-blueviolet.svg)](https://modelcontextprotocol.io/)
[![CPU Native](https://img.shields.io/badge/Hardware-100%25%20CPU%20Native-orange.svg)](#performans--k?yaslama-benchmarks)

<p align="center">
  <a href="#neden-elephantine">Neden Elephantine?</a> ?
  <a href="#mimari">Mimari</a> ?
  <a href="#h?zl?-ba?lang??">H?zl? Ba?lang??</a> ?
  <a href="#?oklu-ajan-ortak-?al??ma-alan?">?oklu Ajan Alan?</a> ?
  <a href="#webui-dashboard">Dashboard</a> ?
  <a href="#ide--ajan-kurulumu-mcp">Cursor, Codex & Claude</a> ?
  <a href="#python-sdk">Python SDK</a> ?
  <a href="#performans--k?yaslama-benchmarks">K?yaslamalar</a>
</p>

---

<br/>

<a href="#webui-dashboard">
  <img src="../docs/assets/dashboard_mockup.svg" alt="Elephantine Memory Inspector Dashboard" width="100%" />
</a>

<br/>

</div>

## ?? Felsefe

Efsaneye g?re filler, de?i?en ??l kumlar? aras?nda onlarca y?l ?nceki su kaynaklar?n? dahi hat?rlar. G?n?m?z yapay zeka ajanlar? ise ba?lam penceresi (context window) kapand??? anda t?m tercihlerinizi ve kararlar?n?z? unutur.

**Elephantine**, ajanlar?n?za kal?c?, sars?lmaz bir haf?za kazand?r?r. Standart CPU altyap?lar? (2 vCPU / 4 GB RAM) i?in s?f?rdan in?a edilen Elephantine, **s?f?r GPU** gerektirir, **harici API ?a?r?s? yapmaz** ve embedded LanceDB ile SQLite kullanarak **verilerinizin ana makineden asla d??ar? s?zmamas?n?** sa?lar.

---

## ? ?ne ??kan ?zellikler

- ?? **%100 CPU-Native ?al??ma**: AVX-512 SIMD thread optimizasyonlu ONNX Runtime ile 2 vCPU sunucularda 35ms alt? geri ?a??rma (recall) gecikmesi. CUDA veya PyTorch y?k? yok.
- ?? **Proje Bazl? ?zole Haf?za**: Cursor veya ?al??ma dizini a??ld???nda projenin Git reposunu otomatik tespit eden ve projeler aras? kural/ba?lam kar??mas?n? (workspace_id) engelleyen mekanizma.
- ?? **?oklu Ajan Ortak Haf?zas?**: Ajan ekipleri (Coder, Tester, Architect) aras?nda payla??ml? haf?za ve stajyer ajanlar?n k?demli mimari kararlar?n? ezmesini ?nleyen **Rol Tabanl? Otorite Konsens?s?** (
ole_authority).
- ?? **Dahili WebUI Inspector**: Canl? motor metriklerini, haf?za kay?tlar?n?, ?eli?ki ge?mi?ini ve bilgi grafi?ini g?steren ger?ek zamanl? web paneli (/dashboard).
- ?? **G?m?l? GGUF SLM ??kar?m?**: Harici LLM sunucusuna gerek kalmadan, g?m?l? llama-cpp-python (Qwen2.5-0.5B-Instruct) ile yerel yap?sal haf?za ??kar?m?.
- ?? **Grafik Bellek (Knowledge Graph)**: Hibrit arama hatt?na entegre, ?zne-y?klem-nesne semantik ili?kileri (/graph/query).
- ?? **Yerel-?ncelikli & S?f?r Veri S?z?nt?s?**: Embedded LanceDB (Arrow/C++) vekt?r deposu + SQLite WAL. Verileriniz asla diskinizden ayr?lmaz.
- ?? **Evrensel Ajan Deste?i (MCP & REST)**: **OpenAI Codex**, **Cursor Composer**, **GitHub Copilot**, **Windsurf** ve **Claude Desktop** ile tek t?kla do?rudan entegrasyon.

---

<a id="neden-elephantine"></a>
## ?? Neden Elephantine?

| ?zellik / Metrik | Bulut Bellek / Hosted RAG | Geleneksel Vekt?r DB | ?? **ELEPHANTINE** |
|---|---|---|---|
| **GPU Ba??ml?l???** | Zorunlu / Bulut fatural? | Genellikle gerekli | **S?f?r (%100 CPU Native)** |
| **Veri Gizlili?i** | 3. parti buluta s?zar | Bar?nd?r?lan sunucular | **%100 Ana Makinede Yerel (Embedded)** |
| **Bellek Boyutlar?** | Sadece anlamsal | Sadece vekt?r embedding | **Anlamsal + Prosed?rel + Grafik** |
| **?oklu Ajan Ekipleri**| Ayr?k silo havuzlar | Dahili konsens?s yok | **?al??ma Alan? Havuzu + Rol Otoritesi** |
| **So?uk Ba?lang?? RAM** | Bulut servisi | 1.5 GB - 4 GB+ | **< 400 MB** |
| **Geri ?a??rma Gecikmesi** | 120ms - 400ms (A?) | 50ms - 150ms | **~35ms (p50)** |
| **??letme Maliyeti** | Ajan ba??  - +/ay | ?zel sanal makine maliyeti | **.00 (Mevcut sunucuda ?al???r)** |
| **MCP Entegrasyonu** | Manuel API sarmalama | ?zel ba?lay?c? gerektirir | **Dahili 1-T?k (stdio / sse)** |

---

<a id="mimari"></a>
## ??? Mimari

<br/>

<div align="center">
  <img src="../docs/assets/architecture.png" alt="Elephantine Mimari ?emas?" width="100%" />
</div>

<br/>

---

<a id="h?zl?-ba?lang??"></a>
## ?? H?zl? Ba?lang?? (30 Saniye)

### Y?ntem A: pip ile Kurulum (?nerilen)
`ash
pip install elephantine

# Motor sunucusunu ve g?sterge panelini ba?lat?n
elephantine start --port 8765
`

Canl? haf?za denetleyicisini g?rmek i?in taray?c?n?zdan [http://localhost:8765/dashboard](http://localhost:8765/dashboard) adresine gidin!

---

<a id="?oklu-ajan-ortak-?al??ma-alan?"></a>
## ?? ?oklu Ajan Ortak ?al??ma Alan?

Farkl? ajanlar? hiyerar?ik yetki korumas?yla tek bir projede koordine edin:

`python
from elephantine.client import ElephantineClient

client = ElephantineClient("http://127.0.0.1:8765")

# 1. Ba? Mimar mimari karar? belirler (Otorite: 1.0)
client.remember(
    content="Veritaban? pgvector uzant?l? PostgreSQL 16 olmak zorundad?r.",
    category="architecture",
    entity_key="project:db_engine",
    workspace_id="proje-x",
    role_authority=1.0
)

# 2. Junior Geli?tirici veritaban?n? de?i?tirmeye ?al???r (Otorite: 0.3)
# -> Rol Otoritesi Konsens?s? taraf?ndan REDDED?L?R
client.remember(
    content="Basitlik olsun diye SQLite kullanal?m.",
    category="architecture",
    entity_key="project:db_engine",
    workspace_id="proje-x",
    role_authority=0.3
)
`

---

<a id="performans--k?yaslama-benchmarks"></a>
## ?? Performans & K?yaslamalar

Standart **Ubuntu 24.04 VDS (2 vCPU / 4 GB RAM, GPU Yok)** ?zerinde test edilmi?tir:

| Operasyon | Metrik | De?er |
|---|---|---|
| **Bo?ta RAM T?ketimi (RSS)** | Idle Bellek Ayak ?zi | **310 MB** |
| **Aktif ?al??ma Belle?i** | Y?k Alt?nda | **< 680 MB** |
| **CPU Vekt?r ??kar?m?** | Normalize 384 boyutlu vekt?r | **14.2 ms** |
| **Yo?un Vekt?r Arama** | LanceDB kosin?s benzerli?i | **9.1 ms** |
| **Seyrek BM25 Arama** | SQLite FTS5 indeksi | **3.2 ms** |
| **Hibrit /recall (p50)** | U?tan Uca Gecikme | **36.3 ms** |
| **Hibrit /recall (p95)** | U?tan Uca Gecikme | **42.8 ms** |

---

<div align="center">

**Filler Asla Unutmaz. Yapay Zeka Ajanlar?n?z da Unutmayacak.**

[Partitect](https://github.com/partitect) ve A??k Kaynak Toplulu?u taraf?ndan ?? ile in?a edilmi?tir.

</div>
