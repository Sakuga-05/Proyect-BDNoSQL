from typing import Any

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.config.collections import COLLECTIONS
from app.config.database import get_database
from app.utils.helpers import serialize_many, serialize_mongo

router = APIRouter(prefix="/catalog", tags=["catalog"])


def parse_filter_value(value: str) -> Any:
    if ObjectId.is_valid(value):
        return ObjectId(value)
    return value


@router.get("/stats", status_code=status.HTTP_200_OK)
async def catalog_stats(
    db: AsyncIOMotorDatabase = Depends(get_database),
) -> dict[str, int]:
    tracked = (
        "destino",
        "paqueteTuristico",
        "resena",
        "multimedia",
        "multimedia_clip",
        "chunks",
        "alojamiento",
        "guiaTuristico",
        "transporte",
        "proveedor",
        "seguroViaje",
        "viajeProgramado",
        "participante",
        "pago",
        "evaluaciones",
    )
    return {name: await db[name].count_documents({}) for name in tracked}


@router.get("/{collection_name}", status_code=status.HTTP_200_OK)
async def catalog_list(
    collection_name: str,
    limit: int = Query(default=50, ge=1, le=300),
    skip: int = Query(default=0, ge=0),
    db: AsyncIOMotorDatabase = Depends(get_database),
) -> dict[str, Any]:
    if collection_name not in COLLECTIONS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Coleccion no soportada: {collection_name}",
        )

    cursor = db[collection_name].find({}).skip(skip).limit(limit)
    documents = await cursor.to_list(length=limit)
    total = await db[collection_name].count_documents({})
    return {
        "collection": collection_name,
        "total": total,
        "limit": limit,
        "skip": skip,
        "results": serialize_many(documents),
    }


@router.get("/{collection_name}/{document_id}", status_code=status.HTTP_200_OK)
async def catalog_detail(
    collection_name: str,
    document_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
) -> dict[str, Any]:
    if collection_name not in COLLECTIONS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Coleccion no soportada: {collection_name}",
        )

    filters = {"_id": parse_filter_value(document_id)}
    document = await db[collection_name].find_one(filters)
    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Documento no encontrado",
        )
    return serialize_mongo(document)
