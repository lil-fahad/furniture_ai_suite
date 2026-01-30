"""Professional Interior Design AI Suite API.

This application provides a comprehensive solution for interior design classification
using state-of-the-art deep learning models. It handles the complete workflow from
data acquisition to model training and inference.
"""
from fastapi import FastAPI, UploadFile, File, Query, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import json
import os
import logging
from typing import Dict, Any, List

import httpx

from utils_kaggle import ensure_pkg, ensure_kaggle_token, kaggle_download
from prepare_data import scan_images, unify_and_clean, export_clean_256
from train_multi import train_all
from infer import predict_bytes

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Professional Interior Design AI Suite",
    version="2.0.0",
    description="A state-of-the-art interior design classification system powered by deep learning",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS for better API accessibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health", tags=["System"])
def health() -> Dict[str, str]:
    """Health check endpoint to verify API is running.
    
    Returns:
        Dictionary with status information.
    """
    logger.info("Health check requested")
    return {
        "status": "healthy",
        "service": "Interior Design AI Suite",
        "version": "2.0.0"
    }


@app.get("/github-user", tags=["System"])
def github_user() -> Dict[str, Any]:
    """Fetch the authenticated GitHub user using a token from the environment.
    
    Returns:
        Dictionary with user information or error details.
        
    Raises:
        HTTPException: If the GitHub token is not set or the request fails.
    """
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        logger.error("GITHUB_TOKEN environment variable not set")
        raise HTTPException(
            status_code=500,
            detail="GITHUB_TOKEN not set in environment variables"
        )

    headers = {"Authorization": f"token {token}"}
    try:
        resp = httpx.get("https://api.github.com/user", headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        logger.info(f"Successfully fetched GitHub user: {data.get('login')}")
        return {"ok": True, "login": data.get("login"), "name": data.get("name")}
    except httpx.HTTPError as e:
        logger.error(f"Failed to fetch GitHub user: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch GitHub user: {str(e)}"
        )

@app.post("/download", tags=["Data Management"])
def download_all(skip_if_exists: bool = True) -> Dict[str, Any]:
    """Download all datasets from the catalog.
    
    This endpoint downloads furniture and interior design datasets from Kaggle
    as specified in datasets_catalog.json.
    
    Args:
        skip_if_exists: Skip downloading if the dataset directory already has content.
        
    Returns:
        Dictionary with success status and message.
        
    Raises:
        HTTPException: If kaggle package is not installed or download fails.
    """
    logger.info(f"Starting dataset download (skip_if_exists={skip_if_exists})")
    
    try:
        ensure_pkg("kaggle")
    except ImportError as e:
        logger.error(f"Kaggle package not available: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Kaggle package is required. Please install it: pip install kaggle. Error: {str(e)}"
        )

    try:
        ensure_kaggle_token()
    except FileNotFoundError as e:
        logger.error(f"Kaggle token not found: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

    catalog_path = Path("datasets_catalog.json")
    if not catalog_path.exists():
        logger.error("datasets_catalog.json not found")
        raise HTTPException(
            status_code=500,
            detail="datasets_catalog.json not found in project root"
        )
    
    try:
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in datasets_catalog.json: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Invalid JSON in datasets_catalog.json: {str(e)}"
        )
    
    downloaded_count = 0
    skipped_count = 0
    
    for item in catalog:
        try:
            kaggle_download(item["slug"], item["dest"], skip_if_exists=skip_if_exists)
            if skip_if_exists:
                skipped_count += 1
            else:
                downloaded_count += 1
        except Exception as e:
            logger.error(f"Failed to download {item['slug']}: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to download {item['slug']}: {str(e)}"
            )
    
    logger.info(f"Dataset download completed: {downloaded_count} downloaded, {skipped_count} skipped")
    return {
        "ok": True,
        "message": "All datasets processed successfully",
        "datasets_processed": len(catalog),
        "downloaded": downloaded_count,
        "skipped": skipped_count
    }

@app.post("/prepare", tags=["Data Management"])
def prepare() -> Dict[str, Any]:
    """Prepare and process image datasets for training.
    
    This endpoint scans images from downloaded datasets, validates them,
    removes duplicates, and exports clean resized images in train/val splits.
    
    Returns:
        Dictionary with processing results including row count and output directory.
        
    Raises:
        HTTPException: If catalog is missing or data preparation fails.
    """
    logger.info("Starting data preparation")
    
    catalog_path = Path("datasets_catalog.json")
    if not catalog_path.exists():
        logger.error("datasets_catalog.json not found")
        raise HTTPException(
            status_code=500,
            detail="datasets_catalog.json not found. Please ensure it exists in project root."
        )
    
    try:
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in catalog: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Invalid JSON in datasets_catalog.json: {str(e)}"
        )
    
    try:
        rows = []
        for it in catalog:
            dest_path = Path(it["dest"])
            if not dest_path.exists():
                logger.warning(f"Dataset directory not found: {it['dest']}")
                continue
            logger.info(f"Scanning images from {it['slug']}")
            rows += scan_images(it["dest"], it["slug"])
        
        if not rows:
            logger.error("No images found in any dataset")
            raise HTTPException(
                status_code=500,
                detail="No images found. Please download datasets first using /download endpoint."
            )
        
        logger.info(f"Found {len(rows)} images, starting validation and cleaning")
        df = unify_and_clean(rows, min_size=256, csv_out="data/unified_images.csv")
        
        logger.info(f"Exporting {len(df)} clean images")
        out_dir = export_clean_256(
            csv_path="data/unified_images.csv",
            out_dir="data/clean256",
            img_size=256
        )
        
        logger.info(f"Data preparation completed: {len(df)} images exported to {out_dir}")
        return {
            "ok": True,
            "message": "Data preparation completed successfully",
            "total_images_found": len(rows),
            "valid_images": len(df),
            "output_directory": out_dir
        }
    except Exception as e:
        logger.error(f"Data preparation failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Data preparation failed: {str(e)}"
        )

