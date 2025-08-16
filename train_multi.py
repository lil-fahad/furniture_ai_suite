import json
import torch
import timm
import numpy as np
from pathlib import Path
from tqdm import tqdm
import albumentations as A
from albumentations.pytorch import ToTensorV2
from torchvision import datasets
from torch.utils.data import DataLoader, Dataset
import torch.nn as nn
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingLR
from sklearn.metrics import classification_report, confusion_matrix

DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'

def make_transforms() -> tuple[A.Compose, A.Compose]:
    """Return training and validation augmentation pipelines."""
    train_tf = A.Compose([
        A.HorizontalFlip(p=0.5),
        A.RandomBrightnessContrast(p=0.3),
        A.Affine(
            scale=(0.9, 1.1),
            translate_percent={"x": (-0.05, 0.05), "y": (-0.05, 0.05)},
            rotate=(-10, 10),
            shear={"x": (-5, 5), "y": (-5, 5)},
            p=0.5
        ),
        ToTensorV2()
    ])
    val_tf = A.Compose([ToTensorV2()])
    return train_tf, val_tf

class AlbDS(Dataset):
    """Dataset wrapper applying Albumentations to ImageFolder."""

    def __init__(self, root: str, t: A.Compose) -> None:
        """Initialize dataset with root directory and transform."""
        self.ds = datasets.ImageFolder(root)
        self.t = t

    def __len__(self) -> int:
        """Return number of samples."""
        return len(self.ds)

    def __getitem__(self, i: int) -> tuple[torch.Tensor, int]:
        """Return transformed image tensor and label."""
        x, y = self.ds[i]
        return self.t(image=np.array(x))['image'], y

def evaluate(model: nn.Module, loader: DataLoader) -> float:
    """Compute accuracy of ``model`` over a dataloader."""
    model.eval(); ys = []; yh = []
    with torch.no_grad():
        for x, y in loader:
            x, y = x.to(DEVICE), y.to(DEVICE)
            o = model(x); yh.append(o.argmax(1).cpu()); ys.append(y.cpu())
    yh = torch.cat(yh); ys = torch.cat(ys)
    acc = (yh == ys).float().mean().item()
    return acc

def train_one(
    backbone: str,
    data_dir: str = "data/clean256",
    max_epochs: int = 12,
    patience: int = 4,
    lr: float = 3e-4,
    wd: float = 1e-4,
) -> dict[str, float | str]:
    """Fine-tune a single backbone on the dataset."""
    train_tf, val_tf = make_transforms()
    tr = DataLoader(AlbDS(f'{data_dir}/train', train_tf), batch_size=64, shuffle=True,  num_workers=2, pin_memory=True)
    va = DataLoader(AlbDS(f'{data_dir}/val',   val_tf),   batch_size=64, shuffle=False, num_workers=2, pin_memory=True)

    classes = sorted([p.name for p in Path(f'{data_dir}/train').iterdir() if p.is_dir()])
    Path("models").mkdir(exist_ok=True, parents=True)
    Path("artifacts").mkdir(exist_ok=True, parents=True)
    with open("artifacts/labels.json", "w", encoding="utf-8") as f:
        json.dump(classes, f, ensure_ascii=False)

    # try pretrained -> fallback
    try:
        model = timm.create_model(backbone, pretrained=True, num_classes=len(classes)).to(DEVICE)
    except Exception as e:
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
            o = model(x); loss = criterion(o, y)
            loss.backward(); optimizer.step()
            ep_loss += loss.item(); steps += 1
        scheduler.step()

        acc = evaluate(model, va)
        print(f"[{backbone}] Epoch {ep}: val_acc={acc:.4f} loss={ep_loss/max(1,steps):.4f}")

        if acc > best_acc:
            best_acc = acc; no_imp = 0
            torch.save(model.state_dict(), best_path)
        else:
            no_imp += 1
        if no_imp >= patience:
            print(f"[{backbone}] ⏹️ Early stop.")
            break

    return {"model": backbone, "val_acc": float(best_acc), "ckpt": str(best_path)}

def train_all(data_dir: str = "data/clean256") -> list[dict[str, float | str]]:
    """Train multiple backbones and export the best model."""
    backbones = ["efficientnet_b0", "convnext_tiny", "swin_tiny_patch4_window7_224"]
    results: list[dict[str, float | str]] = []
    for bb in backbones:
        results.append(train_one(bb, data_dir=data_dir))
    results.sort(key=lambda x: x["val_acc"], reverse=True)
    Path("artifacts").mkdir(parents=True, exist_ok=True)
    (Path("artifacts")/"finetune_results.json").write_text(json.dumps(results, indent=2, ensure_ascii=False))
    # export best
    best = results[0]
    classes = json.loads((Path("artifacts")/"labels.json").read_text(encoding="utf-8"))
    model = timm.create_model(best["model"], pretrained=False, num_classes=len(classes))
    model.load_state_dict(torch.load(best["ckpt"], map_location=DEVICE))
    model.to(DEVICE).eval()

    ex = torch.randn(1, 3, 256, 256).to(DEVICE)
    traced = torch.jit.trace(model, ex); traced.save("artifacts/model.ts")

    import torch.onnx
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
