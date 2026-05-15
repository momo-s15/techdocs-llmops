# TechDocs-LLMOps

Air-gapped, local **Retrieval-Augmented Generation (RAG)** for dense technical manuals: PDF ingestion, HuggingFace embeddings on CPU, ChromaDB on disk, and answers via **Ollama** (local LLM). FastAPI exposes `POST /v1/ask` for downstream tools.

## Requirements

- Python **3.10+** (64-bit recommended on Windows)
- [Ollama](https://ollama.com/) installed and a model pulled, for example: `ollama pull llama3` (use the exact name from `ollama list` in `OLLAMA_MODEL`, e.g. `llama3:latest`)
- Optional: NVIDIA GPU for faster Ollama inference (embeddings default to CPU)

## Quick start (Windows)

From the project root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
copy .env.example .env
```

Put PDF manuals under `data\manuals\` (only `*.pdf` are ingested).

```powershell
python scripts\ingest.py --manuals-dir .\data\manuals --reset-collection
uvicorn techdocs_llmops.api.main:app --reload --host 127.0.0.1 --port 8000
```

Open [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) and try `POST /v1/ask` with a JSON body:

```json
{ "question": "What does the manual say about ...?", "k": 4 }
```

### Health checks

- `GET /health` — Chroma path and basic status
- `GET /health/ollama` — probes Ollama (`/api/tags`)

### Reindex via API (optional)

By default `POST /v1/reindex` is **disabled**. Set `ENABLE_REINDEX_API=true` in `.env` to allow on-host reindexing without restarting the server. Prefer `scripts/ingest.py` for air-gap operations when possible.

## Air-gap and privacy

- **No cloud LLM or embedding APIs** in the default path: models run locally (sentence-transformers + Ollama).
- After first install, you can run with **network disabled** once wheels and model weights are cached.
- **Caches to back up or pre-seed** on Windows:
  - Chroma data: directory set by `CHROMA_PERSIST_DIR` (default `./data/chroma`)
  - HuggingFace / sentence-transformers weights: typically under `%USERPROFILE%\.cache\huggingface\`
  - Ollama models: under `%USERPROFILE%\.ollama\models` (see Ollama docs)

## Configuration

Copy [.env.example](.env.example) to `.env` and adjust. All variables are operational knobs (no API keys required for the default stack).

Notable variables:

| Variable | Purpose |
|----------|---------|
| `CHROMA_PERSIST_DIR` | On-disk Chroma persistence |
| `MANUALS_DIR` | Default directory for PDFs |
| `CHROMA_COLLECTION_NAME` | Collection name |
| `EMBEDDING_MODEL` | sentence-transformers model id |
| `CHUNK_SIZE` / `CHUNK_OVERLAP` | LangChain `RecursiveCharacterTextSplitter` |
| `OLLAMA_BASE_URL` | Default `http://127.0.0.1:11434` |
| `OLLAMA_MODEL` | Must match a pulled Ollama model |
| `DEFAULT_TOP_K` | Retrieval depth for `/v1/ask` |
| `ENABLE_REINDEX_API` | `true` to allow `POST /v1/reindex` |

## Ollama CUDA errors on Windows

If `POST /v1/ask` returns **503** with text like **`CUDA error`** or **`shared object initialization failed`**, the **Ollama** process is failing on the **GPU** path (driver/CUDA stack, not this Python repo).

1. **Force Ollama to use CPU** (slower, usually stable). In PowerShell (new sessions will see the variable):

   ```powershell
   setx CUDA_VISIBLE_DEVICES "-1"
   ```

   Then **fully quit Ollama** from the **system tray** and start Ollama again. If it still uses the GPU, **sign out of Windows** or **reboot** once so the tray app inherits the variable.

2. **Fix the GPU stack**: install the latest **NVIDIA driver** from NVIDIA or Windows Update, reboot, then remove `CUDA_VISIBLE_DEVICES` if you want GPU acceleration again.

3. **Smaller model** (after GPU works): set `OLLAMA_MODEL=llama3.2:latest` in `.env` to use less VRAM.

Variables in this project’s **`.env`** only affect our app’s HTTP client to Ollama; they do **not** change how Ollama loads CUDA. Ollama reads **Windows user/system environment variables** for that.

## Restart after CLI ingest

If the API was already running and you ingest new PDFs with `scripts/ingest.py`, **restart Uvicorn** so in-memory Chroma handles pick up the updated index (or use `POST /v1/reindex` with `ENABLE_REINDEX_API=true`).

## Tests

Pytest sets `TECHDOCS_TESTING=1` (see [tests/conftest.py](tests/conftest.py)) so the API uses `FakeEmbeddings` and avoids downloading HuggingFace weights. [pyproject.toml](pyproject.toml) adds `pythonpath = ["src"]` so tests resolve the package without extra `PYTHONPATH` setup.

```powershell
pytest
```

Do **not** set `TECHDOCS_TESTING` for production serving; it is only for automated tests.

## Project layout

- [src/techdocs_llmops/](src/techdocs_llmops/) — application package (config, ingest, vector store, RAG chain, API)
- [scripts/ingest.py](scripts/ingest.py) — CLI ingestion
- [tests/](tests/) — pytest suite

## Limitations (v1)

- PDF text extraction uses **PyPDF**; complex tables or scanned pages may need a different parser in a future revision.
- Retrieval scores are Chroma distance scores (lower is typically “closer” for L2); treat them as relative ranks.
