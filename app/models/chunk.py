from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.models.base import MongoModel

ChunkingStrategy = Literal["fixed-size", "sentence-aware"]


class Chunk(MongoModel):
    doc_id: str
    chunk_index: int
    estrategia_chunking: ChunkingStrategy
    chunk_texto: str
    embedding: list[float] = Field(min_length=384, max_length=384)
    modelo: str
    fecha_ingesta: datetime
    metadata: dict[str, str | int | float | bool | None] = Field(default_factory=dict)


class ChunkStats(BaseModel):
    estrategia_chunking: ChunkingStrategy
    total_chunks: int
    promedio_caracteres: float
    minimo_caracteres: int
    maximo_caracteres: int
