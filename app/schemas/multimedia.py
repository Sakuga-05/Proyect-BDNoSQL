# app/schemas/multimedia.py
from typing import Any

from pydantic import BaseModel, Field


class MultimediaSearchRequest(BaseModel):
    query: str = Field(min_length=2, max_length=1000)
    limit: int = Field(default=8, ge=1, le=30)
    tipo: str | None = None
    destino_id: str | None = None
    filters: dict[str, Any] = Field(default_factory=dict)


class MultimediaSearchResult(BaseModel):
    id: str | None = None
    titulo: str
    descripcion: str | None = None
    tipo: str
    url: str
    score: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class MultimediaSearchResponse(BaseModel):
    query: str
    total: int
    results: list[MultimediaSearchResult]