@app.post("/train", tags=["Model Training"])
def train() -> Dict[str, Any]:
    """Train multiple deep learning models on the prepared dataset.
    
    This endpoint trains multiple state-of-the-art models (EfficientNet, ConvNeXt, Swin Transformer)
    and exports the best performing model in multiple formats (PyTorch, TorchScript, ONNX).
    
    Returns:
        Dictionary with training results for all models.
        
    Raises:
        HTTPException: If training data is not prepared or training fails.
    """
    logger.info("Starting model training")
    
    data_dir = Path("data/clean256")
    if not data_dir.exists():
        logger.error("Training data directory not found")
        raise HTTPException(
            status_code=500,
            detail="Training data not found. Please run /prepare endpoint first to prepare the dataset."
        )
    
    train_dir = data_dir / "train"
    val_dir = data_dir / "val"
    
    if not train_dir.exists() or not val_dir.exists():
        logger.error("Train or validation directory missing")
        raise HTTPException(
            status_code=500,
            detail="Training or validation directory missing. Please run /prepare endpoint."
        )
    
    try:
        logger.info("Training models - this may take a while...")
        results = train_all(data_dir="data/clean256")
        
        logger.info(f"Training completed. Best model: {results[0]['model']} with accuracy {results[0]['val_acc']:.4f}")
        return {
            "ok": True,
            "message": "Model training completed successfully",
            "results": results,
            "best_model": results[0]["model"],
            "best_accuracy": results[0]["val_acc"]
        }
    except Exception as e:
        logger.error(f"Model training failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Model training failed: {str(e)}"
        )

@app.post("/predict", tags=["Inference"])
async def predict(
    file: UploadFile = File(..., description="Image file to classify"),
    topk: int = Query(3, ge=1, le=10, description="Number of top predictions to return")
) -> Dict[str, Any]:
    """Predict interior design category for an uploaded image.
    
    This endpoint accepts an image file and returns the top-k predicted categories
    with their confidence scores using the best trained model.
    
    Args:
        file: Image file to classify (JPEG, PNG, etc.)
        topk: Number of top predictions to return (1-10)
        
    Returns:
        Dictionary with predictions and model information.
        
    Raises:
        HTTPException: If model is not trained or prediction fails.
    """
    if not file.filename:
        logger.error("No filename provided")
        raise HTTPException(
            status_code=400,
            detail="No file provided"
        )
    
    # Validate file type
    allowed_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.webp'}
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in allowed_extensions:
        logger.error(f"Invalid file type: {file_ext}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed types: {', '.join(allowed_extensions)}"
        )
    
    logger.info(f"Processing prediction for file: {file.filename}")
    
    try:
        image_bytes = await file.read()
        
        if len(image_bytes) == 0:
            raise HTTPException(
                status_code=400,
                detail="Empty file received"
            )
        
        preds, best = predict_bytes(image_bytes, topk=topk)
        
        logger.info(f"Prediction successful. Top prediction: {preds[0]['label']} ({preds[0]['prob']:.4f})")
        
        return {
            "ok": True,
            "message": "Prediction completed successfully",
            "model": best["model"],
            "model_accuracy": best.get("val_acc", "N/A"),
            "predictions": preds,
            "top_prediction": preds[0] if preds else None
        }
    except FileNotFoundError as e:
        logger.error(f"Model not found: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Model not trained yet. Please run /train endpoint first."
        )
    except Exception as e:
        logger.error(f"Prediction failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Prediction failed: {str(e)}"
        )

@app.get("/labels", tags=["Information"])
def labels() -> Dict[str, Any]:
    """Get the list of interior design categories.
    
    Returns all possible classification labels that the model can predict.
    
    Returns:
        Dictionary with list of labels.
        
    Raises:
        HTTPException: If labels file doesn't exist (model not trained).
    """
    logger.info("Fetching labels")
    p = Path("artifacts/labels.json")
    
    if not p.exists():
        logger.error("Labels file not found")
        raise HTTPException(
            status_code=404,
            detail="Labels not found. Please train the model first using /train endpoint."
        )
    
    try:
        labels_list = json.loads(p.read_text(encoding="utf-8"))
        logger.info(f"Retrieved {len(labels_list)} labels")
        return {
            "ok": True,
            "count": len(labels_list),
            "labels": labels_list
        }
    except Exception as e:
        logger.error(f"Failed to read labels: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to read labels: {str(e)}"
        )

@app.get("/results", tags=["Information"])
def results() -> Dict[str, Any]:
    """Get training results for all models.
    
    Returns performance metrics for all trained models, sorted by validation accuracy.
    
    Returns:
        Dictionary with training results.
        
    Raises:
        HTTPException: If results file doesn't exist (model not trained).
    """
    logger.info("Fetching training results")
    p = Path("artifacts/finetune_results.json")
    
    if not p.exists():
        logger.error("Training results not found")
        raise HTTPException(
            status_code=404,
            detail="Training results not found. Please train the model first using /train endpoint."
        )
    
    try:
        results_data = json.loads(p.read_text(encoding="utf-8"))
        logger.info(f"Retrieved results for {len(results_data)} models")
        return {
            "ok": True,
            "count": len(results_data),
            "models": results_data,
            "best_model": results_data[0] if results_data else None
        }
    except Exception as e:
        logger.error(f"Failed to read results: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to read results: {str(e)}"
        )
