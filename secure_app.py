from __future__ import annotations

from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, File, HTTPException, Path as PathParam, Query, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware

from api_utils import (
    allow_credentials,
    allowed_origins,
    canonical_floor_plan,
    read_validated_image,
    require_admin,
    safe_slug,
)

app = FastAPI(
    title="Interior Design AI Suite",
    version="3.0.0",
    description="Secure inference API for interior classification and floor-plan analysis.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins(),
    allow_credentials=allow_credentials(),
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-Admin-Key"],
)


@app.get("/health", tags=["system"])
def health() -> dict[str, object]:
    return {
        "status": "healthy",
        "version": "3.0.0",
        "model_artifacts": {
            "labels": Path("artifacts/labels.json").is_file(),
            "training_results": Path("artifacts/finetune_results.json").is_file(),
        },
        "catalog_mode": "simulated",
    }


@app.post("/api/v2/classify", tags=["inference"])
async def classify_image(
    file: UploadFile = File(...),
    top_k: Annotated[int, Query(ge=1, le=10)] = 3,
) -> dict[str, object]:
    payload, _ = await read_validated_image(file)
    try:
        from infer import predict_bytes

        predictions, model = await run_in_threadpool(predict_bytes, payload, top_k)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail="A trained classifier is not available") from exc
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail="The image could not be classified") from exc
    return {
        "ok": True,
        "model": model.get("model"),
        "model_accuracy": model.get("val_acc"),
        "predictions": predictions,
    }


@app.post("/api/v2/floor-plans/analyze", tags=["floor-plans"])
async def analyze_floor_plan(file: UploadFile = File(...)) -> dict[str, object]:
    payload, image = await read_validated_image(file)
    try:
        from floor_plan_analyzer import analyze_floor_plan_bytes

        raw = await run_in_threadpool(analyze_floor_plan_bytes, payload)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="The floor plan could not be analyzed") from exc
    return {
        "ok": True,
        "analysis": canonical_floor_plan(raw, width=image.width, height=image.height),
        "raw_metrics": {
            "total_rooms": raw.get("total_rooms", 0),
            "wall_count": raw.get("wall_count", 0),
        },
    }


@app.get("/api/v2/recommendations", tags=["recommendations"])
def recommendations(
    room_type: Annotated[str, Query(min_length=2, max_length=64)],
    area_sqm: Annotated[float, Query(ge=3, le=500)],
) -> dict[str, object]:
    from floor_plan_analyzer import FloorPlanAnalyzer

    normalized_type = room_type.strip().lower().replace(" ", "_")
    room = {"type": normalized_type, "area_pixels": int(area_sqm * 1000)}
    items = FloorPlanAnalyzer().recommend_furniture(room)
    return {
        "ok": True,
        "room_type": normalized_type,
        "area_sqm": area_sqm,
        "recommendations": items,
        "method": "rules",
    }


@app.get("/api/v2/catalog/search", tags=["catalog"])
def catalog_search(
    keyword: Annotated[str, Query(min_length=2, max_length=80)],
    category: Annotated[str | None, Query(max_length=64)] = None,
    min_price: Annotated[float | None, Query(ge=0)] = None,
    max_price: Annotated[float | None, Query(ge=0)] = None,
    page: Annotated[int, Query(ge=1, le=10)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 20,
) -> dict[str, object]:
    if min_price is not None and max_price is not None and min_price > max_price:
        raise HTTPException(status_code=422, detail="min_price cannot exceed max_price")
    from alibaba_scraper import AlibabaFurnitureScraper

    scraper = AlibabaFurnitureScraper(rate_limit_seconds=1.0)
    results = scraper.search_furniture(
        keyword=keyword,
        category=category,
        min_price=min_price,
        max_price=max_price,
        page=page,
        page_size=page_size,
        use_cache=True,
    )
    return {
        "ok": True,
        "data_mode": "simulated",
        "notice": "Results are demonstration records, not verified live inventory.",
        "results": results,
    }


@app.get("/api/v2/catalog/products/{product_id}", tags=["catalog"])
def catalog_product(
    product_id: Annotated[str, PathParam(min_length=1, max_length=128)],
) -> dict[str, object]:
    from alibaba_scraper import AlibabaFurnitureScraper

    product = AlibabaFurnitureScraper().get_product_details(product_id)
    return {
        "ok": True,
        "data_mode": "simulated",
        "notice": "Product details are demonstration data and are not verified.",
        "product": product,
    }


@app.post(
    "/api/v2/admin/catalog/export",
    tags=["administration"],
    dependencies=[Depends(require_admin)],
)
def export_catalog(
    keyword: Annotated[str, Query(min_length=2, max_length=80)],
    max_results: Annotated[int, Query(ge=1, le=500)] = 100,
) -> dict[str, object]:
    from alibaba_scraper import AlibabaFurnitureScraper, search_alibaba_furniture

    results = search_alibaba_furniture(keyword=keyword, max_results=max_results)
    output = Path("data") / f"catalog-{safe_slug(keyword)}.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    path = AlibabaFurnitureScraper().save_products_to_file(
        products=results["products"],
        output_path=str(output),
    )
    return {
        "ok": True,
        "data_mode": "simulated",
        "total_saved": len(results["products"]),
        "file_path": path,
    }
