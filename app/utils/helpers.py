from datetime import UTC, date, datetime
from typing import Any

from bson import ObjectId


def utc_now() -> datetime:
    return datetime.now(UTC)


def serialize_mongo(document: dict[str, Any]) -> dict[str, Any]:
    return {key: serialize_mongo_value(value) for key, value in document.items()}


def serialize_mongo_value(value: Any) -> Any:
    if isinstance(value, ObjectId):
        return str(value)
    if isinstance(value, datetime | date):
        return value.isoformat()
    if isinstance(value, list):
        return [serialize_mongo_value(item) for item in value]
    if isinstance(value, dict):
        return {key: serialize_mongo_value(item) for key, item in value.items()}
    return value


def serialize_many(documents: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [serialize_mongo(document) for document in documents]
