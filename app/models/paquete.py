from datetime import date

from pydantic import Field

from app.models.base import AuditFields, MongoModel


class PaqueteTuristico(MongoModel, AuditFields):
    nombre: str
    destino_id: str
    descripcion: str
    precio_base: float
    duracion_dias: int
    servicios_incluidos: list[str] = Field(default_factory=list)
    fecha_inicio_vigencia: date | None = None
    fecha_fin_vigencia: date | None = None
