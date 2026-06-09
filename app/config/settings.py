#app/config/settings.py
from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Settings leidos desde variables de entorno y .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    app_name: str = "Agencia de Viajes RAG API"
    app_version: str = "0.1.0"
    environment: Literal["local", "dev", "staging", "prod"] = "local"
    log_level: str = "INFO"

    mongo_uri: str = Field(alias="MONGO_URI")
    db_name: str = Field(default="agencia_viajes_rag", alias="DB_NAME")
    mongodb_vector_index: str = Field(default="vector_index", alias="MONGODB_VECTOR_INDEX")
    mongodb_multimedia_vector_index: str = Field(
        default="multimedia_vector_index",
        alias="MONGODB_MULTIMEDIA_VECTOR_INDEX",
    )
    mongodb_multimedia_clip_vector_index: str = Field(
        default="multimedia_clip_vector_index",
        alias="MONGODB_MULTIMEDIA_CLIP_VECTOR_INDEX",
    )

    embedding_model: str = Field(default="all-MiniLM-L6-v2", alias="EMBEDDING_MODEL")
    embedding_dim: int = Field(default=384, alias="EMBEDDING_DIM")
    clip_embedding_model: str = Field(
        default="sentence-transformers/clip-ViT-B-32",
        alias="CLIP_EMBEDDING_MODEL",
    )
    clip_embedding_dim: int = Field(default=512, alias="CLIP_EMBEDDING_DIM")

    gemini_api_key: str | None = Field(default=None, alias="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-2.5-flash", alias="GEMINI_MODEL")

    default_search_limit: int = 5
    vector_num_candidates: int = 100
    chunk_size: int = 500
    chunk_overlap: int = 100
    sentence_chunk_max_chars: int = 500


@lru_cache
def get_settings() -> Settings:
    return Settings()
