from pydantic import BaseModel, Field


class MultimediaClipTextSearchRequest(BaseModel):
    query: str = Field(min_length=2, max_length=1000)
    limit: int = Field(default=8, ge=1, le=30)


class MultimediaClipSearchResult(BaseModel):
    id: str | None = None
    url: str
    nombre_destino: str | None = None
    descripcion_visual: str | None = None
    score: float | None = None


class MultimediaClipSearchResponse(BaseModel):
    query: str | None = None
    total: int
    results: list[MultimediaClipSearchResult]
