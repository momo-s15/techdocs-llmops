from __future__ import annotations

from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document


def load_pdf(path: Path | str) -> list[Document]:
    loader = PyPDFLoader(str(path))
    return loader.load()
