import io
import json
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import timm
import torch
from PIL import Image

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

def load_best() -> Tuple[torch.nn.Module, List[str], Dict[str, object]]:
    """Load the best trained model and associated metadata.

    Returns:
        Tuple containing the model, list of labels, and metadata for the best
        run.

    Raises:
        FileNotFoundError: If required artifact files are missing.
    """
    results_path = Path("artifacts/finetune_results.json")
    labels_path = Path("artifacts/labels.json")

    if not results_path.exists():
        raise FileNotFoundError("artifacts/finetune_results.json not found. Train the model first.")
    if not labels_path.exists():
        raise FileNotFoundError("artifacts/labels.json not found. Train the model first.")

    results = json.loads(results_path.read_text(encoding="utf-8"))
    best = results[0]
    labels = json.loads(labels_path.read_text(encoding="utf-8"))

    model = timm.create_model(best["model"], pretrained=False, num_classes=len(labels))
    state = torch.load(best["ckpt"], map_location=DEVICE)
    model.load_state_dict(state)
    model.to(DEVICE).eval()
    return model, labels, best

def preprocess_pil(img: Image.Image) -> torch.Tensor:
    """Preprocess a PIL image into a tensor suitable for the model."""
    img = img.convert("RGB").resize((256, 256))
    arr = np.array(img).astype(np.float32) / 255.0
    arr = arr.transpose(2, 0, 1)  # CHW
    tensor = torch.from_numpy(arr).unsqueeze(0)
    return tensor

def predict_bytes(image_bytes: bytes, topk: int = 3) -> Tuple[List[Dict[str, float]], Dict[str, object]]:
    """Run inference on raw image bytes.

    Args:
        image_bytes: Encoded image data.
        topk: Number of top predictions to return.

    Returns:
        A list of predictions and metadata about the best model.
    """
    model, labels, best = load_best()
    img = Image.open(io.BytesIO(image_bytes))
    x = preprocess_pil(img).to(DEVICE)
    with torch.no_grad():
        logits = model(x)
        probs = torch.softmax(logits, dim=1).cpu().numpy()[0]
    idxs = probs.argsort()[::-1][:topk]
    return [{"label": labels[i], "prob": float(probs[i])} for i in idxs], best
