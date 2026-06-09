from pathlib import Path
from typing import Any

from bson import ObjectId

from app.utils.helpers import utc_now

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
STATIC_IMG_DIR = Path(__file__).resolve().parents[1] / "static" / "img"


def iter_destination_images(static_img_dir: Path = STATIC_IMG_DIR) -> list[tuple[str, Path]]:
    if not static_img_dir.exists():
        return []

    images: list[tuple[str, Path]] = []
    for destination_dir in sorted(path for path in static_img_dir.iterdir() if path.is_dir()):
        for image_path in sorted(destination_dir.iterdir()):
            if image_path.is_file() and image_path.suffix.lower() in IMAGE_EXTENSIONS:
                images.append((destination_dir.name, image_path))
    return images


def build_static_url(destination_name: str, image_path: Path) -> str:
    return f"/static/img/{destination_name}/{image_path.name}"


def build_visual_description(destination: dict[str, Any], image_index: int) -> str:
    destination_name = str(destination.get("nombre", "Destino turistico"))
    category = destination.get("categoria")
    tags = ", ".join(destination.get("tags") or [])
    base_description = destination.get("descripcion") or ""
    parts = [
        f"Imagen {image_index} de {destination_name}",
        f"categoria {category}" if category else "",
        base_description,
        f"Tags: {tags}" if tags else "",
    ]
    return ". ".join(part for part in parts if part).strip()


def build_multimedia_document(
    destination: dict[str, Any],
    image_path: Path,
    image_index: int,
) -> dict[str, Any]:
    destination_name = str(destination["nombre"])
    tags = list(destination.get("tags") or [])
    destination_id = destination.get("_id")
    if destination_id is not None and not isinstance(destination_id, ObjectId):
        destination_id = ObjectId(str(destination_id))

    return {
        "destino_id": destination_id,
        "nombre_destino": destination_name,
        "titulo": f"{destination_name} - imagen {image_index}",
        "tipo": "imagen",
        "url": build_static_url(destination_name, image_path),
        "descripcion": build_visual_description(destination, image_index),
        "descripcion_visual": build_visual_description(destination, image_index),
        "tags": tags,
        "metadata": {
            "nombre_archivo": image_path.name,
            "nombre_destino": destination_name,
            "categoria_destino": destination.get("categoria"),
        },
        "creado_en": utc_now(),
    }
