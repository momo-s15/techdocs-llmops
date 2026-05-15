from __future__ import annotations

import logging
import time
from pathlib import Path

from langchain_chroma import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document

from techdocs_llmops.config import Settings
from techdocs_llmops.ingest.chunking import chunk_documents
from techdocs_llmops.ingest.pdf_loader import load_pdf
from techdocs_llmops.vectorstore.factory import (
    delete_collection_if_exists,
    get_chroma_store,
)

logger = logging.getLogger(__name__)


def load_all_pdfs(manuals_dir: Path) -> list[Document]:
    pdfs = sorted(manuals_dir.glob("*.pdf"))
    if not pdfs:
        logger.warning("No PDF files found in %s", manuals_dir)
    documents: list[Document] = []
    for pdf_path in pdfs:
        logger.info("Loading PDF: %s", pdf_path.name)
        documents.extend(load_pdf(pdf_path))
    return documents


def ingest_directory(
    settings: Settings,
    embeddings: HuggingFaceEmbeddings,
    *,
    manuals_dir: Path | None = None,
    reset_collection: bool = False,
) -> int:
    root = manuals_dir or settings.manuals_path()
    if not root.is_dir():
        raise FileNotFoundError(f"Manuals directory does not exist: {root}")

    t0 = time.perf_counter()
    if reset_collection:
        delete_collection_if_exists(settings)

    raw_docs = load_all_pdfs(root)
    chunks = chunk_documents(raw_docs, settings)
    logger.info(
        "Chunked %d raw pages/documents into %d chunks (chunk_size=%s overlap=%s)",
        len(raw_docs),
        len(chunks),
        settings.chunk_size,
        settings.chunk_overlap,
    )

    store = get_chroma_store(settings, embeddings)
    if chunks:
        store.add_documents(chunks)
    elapsed = time.perf_counter() - t0
    logger.info("Ingest finished in %.2fs; indexed %d chunks", elapsed, len(chunks))
    return len(chunks)
