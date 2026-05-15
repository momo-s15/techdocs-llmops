from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException, Request
from langchain_chroma import Chroma
from techdocs_llmops.api.schemas import (
    AskRequest,
    AskResponse,
    HealthResponse,
    OllamaHealthResponse,
    ReindexRequest,
    ReindexResponse,
    SourceChunk,
)
from techdocs_llmops.config import Settings, get_settings
from techdocs_llmops.ingest.pipeline import ingest_directory
from techdocs_llmops.rag.chain import run_rag
from techdocs_llmops.vectorstore.factory import get_chroma_store, get_embeddings

logger = logging.getLogger(__name__)

_FAKE_EMBEDDING_DIM = 384


def _testing_mode() -> bool:
    return os.environ.get("TECHDOCS_TESTING", "").strip().lower() in ("1", "true", "yes")


def _make_embeddings(settings: Settings):
    if _testing_mode():
        from langchain_community.embeddings import FakeEmbeddings

        logger.warning("TECHDOCS_TESTING is set: using FakeEmbeddings (no HuggingFace download)")
        return FakeEmbeddings(size=_FAKE_EMBEDDING_DIM)
    return get_embeddings(settings)


def _excerpt(text: str, max_len: int = 400) -> str:
    t = text.strip().replace("\n", " ")
    if len(t) <= max_len:
        return t
    return t[: max_len - 1] + "…"


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    logging.basicConfig(level=level, format="%(levelname)s %(name)s %(message)s")
    settings.chroma_path().mkdir(parents=True, exist_ok=True)
    settings.manuals_path().mkdir(parents=True, exist_ok=True)

    logger.info("Warming embedding model and Chroma (collection=%s)", settings.chroma_collection_name)
    embeddings = _make_embeddings(settings)
    store = get_chroma_store(settings, embeddings)
    app.state.settings = settings
    app.state.embeddings = embeddings
    app.state.store = store
    yield


app = FastAPI(
    title="TechDocs-LLMOps",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/")
def root() -> dict[str, str]:
    """Avoid a bare 404 when opening the server root in a browser."""
    return {
        "service": "TechDocs-LLMOps",
        "docs": "/docs",
        "openapi": "/openapi.json",
        "health": "/health",
        "health_ollama": "/health/ollama",
        "ask": "POST /v1/ask",
    }


@app.get("/health", response_model=HealthResponse)
def health(request: Request) -> HealthResponse:
    settings: Settings = request.app.state.settings
    path = settings.chroma_path()
    return HealthResponse(
        status="ok",
        chroma_persist_dir=str(path),
        chroma_exists=path.is_dir(),
        ollama_model=settings.ollama_model,
    )


@app.get("/health/ollama", response_model=OllamaHealthResponse)
def health_ollama(request: Request) -> OllamaHealthResponse:
    settings: Settings = request.app.state.settings
    url = settings.ollama_base_url.rstrip("/") + "/api/tags"
    try:
        r = httpx.get(url, timeout=5.0)
        r.raise_for_status()
        return OllamaHealthResponse(ok=True, detail=None)
    except Exception as exc:
        logger.warning("Ollama health check failed: %s", exc)
        return OllamaHealthResponse(ok=False, detail=str(exc))


@app.post("/v1/ask", response_model=AskResponse)
def ask(request: Request, body: AskRequest) -> AskResponse:
    settings: Settings = request.app.state.settings
    store: Chroma = request.app.state.store
    try:
        answer, chunks = run_rag(
            store,
            body.question,
            settings,
            k=body.k,
        )
    except Exception as exc:
        logger.exception("POST /v1/ask failed during retrieval or Ollama generation")
        raise HTTPException(
            status_code=503,
            detail=(
                "RAG step failed (often: Ollama not running, wrong OLLAMA_MODEL, or model not pulled). "
                f"Underlying error: {exc}"
            ),
        ) from exc
    sources = [
        SourceChunk(
            chunk_id=c.chunk_id,
            excerpt=_excerpt(c.text),
            score=c.score,
            source=c.source,
            page=c.page,
        )
        for c in chunks
    ]
    return AskResponse(answer=answer, sources=sources)


@app.post("/v1/reindex", response_model=ReindexResponse)
def reindex(request: Request, body: ReindexRequest) -> ReindexResponse:
    settings: Settings = request.app.state.settings
    if not settings.enable_reindex_api:
        raise HTTPException(status_code=403, detail="Reindex API is disabled (set ENABLE_REINDEX_API=true)")

    embeddings = request.app.state.embeddings
    manuals = Path(body.manuals_dir).resolve() if body.manuals_dir else settings.manuals_path()
    n = ingest_directory(
        settings,
        embeddings,
        manuals_dir=manuals,
        reset_collection=body.reset_collection,
    )
    request.app.state.store = get_chroma_store(settings, embeddings)
    return ReindexResponse(chunks_indexed=n)
