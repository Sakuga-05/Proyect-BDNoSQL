from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class MongoModel(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={datetime: lambda value: value.isoformat()},
    )

    id: str | None = Field(default=None, alias="_id")


class AuditFields(BaseModel):
    creado_en: datetime | None = None
    actualizado_en: datetime | None = None


class FlexibleDocument(MongoModel):
    nombre: str | None = None
    descripcion: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
