import io
import json
import torch
import timm
import numpy as np
from pathlib import Path
from PIL import Image
import torch.nn as nn

DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'

def load_best() -> tuple[nn.Module, list[str], dict[str, float | str]]:
    """Load the best trained model and associated labels."""
    results_path = Path("artifacts/finetune_results.json")
    labels_path = Path("artifacts/labels.json")
    assert results_path.exists() and labels_path.exists(), "لم يتم العثور على نتائج التدريب/الملصقات."

    results = json.loads(results_path.read_text(encoding="utf-8"))
    best = results[0]
    labels = json.loads(labels_path.read_text(encoding="utf-8"))

    model = timm.create_model(best["model"], pretrained=False, num_classes=len(labels))
    state = torch.load(best["ckpt"], map_location=DEVICE)
    model.load_state_dict(state)
    model.to(DEVICE).eval()
    return model, labels, best

def preprocess_pil(img: Image.Image) -> torch.Tensor:
    """Convert a PIL image to a normalized tensor."""
    img = img.convert('RGB').resize((256, 256))
    arr = np.array(img).astype(np.float32) / 255.0
    arr = arr.transpose(2, 0, 1)  # CHW
    tensor = torch.from_numpy(arr).unsqueeze(0)
    return tensor

def predict_bytes(image_bytes: bytes, topk: int = 3) -> tuple[list[dict[str, float | str]], dict[str, float | str]]:
    """Predict top-k labels for raw image bytes."""
    model, labels, best = load_best()
    img = Image.open(io.BytesIO(image_bytes))
    x = preprocess_pil(img).to(DEVICE)
    with torch.no_grad():
        logits = model(x)
        probs = torch.softmax(logits, dim=1).cpu().numpy()[0]
    idxs = probs.argsort()[::-1][:topk]
    return [{"label": labels[i], "prob": float(probs[i])} for i in idxs], best
