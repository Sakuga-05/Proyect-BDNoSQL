#schemas/search.py
from typing import Any

from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(min_length=2, max_length=1000)
    limit: int = Field(default=5, ge=1, le=20)
    estrategia_chunking: str | None = None
    filters: dict[str, Any] = Field(default_factory=dict)


class SearchResult(BaseModel):
    id: str | None = None
    doc_id: str | None = None
    score: float | None = None
    texto: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class SearchResponse(BaseModel):
    query: str
    total: int
    results: list[SearchResult]
