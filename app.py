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

from utils_kaggle import ensure_pkg, ensure_kaggle_token, kaggle_download, huggingface_clone
from prepare_data import scan_images, unify_and_clean, export_clean_256
from train_multi import train_all
from infer import predict_bytes
from floor_plan_analyzer import analyze_floor_plan_bytes, FloorPlanAnalyzer
from alibaba_scraper import AlibabaFurnitureScraper, search_alibaba_furniture

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global model cache
_model_cache = {"model": None, "labels": None, "metadata": None}

app = FastAPI(
    title="Professional Interior Design AI Suite",
    version="2.0.0",
    description="A state-of-the-art interior design classification system powered by deep learning",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS - configure allowed origins via environment variable for production
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
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
            source = item.get("source", "kaggle")  # Default to kaggle for backward compatibility
            
            if source == "huggingface":
                # Clone from Hugging Face
                dataset_id = item["repo_url"]
                huggingface_clone(item["repo_url"], item["dest"], skip_if_exists=skip_if_exists)
            else:
                # Download from Kaggle
                dataset_id = item["slug"]
                kaggle_download(item["slug"], item["dest"], skip_if_exists=skip_if_exists)
            
            if skip_if_exists:
                skipped_count += 1
            else:
                downloaded_count += 1
        except Exception as e:
            logger.error(f"Failed to download {dataset_id}: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to download {dataset_id}: {str(e)}"
            )
    
    logger.info(f"Dataset download completed: {downloaded_count} downloaded, {skipped_count} skipped")
    return {
        "ok": True,
        "message": "All datasets processed successfully",
        "datasets_processed": len(catalog),
        "downloaded": downloaded_count,
        "skipped": skipped_count
    }

@app.post("/clone-deepfurniture", tags=["Data Management"])
def clone_deepfurniture(skip_if_exists: bool = True) -> Dict[str, Any]:
    """Clone the DeepFurniture dataset from Hugging Face.
    
    This endpoint clones the DeepFurniture dataset from Hugging Face using git.
    
    Args:
        skip_if_exists: Skip cloning if the dataset directory already has content.
        
    Returns:
        Dictionary with success status and message.
        
    Raises:
        HTTPException: If git is not available or clone fails.
    """
    logger.info(f"Starting DeepFurniture dataset clone (skip_if_exists={skip_if_exists})")
    
    repo_url = "https://huggingface.co/datasets/byliu/DeepFurniture"
    dest = "data/raw/deepfurniture"
    
    try:
        huggingface_clone(repo_url, dest, skip_if_exists=skip_if_exists)
        logger.info("DeepFurniture dataset clone completed successfully")
        return {
            "ok": True,
            "message": "DeepFurniture dataset cloned successfully",
            "repo_url": repo_url,
            "destination": dest
        }
    except Exception as e:
        logger.error(f"Failed to clone DeepFurniture dataset: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clone DeepFurniture dataset: {str(e)}"
        )

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


@app.post("/analyze-floor-plan", tags=["Floor Plan Analysis"])
async def analyze_floor_plan(
    file: UploadFile = File(..., description="Floor plan image file"),
    save_visualization: bool = Query(False, description="Save annotated visualization")
) -> Dict[str, Any]:
    """Analyze a floor plan image to detect rooms and architectural elements.
    
    This endpoint processes floor plan images to:
    - Detect individual rooms
    - Identify walls, doors, and windows
    - Estimate room types
    - Provide furniture recommendations for each room
    
    Args:
        file: Floor plan image file (JPEG, PNG, etc.)
        save_visualization: Whether to save an annotated visualization
        
    Returns:
        Dictionary with complete floor plan analysis including:
        - Detected rooms with types and dimensions
        - Door and window locations
        - Furniture recommendations per room
        
    Raises:
        HTTPException: If file is invalid or analysis fails.
    """
    if not file.filename:
        logger.error("No filename provided")
        raise HTTPException(
            status_code=400,
            detail="No file provided"
        )
    
    # Validate file type
    allowed_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff'}
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in allowed_extensions:
        logger.error(f"Invalid file type: {file_ext}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed types: {', '.join(allowed_extensions)}"
        )
    
    logger.info(f"Processing floor plan analysis for file: {file.filename}")
    
    try:
        image_bytes = await file.read()
        
        if len(image_bytes) == 0:
            raise HTTPException(
                status_code=400,
                detail="Empty file received"
            )
        
        # Prepare output path if visualization requested
        output_path = None
        if save_visualization:
            Path("artifacts/floor_plans").mkdir(parents=True, exist_ok=True)
            output_path = f"artifacts/floor_plans/analyzed_{Path(file.filename).stem}.jpg"
        
        # Analyze floor plan
        results = analyze_floor_plan_bytes(image_bytes, output_path)
        
        logger.info(f"Floor plan analysis complete. Found {results['total_rooms']} rooms")
        
        response = {
            "ok": True,
            "message": "Floor plan analysis completed successfully",
            "filename": file.filename,
            "analysis": results
        }
        
        if output_path:
            response["visualization_path"] = output_path
        
        return response
        
    except ValueError as e:
        logger.error(f"Invalid floor plan image: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid floor plan image: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Floor plan analysis failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Floor plan analysis failed: {str(e)}"
        )


@app.post("/furniture-recommendations", tags=["Floor Plan Analysis"])
async def get_furniture_recommendations(
    room_type: str = Query(..., description="Type of room (bedroom, living_room, etc.)"),
    area_sqm: float = Query(..., ge=5, le=200, description="Room area in square meters")
) -> Dict[str, Any]:
    """Get furniture recommendations for a specific room type and size.
    
    Args:
        room_type: Type of room (bedroom, living_room, dining_room, kitchen, bathroom)
        area_sqm: Room area in square meters
        
    Returns:
        Dictionary with furniture recommendations
        
    Raises:
        HTTPException: If parameters are invalid
    """
    logger.info(f"Getting furniture recommendations for {room_type} ({area_sqm} sqm)")
    
    # Convert sqm to approximate pixels (rough estimation)
    pixels_per_sqm = 1000  # Rough approximation
    area_pixels = int(area_sqm * pixels_per_sqm)
    
    # Create mock room object
    room = {
        "type": room_type.lower().replace(" ", "_"),
        "area_pixels": area_pixels
    }
    
    try:
        analyzer = FloorPlanAnalyzer()
        recommendations = analyzer.recommend_furniture(room)
        
        logger.info(f"Generated {len(recommendations)} furniture recommendations")
        
        return {
            "ok": True,
            "room_type": room_type,
            "area_sqm": area_sqm,
            "recommendations": recommendations,
            "total_items": len(recommendations)
        }
    except Exception as e:
        logger.error(f"Failed to generate recommendations: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate recommendations: {str(e)}"
        )


@app.post("/alibaba/search", tags=["Alibaba Integration"])
async def search_alibaba(
    keyword: str = Query(..., min_length=2, description="Search keyword for furniture"),
    category: Optional[str] = Query(None, description="Furniture category filter"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price in USD"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price in USD"),
    page: int = Query(1, ge=1, le=10, description="Page number"),
    page_size: int = Query(20, ge=1, le=50, description="Results per page")
) -> Dict[str, Any]:
    """Search for furniture products on Alibaba.
    
    This endpoint searches Alibaba for furniture products with filtering options.
    Results are cached to improve performance and reduce load on Alibaba servers.
    
    Args:
        keyword: Search keyword (e.g., "sofa", "dining table", "office chair")
        category: Optional category filter
        min_price: Minimum price filter in USD
        max_price: Maximum price filter in USD
        page: Page number for pagination
        page_size: Number of results per page
        
    Returns:
        Dictionary with search results including products, pricing, and supplier info
        
    Note:
        This uses simulated data for demonstration. In production:
        - Requires proper Alibaba API credentials or scraping authorization
        - Should implement proxy rotation for large-scale scraping
        - Must comply with Alibaba's terms of service
        
    Raises:
        HTTPException: If search fails or parameters are invalid
    """
    logger.info(f"Searching Alibaba: keyword={keyword}, page={page}")
    
    # Validate price range
    if min_price and max_price and min_price > max_price:
        raise HTTPException(
            status_code=400,
            detail="Minimum price cannot be greater than maximum price"
        )
    
    try:
        scraper = AlibabaFurnitureScraper(rate_limit_seconds=1.0)
        
        results = scraper.search_furniture(
            keyword=keyword,
            category=category,
            min_price=min_price,
            max_price=max_price,
            page=page,
            page_size=page_size,
            use_cache=True
        )
        
        logger.info(f"Found {len(results['products'])} products for '{keyword}'")
        
        return {
            "ok": True,
            "message": "Search completed successfully",
            "query": keyword,
            "category": category,
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Alibaba search failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to search Alibaba: {str(e)}"
        )


@app.get("/alibaba/product/{product_id}", tags=["Alibaba Integration"])
async def get_alibaba_product(
    product_id: str = Path(..., description="Alibaba product ID")
) -> Dict[str, Any]:
    """Get detailed information about a specific Alibaba product.
    
    Args:
        product_id: Unique Alibaba product identifier
        
    Returns:
        Detailed product information including specifications, pricing, and reviews
        
    Raises:
        HTTPException: If product not found or fetch fails
    """
    logger.info(f"Fetching Alibaba product details: {product_id}")
    
    try:
        scraper = AlibabaFurnitureScraper()
        product_details = scraper.get_product_details(product_id)
        
        logger.info(f"Retrieved details for product: {product_id}")
        
        return {
            "ok": True,
            "message": "Product details retrieved successfully",
            "product": product_details
        }
        
    except Exception as e:
        logger.error(f"Failed to fetch product {product_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch product details: {str(e)}"
        )


@app.post("/alibaba/save-products", tags=["Alibaba Integration"])
async def save_alibaba_products(
    keyword: str = Query(..., description="Search keyword to save products for"),
    max_results: int = Query(100, ge=1, le=500, description="Maximum products to save")
) -> Dict[str, Any]:
    """Search and save Alibaba furniture products to a file.
    
    This endpoint searches for products and saves them to a JSON file for later use.
    Useful for building a local furniture catalog from Alibaba.
    
    Args:
        keyword: Search keyword for furniture
        max_results: Maximum number of products to save
        
    Returns:
        Dictionary with save status and file path
        
    Raises:
        HTTPException: If search or save fails
    """
    logger.info(f"Saving Alibaba products: keyword={keyword}, max={max_results}")
    
    try:
        # Search for products
        results = search_alibaba_furniture(
            keyword=keyword,
            max_results=max_results
        )
        
        # Save to file
        scraper = AlibabaFurnitureScraper()
        output_path = scraper.save_products_to_file(
            products=results["products"],
            output_path=f"data/alibaba_{keyword.replace(' ', '_')}.json"
        )
        
        logger.info(f"Saved {len(results['products'])} products to {output_path}")
        
        return {
            "ok": True,
            "message": "Products saved successfully",
            "keyword": keyword,
            "total_saved": len(results["products"]),
            "file_path": output_path
        }
        
    except Exception as e:
        logger.error(f"Failed to save products: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save products: {str(e)}"
        )


@app.get("/alibaba/categories", tags=["Alibaba Integration"])
async def get_alibaba_categories() -> Dict[str, Any]:
    """Get available furniture categories for Alibaba search.
    
    Returns:
        List of available furniture categories
    """
    categories = [
        {"id": "sofa", "name": "Sofas & Couches", "description": "Living room seating"},
        {"id": "table", "name": "Tables", "description": "Dining, coffee, and console tables"},
        {"id": "chair", "name": "Chairs", "description": "Office, dining, and accent chairs"},
        {"id": "bed", "name": "Beds & Frames", "description": "Bedroom furniture"},
        {"id": "wardrobe", "name": "Wardrobes & Closets", "description": "Storage solutions"},
        {"id": "desk", "name": "Desks", "description": "Office and study desks"},
        {"id": "cabinet", "name": "Cabinets", "description": "Storage cabinets and shelving"},
        {"id": "outdoor", "name": "Outdoor Furniture", "description": "Patio and garden furniture"}
    ]
    
    return {
        "ok": True,
        "total_categories": len(categories),
        "categories": categories
    }
