<div align="center">

# TechDocs-LLMOps

**Enterprise-grade local RAG** for technical manuals — full PDF pipeline, **CPU embeddings**, **persistent Chroma**, **Ollama** generation, and a **production-style FastAPI** surface with OpenAPI, health probes, and **auditable source citations**.

[![Python](https://img.shields.io/badge/python-3.10%2B-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109%2B-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![LangChain](https://img.shields.io/badge/LangChain-RAG-121212?style=flat)](https://www.langchain.com/)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-persistent-FF6B35?style=flat)](https://www.trychroma.com/)
[![Ollama](https://img.shields.io/badge/Ollama-local_LLM-000000?style=flat&logo=ollama&logoColor=white)](https://ollama.com/)

[Repository](https://github.com/momo-s15/techdocs-llmops) · [Quick start](#quick-start-windows) · [API](#api) · [Architecture](#architecture)

</div>

---

## Highlights

- **Sovereign AI path**: dense manuals stay on-box — **no cloud LLM or embedding API** in the default stack.
- **End-to-end LLMOps slice**: batch **ingest CLI**, durable **vector index**, online **`/v1/ask`** with **`answer` + `sources`**, optional **reindex API** behind a feature flag.
- **Operator-ready**: structured logging, **`/health`** + **`/health/ollama`**, typed config via **Pydantic Settings**, Windows-first scripts.
- **Quality bar**: **pytest** suite with **`FakeEmbeddings`** so automated runs stay fast without sacrificing real-code paths.

---

## Table of contents

- [What you get](#what-you-get)
- [Architecture](#architecture)
- [Stack](#stack)
- [Skills this project demonstrates](#skills-this-project-demonstrates-for-recruiters--hiring-managers)
- [Quick start (Windows)](#quick-start-windows)
- [Sample API response](#sample-api-response)
- [Alternative: helper scripts](#alternative-helper-scripts)
- [Health checks](#health-checks)
- [API](#api)
- [Configuration](#configuration)
- [Air-gap and privacy](#air-gap-and-privacy)
- [Tests](#tests)
- [Project layout](#project-layout)

---

## What you get

| Capability | Detail |
|------------|--------|
| **PDF ingestion** | LangChain `PyPDFLoader` + `RecursiveCharacterTextSplitter`; CLI at `scripts/ingest.py` with optional collection reset |
| **Embeddings** | HuggingFace **sentence-transformers** on **CPU** — enterprise-friendly, no per-token embedding bills |
| **Vector store** | **ChromaDB** with **on-disk** persistence (`CHROMA_PERSIST_DIR`) |
| **Generation** | **langchain-ollama** `ChatOllama` with retrieval-augmented prompts and **grounded answers** plus **ranked sources** |
| **API** | **FastAPI**: `GET /`, **OpenAPI** docs, `POST /v1/ask`, opt-in `POST /v1/reindex` |
| **Operations** | Structured logging, **`/health`** and **`/health/ollama`**, structured JSON diagnostics for the serving path |
| **Quality** | **pytest** + **`TECHDOCS_TESTING`** + **`FakeEmbeddings`** for rapid CI-style feedback |

---

## Architecture

End-to-end flow — reference diagram in the repository root, rendered at full README width on GitHub.

<div align="center">
  <img src="architecture-diagram.png" alt="Architecture diagram: PDF manuals → ingest → CPU embeddings → Chroma on disk → FastAPI /v1/ask → Ollama" width="100%" />
</div>

**Full stack runs locally** — embeddings, retrieval, and generation stay under your control.

---

## Stack

| Layer | Technology |
|-------|------------|
| Runtime | Python 3.10+ |
| Web | FastAPI, Uvicorn, Pydantic v2, pydantic-settings |
| RAG | LangChain (community, Chroma, Ollama, text-splitters, core) |
| Vectors | ChromaDB |
| Embeddings | sentence-transformers |
| Documents | pypdf |
| Local LLM | Ollama (langchain-ollama / httpx) |
| Tests | pytest, pytest-asyncio |

---

## Skills this project demonstrates (for recruiters & hiring managers)

- **LLM application design**: classic **RAG** (retrieve → augment → generate), configurable top‑k, **grounded** system prompts, **structured responses** with **source excerpts** for traceability.
- **LLMOps patterns**: clean split between **batch ingestion** and **online serving**, durable embeddings store, **health endpoints**, **environment-driven** configuration.
- **Security & privacy posture**: **local inference** by default, **air-gap–friendly** artifact layout, **no secrets in git** (`.env` ignored; `.env.example` documents knobs only).
- **API craftsmanship**: **OpenAPI** out of the box, **typed** request/response models, **feature-flagged** reindex for controlled operations.
- **Software engineering**: **`src/`** layout, **settings** abstraction, **automated tests** with doubles for embeddings, PowerShell **dev ergonomics**.

---

## Quick start (Windows)

From the project root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
copy .env.example .env
```

Place PDF manuals under `data\manuals\` (only `*.pdf` are ingested).

```powershell
python scripts\ingest.py --manuals-dir .\data\manuals --reset-collection
uvicorn techdocs_llmops.api.main:app --reload --host 127.0.0.1 --port 8000
```

For a polished local demo with a dedicated port, use **`scripts/dev-server.ps1`** (defaults to **8010**).

Open [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) (or your chosen port) and call **`POST /v1/ask`**:

```json
{
  "question": "What is the minimum serviceable thickness for the main gear brake stack?",
  "k": 6
}
```

---

## Sample API response

With manuals indexed and Ollama running, **`POST /v1/ask`** returns a **structured payload**: a grounded **`answer`** and **`sources`** (excerpts, similarity ranks, file paths, pages). Capture below: **Swagger UI** (`/docs`) for the request above.

![Sample POST /v1/ask response: main gear brake stack — answer and cited sources](v1-ask-main-gear-brake-stack-response.jpeg)

---

## Alternative: helper scripts

- **`scripts/dev-server.ps1`** — one-command API bootstrapping (default port **8010**).
- **`scripts/free-port.ps1`** — Windows helper to clear a busy port before demos or CI.

---

## Health checks

| Endpoint | Purpose |
|----------|---------|
| `GET /` | Service overview and deep links |
| `GET /health` | Chroma persistence path and live configuration snapshot |
| `GET /health/ollama` | Live probe of Ollama (`/api/tags`) |

---

## API

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/v1/ask` | RAG query — returns **`answer`** + **`sources`** |
| `POST` | `/v1/reindex` | **Opt-in** on-host reindex; enable with `ENABLE_REINDEX_API=true` |

**CLI ingest** remains the primary path for bulk, repeatable indexing; the reindex route is there when teams want **API-driven** refresh workflows.

---

## Configuration

Copy [`.env.example`](.env.example) to `.env`. The default profile needs **zero cloud API keys**.

| Variable | Purpose |
|----------|---------|
| `CHROMA_PERSIST_DIR` | On-disk Chroma persistence |
| `MANUALS_DIR` | Default directory for PDFs |
| `CHROMA_COLLECTION_NAME` | Collection name |
| `EMBEDDING_MODEL` | sentence-transformers model id |
| `CHUNK_SIZE` / `CHUNK_OVERLAP` | LangChain `RecursiveCharacterTextSplitter` |
| `OLLAMA_BASE_URL` | Default `http://127.0.0.1:11434` |
| `OLLAMA_MODEL` | Pulled Ollama model (see `ollama list`, e.g. `llama3:latest`) |
| `DEFAULT_TOP_K` | Default retrieval depth for `/v1/ask` |
| `ENABLE_REINDEX_API` | `true` to expose `POST /v1/reindex` |

---

## Air-gap and privacy

- **No cloud LLM or embedding APIs** on the default path — **sentence-transformers** + **Ollama** keep workloads local.
- After first materialize, you can operate with **network disabled** once wheels and weights are cached.
- **High-value artifacts** you can snapshot or pre-seed:
  - **Chroma**: `CHROMA_PERSIST_DIR`
  - **HuggingFace cache**: typically `%USERPROFILE%\.cache\huggingface\`
  - **Ollama models**: `%USERPROFILE%\.ollama\models`

Repository hygiene: **`.env`**, proprietary PDFs, and vector data stay **out of version control** via [`.gitignore`](.gitignore).

---

## Tests

Pytest enables **`TECHDOCS_TESTING=1`** (see [`tests/conftest.py`](tests/conftest.py)) so the stack can run with **`FakeEmbeddings`** — fast feedback without pulling embedding weights. [`pyproject.toml`](pyproject.toml) sets `pythonpath = ["src"]` for clean imports.

```powershell
pytest
```

---

## Project layout

| Path | Role |
|------|------|
| [`architecture-diagram.png`](architecture-diagram.png) | Architecture diagram (root) |
| [`v1-ask-main-gear-brake-stack-response.jpeg`](v1-ask-main-gear-brake-stack-response.jpeg) | Live **`/v1/ask`** sample (Swagger) — brake stack query, **`k: 6`** |
| [`src/techdocs_llmops/`](src/techdocs_llmops/) | Application package: config, ingest, vector store, RAG chain, API |
| [`scripts/ingest.py`](scripts/ingest.py) | CLI ingestion |
| [`scripts/dev-server.ps1`](scripts/dev-server.ps1) | Dev server launcher |
| [`tests/`](tests/) | Pytest suite |

---

## Maintainer

Built and maintained by [@momo-s15](https://github.com/momo-s15) — **TechDocs-LLMOps**: a **showcase-grade** local RAG stack you can fork, extend, and drop into portfolio or architecture conversations.
