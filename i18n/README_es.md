<div align="center">

# 🐘 Elephantine

### *Los elefantes nunca olvidan. Tus agentes de IA tampoco.*

**Capa de memoria nativa de CPU, local primero y sin GPU para agentes autónomos de IA**

[![PyPI Version](https://img.shields.io/pypi/v/elephantine.svg?color=blue)](https://pypi.org/project/elephantine/)
[![CI & Quality Gate](https://github.com/partitect/elephantine/actions/workflows/ci.yml/badge.svg)](https://github.com/partitect/elephantine/actions/workflows/ci.yml)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](../LICENSE)
[![Python Version](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-brightgreen.svg)](https://python.org)
[![MCP Ready](https://img.shields.io/badge/MCP-Protocol%20Ready-blueviolet.svg)](https://modelcontextprotocol.io/)
[![CPU Native](https://img.shields.io/badge/Hardware-100%25%20CPU%20Native-orange.svg)](#rendimiento-y-benchmarks)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](#cómo-contribuir)

<p align="center">
  <a href="#por-qué-elephantine">¿Por qué Elephantine?</a> •
  <a href="#arquitectura">Arquitectura</a> •
  <a href="#inicio-rápido">Inicio Rápido</a> •
  <a href="#espacio-de-trabajo-multi-agente">Espacio Multi-Agente</a> •
  <a href="#panel-webui-dashboard">Dashboard</a> •
  <a href="#configuración-mcp-cursor-codex-y-claude">Cursor, Codex & Claude</a> •
  <a href="#python-sdk-e-integración-con-langchain">Python SDK</a> •
  <a href="#rendimiento-y-benchmarks">Benchmarks</a>
</p>

<p align="center">
  <b>Idiomas / Translations:</b>
  <a href="../README.md">English</a> |
  <a href="README_tr.md">Türkçe</a> |
  <a href="README_zh.md">简体中文</a> |
  <a href="README_es.md">Español</a> |
  <a href="README_ja.md">日本語</a>
</p>

---

<br/>

<a href="#panel-webui-dashboard">
  <img src="../docs/assets/dashboard_mockup.svg" alt="Elephantine Memory Inspector Dashboard" width="100%" />
</a>

<br/>

</div>

## 🐘 Filosofía

La leyenda cuenta que los elefantes recuerdan los pozos de agua a través de décadas de arenas cambiantes en el desierto. Los agentes de IA modernos, en cambio, olvidan tus preferencias en el instante en que su ventana de contexto (context window) se cierra.

**Elephantine** otorga a tus agentes una memoria permanente e inquebrantable. Diseñado desde cero para CPUs estándar (2 vCPU / 4 GB RAM), Elephantine requiere **cero GPUs**, realiza **cero llamadas a APIs externas** y garantiza **cero fugas de datos** almacenando todo directamente en el disco local mediante LanceDB y SQLite embebidos.

---

## ⚡ Características Principales

- 🏎 **Ejecución 100% Nativa en CPU**: Latencia de recuperación (recall) inferior a 35ms en servidores de 2 vCPU gracias a ONNX Runtime y optimización AVX-512 SIMD. Sin CUDA ni el peso de PyTorch.
- 👥 **Espacio de Trabajo Multi-Agente Compartido**: Agrupación fluida de memoria (`workspace_id`) entre equipos (Desarrollador, Tester, Arquitecto) con **Consenso de Autoridad Basado en Roles** (`role_authority`) que impide que agentes junior sobrescriban decisiones arquitectónicas críticas.
- 📊 **Panel WebUI Integrado**: Panel de control interactivo en tiempo real (`/dashboard`) que muestra métricas del motor, registros de memoria, historial de conflictos y grafos de conocimiento.
- 🦙 **Extracción GGUF SLM en Proceso**: Extracción estructurada de memoria mediante `llama-cpp-python` (`Qwen2.5-0.5B-Instruct`) local, sin necesidad de servidores LLM externos.
- 🕸 **Memoria en Grafo y Tripletas de Conocimiento**: Grafos semánticos nativos sujeto-predicado-objeto (`/graph/query`) integrados directamente en el flujo de recuperación híbrida.
- 🔒 **Local Primero y Cero Fugas**: Base vectorial LanceDB (Arrow/C++) embebida + SQLite WAL. Tus datos nunca abandonan tu máquina anfitriona.
- 🔌 **Compatibilidad Universal con Agentes (MCP & REST)**: Conexión nativa con **OpenAI Codex**, **Cursor Composer**, **GitHub Copilot**, **Windsurf** y **Claude Desktop** sin fricción de configuración.

---

<a id="por-qué-elephantine"></a>
## ⚖️ ¿Por qué Elephantine?

| Característica / Métrica | Memoria en la Nube / RAG | Bases Vectoriales Tradicionales | 🐘 **ELEPHANTINE** |
|---|---|---|---|
| **Dependencia de GPU** | Obligatoria / Costo en la nube | Frecuentemente requerida | **Cero (100% Nativo en CPU)** |
| **Privacidad de Datos** | Fuga a servicios de terceros | Servidores dedicados | **100% Local en Máquina (Embebido)** |
| **Dimensiones de Memoria** | Solo semántica | Solo embeddings vectoriales | **Semántica + Procedimental + Grafo** |
| **Equipos Multi-Agente** | Silos aislados | Sin consenso nativo | **Fondo Compartido + Autoridad de Rol** |
| **RAM en Arranque Frío** | N/A (Servicio externo) | 1.5 GB - 4 GB+ | **< 400 MB** |
| **Latencia de Recall (CPU)** | 120ms - 400ms (Red) | 50ms - 150ms | **~35ms (p50)** |
| **Costo Operativo** | $20 - $200+/mes por agente | Costos de VM dedicada | **$0.00 (Ejecuta en tu servidor actual)** |
| **Integración MCP** | Código pegamento manual | Wrappers personalizados | **Nativo en 1 clic (stdio / sse)** |

---

<a id="arquitectura"></a>
## 🏗️ Arquitectura

<br/>

<div align="center">
  <img src="../docs/assets/architecture.png" alt="Arquitectura de Elephantine - Infraestructura de Memoria para IA Nativa en CPU" width="100%" />
</div>

<br/>

---

<a id="inicio-rápido"></a>
## 🚀 Inicio Rápido (30 Segundos)

### Opción A: Instalación vía pip (Recomendado)
```bash
pip install elephantine

# Inicia el motor y el panel de control
elephantine start --port 8765
```

### Opción B: Desde el Código Fuente (Para Contribuidores)
```bash
# 1. Clona el repositorio
git clone https://github.com/partitect/elephantine.git
cd elephantine

# 2. Configura el entorno virtual con uv
uv venv .venv
# Windows: .venv\Scripts\activate | Linux/macOS: source .venv/bin/activate
uv pip install -e ".[dev]"

# 3. Inicia el motor y el panel
elephantine start --port 8765
```

¡Abre tu navegador en [http://localhost:8765/dashboard](http://localhost:8765/dashboard) para ver el Inspector de Memoria en vivo!

---

<a id="espacio-de-trabajo-multi-agente"></a>
## 👥 Espacio de Trabajo Multi-Agente Compartido

Coordina equipos de agentes (ej. Desarrollador, Tester, Arquitecto) con fondos de memoria persistentes y protección jerárquica de autoridad:

```python
from elephantine.client import ElephantineClient

# Conectar al demonio local de Elephantine
client = ElephantineClient("http://127.0.0.1:8765")

# 1. El Arquitecto Líder define la base técnica (Autoridad: 1.0)
client.remember(
    content="La base de datos debe ser estrictamente PostgreSQL 16 con la extensión pgvector.",
    category="architecture",
    entity_key="project:db_engine",
    workspace_id="phoenix-core",
    role_authority=1.0
)

# 2. El Agente Junior intenta cambiar la base de datos (Autoridad: 0.3)
# -> RECHAZADO por el Consenso de Autoridad de Roles (protegido contra menor autoridad)
client.remember(
    content="Cambiemos la base de datos a SQLite para mayor simplicidad.",
    category="architecture",
    entity_key="project:db_engine",
    workspace_id="phoenix-core",
    role_authority=0.3
)

# 3. El Agente Tester recupera las memorias del espacio (Reordenamiento ponderado por autoridad)
results = client.recall(
    query="¿Qué motor de base de datos estamos usando?",
    workspace_id="phoenix-core"
)

# Se garantiza que PostgreSQL 16 permanece intacto:
# [architecture] (Autoridad: 1.0) -> La base de datos debe ser estrictamente PostgreSQL 16...
```

---

<a id="panel-webui-dashboard"></a>
## 🖥️ Panel WebUI (Dashboard)

Elephantine incluye un Inspector de Memoria integrado y ligero disponible en `http://localhost:8765/dashboard`:

- **Registro de Memoria en Tiempo Real**: Inspecciona memorias activas y obsoletas (deprecated), revisa números de versión y estados sustituidos.
- **Seguimiento de Autoridad y Conflictos**: Monitorea modificaciones basadas en roles y cadenas de obsolescencia LWW (Last-Write-Wins).
- **Visor de Grafos de Conocimiento**: Explora relaciones tripletas sujeto-predicado-objeto extraídas.
- **Búsqueda y Filtrado en Vivo**: Prueba búsquedas híbridas densas + BM25 de manera interactiva.

---

<a id="configuración-mcp-cursor-codex-y-claude"></a>
## 🔌 Configuración en Cursor, OpenAI Codex y Claude Desktop

Elephantine se conecta a los principales IDEs y clientes de escritorio de IA a través del protocolo nativo **Model Context Protocol (MCP)** y endpoints REST locales de alta velocidad.

### 1. OpenAI Codex & GitHub Copilot (VS Code)
Para flujos de trabajo de agentes en VS Code y entornos basados en Codex:
1. Ejecuta `elephantine config-codex` para ver la configuración lista para copiar.
2. En tu archivo `.vscode/settings.json` (o configuración MCP):
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
*O llama directamente a la API REST local desde tus scripts en `http://127.0.0.1:8765/recall`.*

### 2. Configuración en Cursor
1. Abre **Cursor Settings** -> **Features** -> **MCP Servers** -> **Add New MCP Server**.
2. Completa:
   - **Name**: `elephantine`
   - **Type**: `command`
   - **Command**: `elephantine mcp`

### 3. Configuración en Claude Desktop
Ejecuta `elephantine config-claude` o añade esto a tu archivo `claude_desktop_config.json`:

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

<a id="python-sdk-e-integración-con-langchain"></a>
## 💻 Python SDK e Integración con LangChain

Elephantine ofrece clientes síncronos y asíncronos junto con un adaptador de memoria para LangChain:

```python
import asyncio
from elephantine.client import AsyncElephantineClient, ElephantineLangChainMemory

async def main():
    async with AsyncElephantineClient("http://127.0.0.1:8765") as client:
        # Recordar con alineación de entidad semántica
        await client.remember(
            content="El usuario prefiere pytest con ejecutores de pruebas asíncronos.",
            category="preference",
            entity_key="dev:test_runner",
            workspace_id="dev-team",
            role_authority=0.8
        )

        # Recuperar memorias con decaimiento temporal y filtrado por espacio
        res = await client.recall(
            query="preferencias de ejecutor de pruebas",
            workspace_id="dev-team",
            top_k=3
        )
        print("Recuperado:", res)

    # Adaptador de Memoria para LangChain
    chain_memory = ElephantineLangChainMemory(
        base_url="http://127.0.0.1:8765",
        workspace_id="dev-team"
    )
    chain_memory.save_context({"input": "Hola"}, {"output": "¡Recuerdo tus preferencias!"})

if __name__ == "__main__":
    asyncio.run(main())
```

---

<a id="rendimiento-y-benchmarks"></a>
## 📈 Rendimiento y Benchmarks

Probado en un servidor estándar **Ubuntu 24.04 VDS (2 vCPU / 4 GB RAM, Sin GPU)**:

| Operación | Métrica | Valor |
|---|---|---|
| **Memoria RSS en Arranque Frío** | Huella de Memoria en Reposo | **310 MB** |
| **Conjunto de Trabajo Total** | Bajo Carga Activa | **< 680 MB** |
| **Inferencia de Embeddings (CPU)** | Vector normalizado de 384 dimensiones | **14.2 ms** |
| **Búsqueda Vectorial Densa** | Similitud de coseno en LanceDB | **9.1 ms** |
| **Búsqueda Dispersa BM25** | Índice SQLite FTS5 | **3.2 ms** |
| **`/recall` Híbrido (p50)** | Latencia Extremo a Extremo | **36.3 ms** |
| **`/recall` Híbrido (p95)** | Latencia Extremo a Extremo | **42.8 ms** |

---

## 🗺️ Hoja de Ruta (Roadmap)

- [x] **v0.1.0**: MVP del Núcleo Comunitario (LanceDB + SQLite WAL + ONNX Runtime).
- [x] **v0.1.1**: Validador de Anclaje de Alucinaciones y Verificación de Esquemas Pydantic.
- [x] **v0.1.2**: Servidor FastMCP nativo stdio/SSE para Cursor y Claude Desktop.
- [x] **v0.2.0**: Extracción GGUF SLM embebida (`Qwen2.5-0.5B-Instruct` vía llama.cpp).
- [x] **v0.2.5**: Memoria en Grafo y Extracción de Tripletas (`/graph/query`).
- [x] **v0.3.0**: Inspector de Memoria WebUI ligero y Visualizador de Grafos con Viaje Temporal.
- [x] **v0.3.5**: Espacio de Trabajo Multi-Agente y Consenso de Autoridad Basado en Roles (`workspace_id`, `role_authority`).
- [ ] **v1.0.0**: RBAC Empresarial Multi-Tenant y Consenso Distribuido CRDT.

---

<a id="cómo-contribuir"></a>
## 🤝 Cómo Contribuir

¡Aceptamos con entusiasmo contribuciones de ingenieros de sistemas, investigadores de IA y desarrolladores de agentes!

```bash
git clone https://github.com/partitect/elephantine.git
cd elephantine
uv venv .venv
uv pip install -e ".[dev]"
pytest -v tests/
```

---

## 🌟 Historial de Estrellas

<div align="center">

[![Star History Chart](https://api.star-history.com/svg?repos=partitect/elephantine&type=Date)](https://star-history.com/#partitect/elephantine&Date)

</div>

---

<div align="center">

**Los elefantes nunca olvidan. Tus agentes de IA tampoco.**

Construido con ❤️ por [Partitect](https://github.com/partitect) y la Comunidad de Código Abierto.

</div>
