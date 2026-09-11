<div align="center">

# ?? Elephantine

### *Los elefantes nunca olvidan. Tus agentes de IA tampoco.*

**Capa de memoria nativa de CPU, local primero y sin GPU para agentes aut?nomos de IA**

[![PyPI Version](https://img.shields.io/pypi/v/elephantine.svg?color=blue)](https://pypi.org/project/elephantine/)
[![CI & Quality Gate](https://github.com/partitect/elephantine/actions/workflows/ci.yml/badge.svg)](https://github.com/partitect/elephantine/actions/workflows/ci.yml)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-brightgreen.svg)](https://python.org)
[![MCP Ready](https://img.shields.io/badge/MCP-Protocol%20Ready-blueviolet.svg)](https://modelcontextprotocol.io/)
[![CPU Native](https://img.shields.io/badge/Hardware-100%25%20CPU%20Native-orange.svg)](#rendimiento-y-benchmarks)

<p align="center">
  <a href="#por-qu?-elephantine">?Por qu? Elephantine?</a> ?
  <a href="#arquitectura">Arquitectura</a> ?
  <a href="#inicio-r?pido">Inicio R?pido</a> ?
  <a href="#espacio-de-trabajo-multi-agente">Espacio Multi-Agente</a> ?
  <a href="#panel-webui">Panel WebUI</a> ?
  <a href="#configuraci?n-mcp-cursor-y-claude">Configuraci?n MCP</a> ?
  <a href="#python-sdk">Python SDK</a> ?
  <a href="#rendimiento-y-benchmarks">Benchmarks</a>
</p>

---

<br/>

<a href="#panel-webui">
  <img src="../docs/assets/dashboard_mockup.svg" alt="Elephantine Memory Inspector Dashboard" width="100%" />
</a>

<br/>

</div>

## ?? Filosof?a

La leyenda dice que los elefantes recuerdan los pozos de agua a trav?s de d?cadas de arenas cambiantes. Los agentes de IA modernos, en cambio, olvidan tus preferencias en el momento en que su ventana de contexto se cierra.

**Elephantine** otorga a tus agentes una memoria permanente e inquebrantable. Dise?ado desde cero para CPUs est?ndar (2 vCPU / 4 GB RAM), Elephantine requiere **cero GPUs**, realiza **cero llamadas a APIs externas** y garantiza **cero fugas de datos** almacenando todo directamente en el disco local mediante LanceDB y SQLite integrados.

---

## ? Caracter?sticas Principales

- ?? **Ejecuci?n 100% Nativa en CPU**: Latencia de recuperaci?n inferior a 35ms en servidores de 2 vCPU con ONNX Runtime y AVX-512 SIMD. Sin PyTorch ni CUDA.
- ?? **Memoria Aislada por Proyecto**: Detecci?n autom?tica del repositorio Git o directorio de trabajo (workspace_id), evitando la contaminaci?n de contexto entre proyectos.
- ?? **Espacio Compartido Multi-Agente**: Memoria compartida entre equipos de agentes (Desarrollador, Tester, Arquitecto) con **Consenso de Autoridad Basado en Roles** (
ole_authority).
- ?? **Panel WebUI Integrado**: Panel interactivo en tiempo real (/dashboard) para monitorizar m?tricas clave, registros de memoria y grafos de conocimiento.
- ?? **Extracci?n GGUF SLM en Proceso**: Extracci?n estructurada de memoria mediante llama-cpp-python (Qwen2.5-0.5B-Instruct) local.
- ?? **Grafo de Conocimiento Integrado**: Tripletas sem?nticas sujeto-predicado-objeto (/graph/query) incorporadas en la b?squeda h?brida.
- ?? **Local Primero & M?xima Privacidad**: Los datos nunca abandonan tu m?quina anfitriona.
- ?? **Compatibilidad Universal (MCP & REST)**: Conexi?n nativa con **Cursor**, **OpenAI Codex**, **GitHub Copilot** y **Claude Desktop**.

---

<a id="inicio-r?pido"></a>
## ?? Inicio R?pido (30 Segundos)

`ash
pip install elephantine

# Iniciar servidor y panel de control
elephantine start --port 8765
`

Abre tu navegador en [http://localhost:8765/dashboard](http://localhost:8765/dashboard) para inspeccionar la memoria en vivo.

---

<a id="rendimiento-y-benchmarks"></a>
## ?? Rendimiento y Benchmarks

Probado en un servidor est?ndar **Ubuntu 24.04 VDS (2 vCPU / 4 GB RAM, Sin GPU)**:

| Operaci?n | M?trica | Valor |
|---|---|---|
| **Consumo de Memoria en Reposo (RSS)** | Idle Memory Footprint | **310 MB** |
| **Conjunto Activo de Trabajo** | Bajo carga activa | **< 680 MB** |
| **Inferencia de Vectores (CPU)** | Vector normalizado de 384 dim | **14.2 ms** |
| **B?squeda Vectorial Densa** | Similitud de coseno en LanceDB | **9.1 ms** |
| **B?squeda Dispersa BM25** | ?ndice SQLite FTS5 | **3.2 ms** |
| **Recuperaci?n H?brida /recall (p50)** | Latencia extremo a extremo | **36.3 ms** |
| **Recuperaci?n H?brida /recall (p95)** | Latencia extremo a extremo | **42.8 ms** |

---

<div align="center">

**Los elefantes nunca olvidan. Tus agentes de IA tampoco.**

Construido con ?? por [Partitect](https://github.com/partitect) y la comunidad de c?digo abierto.

</div>
