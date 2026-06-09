# app/schemas/rag.py
from typing import Any

from pydantic import BaseModel, Field


class RagRequest(BaseModel):
    question: str = Field(min_length=3, max_length=2000)
    limit: int = Field(default=5, ge=1, le=10)
    estrategia_chunking: str | None = "sentence-aware"
    filters: dict[str, Any] = Field(default_factory=dict)


class RagSource(BaseModel):
    doc_id: str | None = None
    chunk_index: int | None = None
    score: float | None = None
    texto: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class RagResponse(BaseModel):
    question: str
    answer: str
    sources: list[RagSource]
    query_id: str | None = None
