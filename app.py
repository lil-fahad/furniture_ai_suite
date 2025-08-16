from fastapi import FastAPI, UploadFile, File, Query
from fastapi.responses import JSONResponse
from pathlib import Path
import json

from utils_kaggle import ensure_pkg, ensure_kaggle_token, kaggle_download
from prepare_data import scan_images, unify_and_clean, export_clean_256
from train_multi import train_all
from infer import predict_bytes

app = FastAPI(title="Furniture/Interior AI", version="1.0.0")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/download")
def download_all(skip_if_exists: bool = True):
    """ينزّل كل الـ datasets من datasets_catalog.json"""
    try:
        ensure_pkg("kaggle")
    except ImportError as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=500)

    ensure_kaggle_token()

    catalog = json.loads(Path("datasets_catalog.json").read_text(encoding="utf-8"))
    for item in catalog:
        try:
            kaggle_download(item["slug"], item["dest"], skip_if_exists=skip_if_exists)
        except ImportError as e:
            return JSONResponse({"ok": False, "error": str(e)}, status_code=500)
    return {"ok": True, "message": "Downloaded/checked datasets."}

@app.post("/prepare")
def prepare():
    """يمسح الصور ويجهز CSV موحد ويصدر clean256/train, clean256/val"""
    catalog = json.loads(Path("datasets_catalog.json").read_text(encoding="utf-8"))
    rows = []
    for it in catalog:
        rows += scan_images(it["dest"], it["slug"])
    df = unify_and_clean(rows, min_size=256, csv_out="data/unified_images.csv")
    out_dir = export_clean_256(csv_path="data/unified_images.csv", out_dir="data/clean256", img_size=256)
    return {"ok": True, "rows": len(df), "out_dir": out_dir}

@app.post("/train")
def train():
    """يدرب 3 موديلات ويحفظ أفضل 3 + يصدر TorchScript/ONNX للموديل الأفضل"""
    results = train_all(data_dir="data/clean256")
    return {"ok": True, "results": results}

@app.post("/predict")
async def predict(file: UploadFile = File(...), topk: int = Query(3, ge=1, le=10)):
    """تنبؤ بصورة واحدة (ارفع ملف صورة) — يرجع أفضل topk تصنيفات"""
    image_bytes = await file.read()
    preds, best = predict_bytes(image_bytes, topk=topk)
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
