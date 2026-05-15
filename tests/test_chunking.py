from __future__ import annotations

from langchain_core.documents import Document

from techdocs_llmops.config import Settings
from techdocs_llmops.ingest.chunking import chunk_documents, get_splitter


def test_get_splitter_produces_multiple_chunks() -> None:
    s = Settings(chunk_size=100, chunk_overlap=10)
    sp = get_splitter(s)
    parts = sp.split_text("word " * 80)
    assert len(parts) >= 2
    assert max(len(p) for p in parts) <= 120


def test_chunk_documents_splits() -> None:
    s = Settings(chunk_size=50, chunk_overlap=5)
    docs = [
        Document(page_content="x" * 120, metadata={"source": "t.pdf", "page": 0}),
    ]
    chunks = chunk_documents(docs, s)
    assert len(chunks) >= 2
    assert sum(len(c.page_content) for c in chunks) >= 100
