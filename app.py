from fastapi import FastAPI, UploadFile, File, Query, HTTPException
from fastapi.responses import JSONResponse
from pathlib import Path
import json

from utils_kaggle import ensure_pkg, ensure_kaggle_token, kaggle_download
from prepare_data import scan_images, unify_and_clean, export_clean_256
from train_multi import train_all
from infer import predict_bytes

try:
    DATASETS_CATALOG = json.loads(Path("datasets_catalog.json").read_text(encoding="utf-8"))
    CATALOG_ERROR = ""
except FileNotFoundError:
    DATASETS_CATALOG, CATALOG_ERROR = None, "datasets_catalog.json not found"
except json.JSONDecodeError:
    DATASETS_CATALOG, CATALOG_ERROR = None, "datasets_catalog.json is malformed"

app = FastAPI(title="Furniture/Interior AI", version="1.0.0")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/download")
def download_all(skip_if_exists: bool = True):
    """ينزّل كل الـ datasets من datasets_catalog.json"""
    if DATASETS_CATALOG is None:
        return JSONResponse({"ok": False, "error": CATALOG_ERROR}, status_code=500)
    try:
        ensure_pkg("kaggle")
    except ImportError as e:
        raise HTTPException(status_code=500, detail=str(e))
    ensure_kaggle_token()

    for item in DATASETS_CATALOG:
        kaggle_download(item["slug"], item["dest"], skip_if_exists=skip_if_exists)
    return {"ok": True, "message": "Downloaded/checked datasets."}

@app.post("/prepare")
def prepare():
    """يمسح الصور ويجهز CSV موحد ويصدر clean256/train, clean256/val"""
    if DATASETS_CATALOG is None:
        return JSONResponse({"ok": False, "error": CATALOG_ERROR}, status_code=500)
    rows = []
    for it in DATASETS_CATALOG:
        rows += scan_images(it["dest"], it["slug"])
    df = unify_and_clean(rows, min_size=256, csv_out="data/unified_images.csv")
    out_dir = export_clean_256(csv_path="data/unified_images.csv", out_dir="data/clean256", img_size=256)
    return {"ok": True, "rows": len(df), "out_dir": out_dir}

@app.post("/train")
def train():
    """يدرب 3 موديلات ويحفظ أفضل 3 + يصدر TorchScript/ONNX للموديل الأفضل"""
    results = train_all()
    return {"ok": True, "results": results}

@app.post("/predict")
async def predict(file: UploadFile = File(...), topk: int = Query(3, ge=1, le=10)):
    """تنبؤ بصورة واحدة (ارفع ملف صورة) — يرجع أفضل topk تصنيفات"""
    image_bytes = await file.read()
    try:
        preds, best = predict_bytes(image_bytes, topk=topk)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"ok": True, "backbone": best["model"], "predictions": preds}

@app.get("/labels")
def labels():
    """يعرض قائمة الملصقات (الفئات) بعد التدريب"""
    p = Path("artifacts/labels.json")
    if not p.exists():
        return JSONResponse({"ok": False, "error": "labels.json not found. درب النموذج أولاً."}, status_code=404)
    return json.loads(p.read_text(encoding="utf-8"))

@app.get("/results")
def results():
    """يعرض finetune_results.json (أفضل 3)"""
    p = Path("artifacts/finetune_results.json")
    if not p.exists():
        return JSONResponse({"ok": False, "error": "finetune_results.json not found. درب النموذج أولاً."}, status_code=404)
    return json.loads(p.read_text(encoding="utf-8"))
