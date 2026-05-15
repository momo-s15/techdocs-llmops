"""Pytest setup: fast API tests without downloading embedding models."""

from __future__ import annotations

import os
import tempfile

_tmp_chroma = tempfile.mkdtemp(prefix="techdocs_chroma_test_")
os.environ["TECHDOCS_TESTING"] = "1"
os.environ["CHROMA_PERSIST_DIR"] = _tmp_chroma
