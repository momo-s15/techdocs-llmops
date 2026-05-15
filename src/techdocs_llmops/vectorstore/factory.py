from __future__ import annotations

import logging
from pathlib import Path

from langchain_chroma import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

from techdocs_llmops.config import Settings

logger = logging.getLogger(__name__)


def get_embeddings(settings: Settings) -> HuggingFaceEmbeddings:
    logger.info("Loading embedding model: %s", settings.embedding_model)
    return HuggingFaceEmbeddings(
        model_name=settings.embedding_model,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )


def get_chroma_store(settings: Settings, embeddings: HuggingFaceEmbeddings) -> Chroma:
    persist = Path(settings.chroma_persist_dir)
    persist.mkdir(parents=True, exist_ok=True)
    return Chroma(
        collection_name=settings.chroma_collection_name,
        embedding_function=embeddings,
        persist_directory=str(persist),
    )


def delete_collection_if_exists(settings: Settings) -> None:
    import chromadb

    persist = Path(settings.chroma_persist_dir)
    persist.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(persist))
    try:
        client.delete_collection(settings.chroma_collection_name)
        logger.info("Deleted collection %s", settings.chroma_collection_name)
    except Exception:
        logger.debug(
            "No existing collection to delete: %s",
            settings.chroma_collection_name,
        )
