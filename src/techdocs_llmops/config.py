from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    chroma_persist_dir: str = "./data/chroma"
    manuals_dir: str = "./data/manuals"
    chroma_collection_name: str = "techdocs_v1"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    chunk_size: int = 1000
    chunk_overlap: int = 200
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "llama3:latest"
    default_top_k: int = 4
    enable_reindex_api: bool = False
    log_level: str = "INFO"

    def chroma_path(self) -> Path:
        return Path(self.chroma_persist_dir).resolve()

    def manuals_path(self) -> Path:
        return Path(self.manuals_dir).resolve()


def get_settings() -> Settings:
    return Settings()
