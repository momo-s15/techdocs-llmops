from __future__ import annotations

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from techdocs_llmops.api.main import app
from techdocs_llmops.rag.chain import RetrievedChunk


@patch("techdocs_llmops.api.main.run_rag")
def test_ask_returns_sources(mock_run: MagicMock) -> None:
    mock_run.return_value = (
        "Test answer",
        [
            RetrievedChunk(
                chunk_id="abc123",
                text="some long text " * 20,
                score=0.42,
                source="manual.pdf",
                page=3,
            )
        ],
    )
    with TestClient(app) as client:
        r = client.post("/v1/ask", json={"question": "What is torque?"})
    assert r.status_code == 200
    data = r.json()
    assert data["answer"] == "Test answer"
    assert len(data["sources"]) == 1
    assert data["sources"][0]["chunk_id"] == "abc123"
    assert "score" in data["sources"][0]


def test_reindex_forbidden_by_default() -> None:
    with TestClient(app) as client:
        r = client.post("/v1/reindex", json={"reset_collection": False})
    assert r.status_code == 403


def test_root_returns_service_links() -> None:
    with TestClient(app) as client:
        r = client.get("/")
    assert r.status_code == 200
    data = r.json()
    assert data["service"] == "TechDocs-LLMOps"
    assert data["docs"] == "/docs"
