from __future__ import annotations

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from techdocs_llmops.config import Settings


def get_splitter(settings: Settings) -> RecursiveCharacterTextSplitter:
    return RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )


def chunk_documents(documents: list[Document], settings: Settings) -> list[Document]:
    splitter = get_splitter(settings)
    return splitter.split_documents(documents)
