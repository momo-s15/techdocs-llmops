from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass

from langchain_chroma import Chroma
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama

from techdocs_llmops.config import Settings
from techdocs_llmops.rag.prompts import RAG_SYSTEM_PROMPT, RAG_USER_TEMPLATE

logger = logging.getLogger(__name__)


def _ctx_id(source: str, page: object, text: str) -> str:
    base = f"{source}|{page}|{text[:240]}"
    return hashlib.sha256(base.encode("utf-8", errors="ignore")).hexdigest()[:12]


@dataclass
class RetrievedChunk:
    chunk_id: str
    text: str
    score: float
    source: str | None
    page: int | None


def retrieve(
    store: Chroma,
    question: str,
    *,
    k: int,
) -> list[RetrievedChunk]:
    pairs = store.similarity_search_with_score(question, k=k)
    out: list[RetrievedChunk] = []
    for doc, score in pairs:
        src = doc.metadata.get("source")
        page = doc.metadata.get("page")
        if page is not None:
            try:
                page_int = int(page)
            except (TypeError, ValueError):
                page_int = None
        else:
            page_int = None
        cid = _ctx_id(str(src or ""), page, doc.page_content)
        out.append(
            RetrievedChunk(
                chunk_id=cid,
                text=doc.page_content,
                score=float(score),
                source=str(src) if src else None,
                page=page_int,
            )
        )
    return out


def _message_text(content: object) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and isinstance(block.get("text"), str):
                parts.append(block["text"])
            else:
                parts.append(str(block))
        return "".join(parts)
    return str(content)


def generate_answer(
    question: str,
    chunks: list[RetrievedChunk],
    settings: Settings,
) -> str:
    context_blocks = []
    for c in chunks:
        context_blocks.append(f"[CTX: {c.chunk_id}]\n{c.text.strip()}")
    context = "\n\n---\n\n".join(context_blocks)
    user_content = RAG_USER_TEMPLATE.format(context=context, question=question.strip())

    llm = ChatOllama(
        model=settings.ollama_model,
        base_url=settings.ollama_base_url,
        temperature=0,
        timeout=120.0,
    )
    messages = [
        SystemMessage(content=RAG_SYSTEM_PROMPT),
        HumanMessage(content=user_content),
    ]
    response = llm.invoke(messages)
    return _message_text(getattr(response, "content", None)).strip()


def run_rag(
    store: Chroma,
    question: str,
    settings: Settings,
    *,
    k: int | None = None,
) -> tuple[str, list[RetrievedChunk]]:
    top_k = k if k is not None else settings.default_top_k
    chunks = retrieve(store, question, k=top_k)
    if not chunks:
        logger.info("No retrieval hits for question (top_k=%s)", top_k)
        return (
            "No matching content was found in the indexed manuals for this question. "
            "Ingest relevant PDFs or rephrase the query.",
            [],
        )
    logger.info(
        "Retrieved %d chunks; scores=%s",
        len(chunks),
        [round(c.score, 4) for c in chunks],
    )
    answer = generate_answer(question, chunks, settings)
    return answer, chunks
