from __future__ import annotations

import os
import re
from io import BytesIO

from fastapi import Header, HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", str(10 * 1024 * 1024)))
MAX_IMAGE_PIXELS = int(os.getenv("MAX_IMAGE_PIXELS", "25000000"))


def allowed_origins() -> list[str]:
    configured = os.getenv("ALLOWED_ORIGINS", "http://localhost:8501,http://127.0.0.1:8501")
    origins = [value.strip() for value in configured.split(",") if value.strip()]
    if "*" in origins and os.getenv("ALLOW_CREDENTIALS", "false").lower() == "true":
        raise RuntimeError("Wildcard CORS cannot be combined with credentials")
    return origins


def allow_credentials() -> bool:
    return os.getenv("ALLOW_CREDENTIALS", "false").lower() == "true"


def require_admin(x_admin_key: str | None = Header(default=None)) -> None:
    expected = os.getenv("ADMIN_API_KEY")
    if not expected:
        raise HTTPException(status_code=503, detail="Administrative API is not configured")
    if x_admin_key != expected:
        raise HTTPException(status_code=401, detail="Invalid administrative API key")


async def read_validated_image(file: UploadFile) -> tuple[bytes, Image.Image]:
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=415, detail="Only JPEG, PNG, and WebP images are accepted")
    payload = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(payload) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Image exceeds the upload limit")
    if not payload:
        raise HTTPException(status_code=400, detail="Uploaded image is empty")
    try:
        with Image.open(BytesIO(payload)) as probe:
            probe.verify()
        image = Image.open(BytesIO(payload)).convert("RGB")
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise HTTPException(status_code=400, detail="Invalid or corrupted image") from exc
    if image.width * image.height > MAX_IMAGE_PIXELS:
        raise HTTPException(status_code=413, detail="Image dimensions exceed the safe pixel limit")
    return payload, image


def safe_slug(value: str, *, fallback: str = "item") -> str:
    normalized = re.sub(r"[^a-zA-Z0-9_-]+", "-", value.strip()).strip("-_").lower()
    return normalized[:80] or fallback


def canonical_floor_plan(raw: dict, *, width: int, height: int) -> dict:
    rooms = []
    for index, room in enumerate(raw.get("rooms", []), start=1):
        bounding = room.get("bounding_box", {})
        x = float(bounding.get("x", 0))
        y = float(bounding.get("y", 0))
        box_width = float(bounding.get("width", 0))
        box_height = float(bounding.get("height", 0))
        rooms.append(
            {
                "id": f"room-{room.get('id', index)}",
                "room_type": str(room.get("type", "unknown")),
                "polygon": [
                    {"x": x, "y": y},
                    {"x": x + box_width, "y": y},
                    {"x": x + box_width, "y": y + box_height},
                    {"x": x, "y": y + box_height},
                ],
                "area": float(room.get("area_pixels", box_width * box_height)),
                "confidence": None,
                "furniture": room.get("furniture_recommendations", []),
            }
        )
    return {
        "schema_version": "1.0",
        "source_width": width,
        "source_height": height,
        "unit": "px",
        "scale": None,
        "rooms": rooms,
        "openings": [
            {"kind": "door", **opening} for opening in raw.get("doors", [])
        ]
        + [{"kind": "window", **opening} for opening in raw.get("windows", [])],
        "warnings": [
            "Room labels are heuristic unless a trained semantic classifier is configured."
        ],
    }
