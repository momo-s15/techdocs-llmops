"""CLI: ingest PDFs from a directory into local Chroma."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from techdocs_llmops.config import get_settings
from techdocs_llmops.ingest.pipeline import ingest_directory
from techdocs_llmops.vectorstore.factory import get_embeddings


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest PDF manuals into local ChromaDB")
    parser.add_argument(
        "--manuals-dir",
        type=Path,
        default=None,
        help="Directory containing .pdf files (default: MANUALS_DIR from env / settings)",
    )
    parser.add_argument(
        "--reset-collection",
        action="store_true",
        help="Delete the Chroma collection before re-indexing",
    )
    args = parser.parse_args()
    settings = get_settings()
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(levelname)s %(name)s %(message)s",
    )
    embeddings = get_embeddings(settings)
    n = ingest_directory(
        settings,
        embeddings,
        manuals_dir=args.manuals_dir,
        reset_collection=args.reset_collection,
    )
    print(f"Indexed {n} chunks into collection {settings.chroma_collection_name}")


if __name__ == "__main__":
    main()
