"""Inference module for interior design classification.

This module handles loading trained models and making predictions on new images.
"""
import io
import json
import torch
import timm
import numpy as np
from pathlib import Path
from PIL import Image
import torch.nn as nn
from typing import Tuple, List, Dict, Union
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'
logger.info(f"Using device: {DEVICE}")

# Global model cache
_cached_model = None
_cached_labels = None
_cached_metadata = None


def load_best(use_cache: bool = True) -> Tuple[nn.Module, List[str], Dict[str, Union[float, str]]]:
    """Load the best trained model and associated labels.
    
    Args:
        use_cache: Whether to use cached model if available
    
    Returns:
        Tuple containing:
            - Loaded PyTorch model
            - List of class labels
            - Dictionary with model metadata
            
    Raises:
        FileNotFoundError: If model files don't exist.
        Exception: If model loading fails.
    """
    global _cached_model, _cached_labels, _cached_metadata
    
    # Return cached model if available and caching is enabled
    if use_cache and _cached_model is not None:
        logger.debug("Using cached model")
        return _cached_model, _cached_labels, _cached_metadata
    
    results_path = Path("artifacts/finetune_results.json")
    labels_path = Path("artifacts/labels.json")
    
    if not results_path.exists():
        raise FileNotFoundError(
            "Training results not found at artifacts/finetune_results.json. "
            "Please train the model first."
        )
    
    if not labels_path.exists():
        raise FileNotFoundError(
            "Labels not found at artifacts/labels.json. "
            "Please train the model first."
        )

    try:
        results = json.loads(results_path.read_text(encoding="utf-8"))
        labels = json.loads(labels_path.read_text(encoding="utf-8"))
        
        if not results:
            raise ValueError("No trained models found in results")
        
        best = results[0]
        logger.info(f"Loading best model: {best['model']} with accuracy {best.get('val_acc', 'N/A')}")
        
        model = timm.create_model(best["model"], pretrained=False, num_classes=len(labels))
        
        checkpoint_path = Path(best["ckpt"])
        if not checkpoint_path.exists():
            raise FileNotFoundError(f"Model checkpoint not found: {checkpoint_path}")
        
        state = torch.load(checkpoint_path, map_location=DEVICE)
        model.load_state_dict(state)
        model.to(DEVICE).eval()
        
        # Cache the model
        if use_cache:
            _cached_model = model
            _cached_labels = labels
            _cached_metadata = best
        
        logger.info("Model loaded successfully")
        return model, labels, best
    
    except json.JSONDecodeError as e:
        raise Exception(f"Failed to parse JSON files: {str(e)}")
    except Exception as e:
        raise Exception(f"Failed to load model: {str(e)}")

def preprocess_pil(img: Image.Image, size: int = 256) -> torch.Tensor:
    """Convert a PIL image to a normalized tensor.
    
    Args:
        img: PIL Image to preprocess
        size: Target size for resizing (default: 256)
        
    Returns:
        Preprocessed image tensor ready for model input
        
    Raises:
        ValueError: If image cannot be processed
    """
    # ImageNet mean and std for normalization (must match training)
    mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
    std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
    
    try:
        # Convert to RGB and resize (using LANCZOS for compatibility)
        img = img.convert('RGB').resize((size, size), Image.LANCZOS)
        
        # Convert to array and normalize to [0, 1]
        arr = np.array(img).astype(np.float32) / 255.0
        
        # Apply ImageNet normalization
        arr = (arr - mean) / std
        
        # Transpose to CHW format
        arr = arr.transpose(2, 0, 1)
        
        # Convert to tensor and add batch dimension
        tensor = torch.from_numpy(arr).unsqueeze(0)
        
        return tensor
    except Exception as e:
        raise ValueError(f"Failed to preprocess image: {str(e)}")


def predict_bytes(
    image_bytes: bytes,
    topk: int = 3
) -> Tuple[List[Dict[str, Union[float, str]]], Dict[str, Union[float, str]]]:
    """Predict top-k labels for raw image bytes.
    
    Args:
        image_bytes: Raw bytes of the image file
        topk: Number of top predictions to return
        
    Returns:
        Tuple containing:
            - List of predictions with labels and probabilities
            - Metadata about the model used
            
    Raises:
        ValueError: If image cannot be opened or processed
        FileNotFoundError: If model files don't exist
    """
    if not image_bytes:
        raise ValueError("Empty image bytes provided")
    
    if topk < 1:
        raise ValueError("topk must be at least 1")
    
    try:
        model, labels, best = load_best()
        
        # Open and validate image
        img = Image.open(io.BytesIO(image_bytes))
        
        if img.width < 32 or img.height < 32:
            raise ValueError(f"Image too small: {img.width}x{img.height}. Minimum size is 32x32")
        
        logger.info(f"Processing image of size {img.width}x{img.height}")
        
        # Preprocess and predict
        x = preprocess_pil(img).to(DEVICE)
        
        with torch.no_grad():
            logits = model(x)
            probs = torch.softmax(logits, dim=1).cpu().numpy()[0]
        
        # Get top-k predictions
        topk = min(topk, len(labels))  # Ensure topk doesn't exceed number of labels
        idxs = probs.argsort()[::-1][:topk]
        
        predictions = [
            {
                "label": labels[i],
                "confidence": float(probs[i]),
                "rank": rank + 1
            }
            for rank, i in enumerate(idxs)
        ]
        
        logger.info(f"Prediction complete. Top result: {predictions[0]['label']} ({predictions[0]['confidence']:.4f})")
        
        return predictions, best
        
    except FileNotFoundError:
        raise
    except Exception as e:
        raise Exception(f"Prediction failed: {str(e)}")
