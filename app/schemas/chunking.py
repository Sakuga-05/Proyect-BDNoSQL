from typing import Literal

from pydantic import BaseModel, Field

from app.models.chunk import ChunkStats, ChunkingStrategy


class ChunkingCompareRequest(BaseModel):
    doc_id: str = Field(min_length=2, max_length=200)
    text: str = Field(min_length=20)
    strategies: list[ChunkingStrategy] = Field(default_factory=lambda: ["fixed-size", "sentence-aware"])
    persist: bool = False


class ChunkPreview(BaseModel):
    chunk_index: int
    estrategia_chunking: ChunkingStrategy
    chunk_texto: str
    caracteres: int


class ChunkingCompareResponse(BaseModel):
    doc_id: str
    persisted: bool
    stats: list[ChunkStats]
    previews: list[ChunkPreview]
