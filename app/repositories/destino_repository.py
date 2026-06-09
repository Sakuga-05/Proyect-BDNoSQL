from motor.motor_asyncio import AsyncIOMotorDatabase

from app.repositories.catalog_repository import CatalogRepository


class DestinoRepository(CatalogRepository):
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        super().__init__(db, "destino")
