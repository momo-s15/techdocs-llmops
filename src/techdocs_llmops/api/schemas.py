from __future__ import annotations

from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=4000)
    k: int | None = Field(default=None, ge=1, le=32)


class SourceChunk(BaseModel):
    chunk_id: str
    excerpt: str = Field(..., description="Short excerpt from the retrieved chunk")
    score: float
    source: str | None = None
    page: int | None = None


class AskResponse(BaseModel):
    answer: str
    sources: list[SourceChunk]


class HealthResponse(BaseModel):
    status: str
    chroma_persist_dir: str
    chroma_exists: bool
    ollama_model: str


class OllamaHealthResponse(BaseModel):
    ok: bool
    detail: str | None = None


class ReindexRequest(BaseModel):
    reset_collection: bool = False
    manuals_dir: str | None = Field(
        default=None,
        description="Override manuals directory; defaults to MANUALS_DIR from settings",
    )


class ReindexResponse(BaseModel):
    chunks_indexed: int
