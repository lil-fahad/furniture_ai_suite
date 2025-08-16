import json
import random
from pathlib import Path
from typing import Dict, List, Tuple

import albumentations as A
import numpy as np
import timm
import torch
import yaml
from albumentations.pytorch import ToTensorV2
from torch.utils.data import DataLoader, Dataset
from torchvision import datasets
import torch.nn as nn
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingLR
from tqdm import tqdm

DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'


def set_seed(seed: int) -> None:
    """Seed Python, NumPy and Torch for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def make_transforms() -> Tuple[A.Compose, A.Compose]:
    """Create training and validation augmentation pipelines."""
    train_tf = A.Compose([
        A.HorizontalFlip(p=0.5),
        A.RandomBrightnessContrast(p=0.3),
        A.Affine(
            scale=(0.9, 1.1),
            translate_percent={"x": (-0.05, 0.05), "y": (-0.05, 0.05)},
            rotate=(-10, 10),
            shear={"x": (-5, 5), "y": (-5, 5)},
            p=0.5,
        ),
        ToTensorV2(),
    ])
    val_tf = A.Compose([ToTensorV2()])
    return train_tf, val_tf


class AlbDS(Dataset):
    """Dataset wrapper applying Albumentations transforms."""

    def __init__(self, root: str, t: A.Compose) -> None:
        self.ds = datasets.ImageFolder(root)
        self.t = t

    def __len__(self) -> int:  # pragma: no cover - trivial
        return len(self.ds)

    def __getitem__(self, i: int):  # pragma: no cover - trivial
        x, y = self.ds[i]
        return self.t(image=np.array(x))["image"], y


def evaluate(model: torch.nn.Module, loader: DataLoader) -> float:
    """Evaluate a model on a dataloader and return accuracy."""
    model.eval()
    ys: List[torch.Tensor] = []
    yh: List[torch.Tensor] = []
    with torch.no_grad():
        for x, y in loader:
            x, y = x.to(DEVICE), y.to(DEVICE)
            o = model(x)
            yh.append(o.argmax(1).cpu())
            ys.append(y.cpu())
    yh_cat = torch.cat(yh)
    ys_cat = torch.cat(ys)
    return (yh_cat == ys_cat).float().mean().item()


def train_one(
    backbone: str,
    data_dir: str,
    max_epochs: int,
    patience: int,
    lr: float,
    wd: float,
    batch_size: int,
    num_workers: int,
) -> Dict[str, object]:
    """Train a single backbone and return its best accuracy and checkpoint."""
    train_tf, val_tf = make_transforms()
    tr = DataLoader(
        AlbDS(f"{data_dir}/train", train_tf),
        batch_size=batch_size,
        shuffle=True,
        num_workers=num_workers,
        pin_memory=True,
    )
    va = DataLoader(
        AlbDS(f"{data_dir}/val", val_tf),
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=True,
    )

    classes = sorted([p.name for p in Path(f"{data_dir}/train").iterdir() if p.is_dir()])
    Path("models").mkdir(exist_ok=True, parents=True)
    Path("artifacts").mkdir(exist_ok=True, parents=True)
    with open("artifacts/labels.json", "w", encoding="utf-8") as f:
        json.dump(classes, f, ensure_ascii=False)

    # try pretrained -> fallback
    try:
        model = timm.create_model(backbone, pretrained=True, num_classes=len(classes)).to(DEVICE)
    except Exception as e:  # pragma: no cover - fallback
        print(f"⚠️ Pretrained failed for {backbone}: {e} → random init")
        model = timm.create_model(backbone, pretrained=False, num_classes=len(classes)).to(DEVICE)

    criterion = nn.CrossEntropyLoss()
    optimizer = AdamW(model.parameters(), lr=lr, weight_decay=wd)
    scheduler = CosineAnnealingLR(optimizer, T_max=10)

    best_acc, no_imp = 0.0, 0
    best_path = Path("models") / f"best_{backbone}.pth"

    for ep in range(1, max_epochs + 1):
        model.train()
        ep_loss, steps = 0.0, 0
        for x, y in tr:
            x, y = x.to(DEVICE), y.to(DEVICE)
            optimizer.zero_grad(set_to_none=True)
            o = model(x)
            loss = criterion(o, y)
            loss.backward()
            optimizer.step()
            ep_loss += loss.item()
            steps += 1
        scheduler.step()

        acc = evaluate(model, va)
        print(f"[{backbone}] Epoch {ep}: val_acc={acc:.4f} loss={ep_loss/max(1,steps):.4f}")

        if acc > best_acc:
            best_acc = acc
            no_imp = 0
            torch.save(model.state_dict(), best_path)
        else:
            no_imp += 1
        if no_imp >= patience:
            print(f"[{backbone}] ⏹️ Early stop.")
            break

    return {"model": backbone, "val_acc": float(best_acc), "ckpt": str(best_path)}


def train_all(config_path: str = "model_config.yml") -> List[Dict[str, object]]:
    """Train all models specified in a configuration file."""
    cfg: Dict[str, object] = {}
    if Path(config_path).exists():
        cfg = yaml.safe_load(Path(config_path).read_text(encoding="utf-8")) or {}

    seed = int(cfg.get("seed", 42))
    set_seed(seed)

    data_dir = str(cfg.get("data_dir", "data/clean256"))
    backbones = cfg.get(
        "backbones",
        ["efficientnet_b0", "convnext_tiny", "swin_tiny_patch4_window7_224"],
    )
    batch_size = int(cfg.get("batch_size", 64))
    epochs = int(cfg.get("epochs", 12))
    patience = int(cfg.get("patience", 4))
    lr = float(cfg.get("learning_rate", 3e-4))
    wd = float(cfg.get("weight_decay", 1e-4))
    num_workers = int(cfg.get("num_workers", 2))

    results: List[Dict[str, object]] = []
    for bb in backbones:
        results.append(
            train_one(
                bb,
                data_dir=data_dir,
                max_epochs=epochs,
                patience=patience,
                lr=lr,
                wd=wd,
                batch_size=batch_size,
                num_workers=num_workers,
            )
        )
    results.sort(key=lambda x: x["val_acc"], reverse=True)
    Path("artifacts").mkdir(parents=True, exist_ok=True)
    (Path("artifacts") / "finetune_results.json").write_text(
        json.dumps(results, indent=2, ensure_ascii=False)
    )
    # export best
    best = results[0]
    classes = json.loads((Path("artifacts") / "labels.json").read_text(encoding="utf-8"))
    model = timm.create_model(best["model"], pretrained=False, num_classes=len(classes))
    model.load_state_dict(torch.load(best["ckpt"], map_location=DEVICE))
    model.to(DEVICE).eval()

    ex = torch.randn(1, 3, 256, 256).to(DEVICE)
    traced = torch.jit.trace(model, ex)
    traced.save("artifacts/model.ts")

    import torch.onnx  # noqa: WPS433

    torch.onnx.export(
        model,
        ex,
        "artifacts/model.onnx",
        input_names=["input"],
        output_names=["logits"],
        opset_version=13,
    )
    print("✅ Exported:", best["ckpt"], "→ artifacts/model.ts, artifacts/model.onnx")

    return results
