from datetime import datetime

from pydantic import Field

from app.models.base import AuditFields, MongoModel


class Multimedia(MongoModel, AuditFields):
    titulo: str
    descripcion: str | None = None
    tipo: str
    url: str
    destino_id: str | None = None
    paquete_id: str | None = None
    tags: list[str] = Field(default_factory=list)
    embedding: list[float] | None = None
    modelo: str | None = None
    fecha_ingesta: datetime | None = None
