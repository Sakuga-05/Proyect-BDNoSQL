from datetime import date, datetime
from typing import Any

from pydantic import Field

from app.models.base import AuditFields, FlexibleDocument, MongoModel


class Participante(FlexibleDocument, AuditFields):
    contacto: dict[str, Any] = Field(default_factory=dict)
    preferencias: list[str] = Field(default_factory=list)


class Alojamiento(FlexibleDocument, AuditFields):
    destino_id: str | None = None
    categoria: str | None = None
    precio_noche: float | None = None


class Transporte(FlexibleDocument, AuditFields):
    tipo: str | None = None
    proveedor_id: str | None = None
    capacidad: int | None = None


class Proveedor(FlexibleDocument, AuditFields):
    tipo_servicio: str | None = None
    contacto: dict[str, Any] = Field(default_factory=dict)


class GuiaTuristico(FlexibleDocument, AuditFields):
    idiomas: list[str] = Field(default_factory=list)
    destinos: list[str] = Field(default_factory=list)


class ViajeProgramado(MongoModel, AuditFields):
    paquete_id: str
    fecha_inicio: date
    fecha_fin: date
    cupos_disponibles: int
    estado: str = "programado"


class Pago(MongoModel, AuditFields):
    participante_id: str
    viaje_id: str
    monto: float
    moneda: str = "COP"
    estado: str = "pendiente"


class Resena(MongoModel, AuditFields):
    participante_id: str
    paquete_id: str | None = None
    destino_id: str | None = None
    calificacion: int
    comentario: str


class SeguroViaje(FlexibleDocument, AuditFields):
    proveedor_id: str | None = None
    cobertura: list[str] = Field(default_factory=list)
    precio: float | None = None


class ConsultaRag(MongoModel):
    pregunta: str
    respuesta: str
    chunks_usados: list[dict[str, Any]]
    modelo_llm: str
    fecha_consulta: datetime


class Evaluacion(MongoModel):
    consulta_id: str
    puntuacion: float
    comentario: str | None = None
    fecha_evaluacion: datetime
