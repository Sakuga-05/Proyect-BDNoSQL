from typing import Any

from pydantic import Field

from app.models.base import AuditFields, MongoModel


class Destino(MongoModel, AuditFields):
    nombre: str
    pais: str = "Colombia"
    ciudad: str | None = None
    descripcion: str
    categoria: str | None = None
    ubicacion: dict[str, Any] | None = None
    tags: list[str] = Field(default_factory=list)
