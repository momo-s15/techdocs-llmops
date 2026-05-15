from __future__ import annotations

from unittest.mock import MagicMock

from techdocs_llmops.config import Settings
from techdocs_llmops.rag.chain import run_rag


def test_run_rag_returns_refusal_when_no_chunks() -> None:
    store = MagicMock()
    store.similarity_search_with_score.return_value = []
    settings = Settings()
    answer, chunks = run_rag(store, "any question?", settings, k=4)
    assert "No matching content" in answer
    assert chunks == []
