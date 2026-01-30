"""Multi-model training module for interior design classification.

This module handles training multiple state-of-the-art deep learning models
and selecting the best performing one based on validation accuracy.
"""
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
from typing import Tuple, Dict, List, Union
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'
logger.info(f"Training will use device: {DEVICE}")


def make_transforms() -> Tuple[A.Compose, A.Compose]:
    """Create training and validation augmentation pipelines.
    
    Training augmentations include:
        - Horizontal flips
        - Brightness/contrast adjustments
        - Affine transformations (scale, translate, rotate, shear)
    
    Validation only applies normalization.
    
    Returns:
        Tuple of (train_transform, val_transform)
    """
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
    
    logger.info("Created augmentation pipelines")
    return train_tf, val_tf

class AlbDS(Dataset):
    """Dataset wrapper applying Albumentations to ImageFolder.
    
    This class wraps torchvision's ImageFolder and applies Albumentations
    transformations for data augmentation.
    """

    def __init__(self, root: str, t: A.Compose) -> None:
        """Initialize dataset with root directory and transform.
        
        Args:
            root: Path to image directory organized in class folders
            t: Albumentations transform to apply
        """
        self.ds = datasets.ImageFolder(root)
        self.t = t
        logger.info(f"Created dataset from {root} with {len(self.ds)} samples")

    def __len__(self) -> int:
        """Return number of samples in the dataset."""
        return len(self.ds)

    def __getitem__(self, i: int) -> Tuple[torch.Tensor, int]:
        """Return transformed image tensor and label.
        
        Args:
            i: Index of the sample
            
        Returns:
            Tuple of (transformed_image, label)
        """
        x, y = self.ds[i]
        return self.t(image=np.array(x))['image'], y


def evaluate(model: nn.Module, loader: DataLoader) -> float:
    """Compute accuracy of model over a dataloader.
    
    Args:
        model: PyTorch model to evaluate
        loader: DataLoader with validation data
        
    Returns:
        Accuracy as a float between 0 and 1
    """
    model.eval()
    ys = []
    yh = []
    
    with torch.no_grad():
        for x, y in loader:
            x, y = x.to(DEVICE), y.to(DEVICE)
            o = model(x)
            yh.append(o.argmax(1).cpu())
            ys.append(y.cpu())
    
    yh = torch.cat(yh)
    ys = torch.cat(ys)
    acc = (yh == ys).float().mean().item()
    
    return acc

def train_one(
    backbone: str,
    data_dir: str = "data/clean256",
    max_epochs: int = 12,
    patience: int = 4,
    lr: float = 3e-4,
    wd: float = 1e-4,
    batch_size: int = 64,
    num_workers: int = 2
) -> Dict[str, Union[float, str]]:
    """Fine-tune a single backbone on the dataset.
    
    Args:
        backbone: Name of the timm model to use
        data_dir: Path to dataset directory with train/val splits
        max_epochs: Maximum number of training epochs
        patience: Early stopping patience (epochs without improvement)
        lr: Learning rate
        wd: Weight decay
        batch_size: Batch size for training
        num_workers: Number of data loading workers
        
    Returns:
        Dictionary with model name, validation accuracy, and checkpoint path
        
    Raises:
        FileNotFoundError: If data directory doesn't exist
        Exception: If training fails
    """
    logger.info(f"Starting training for {backbone}")
    logger.info(f"Configuration: lr={lr}, wd={wd}, max_epochs={max_epochs}, patience={patience}")
    
    # Create transforms
    train_tf, val_tf = make_transforms()
    
    # Create dataloaders
    train_path = f'{data_dir}/train'
    val_path = f'{data_dir}/val'
    
    if not Path(train_path).exists() or not Path(val_path).exists():
        raise FileNotFoundError(f"Training or validation directory not found in {data_dir}")
    
    tr = DataLoader(
        AlbDS(train_path, train_tf),
        batch_size=batch_size,
        shuffle=True,
        num_workers=num_workers,
        pin_memory=True
    )
    va = DataLoader(
        AlbDS(val_path, val_tf),
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=True
    )

    # Get class names and save labels
    classes = sorted([p.name for p in Path(train_path).iterdir() if p.is_dir()])
    logger.info(f"Found {len(classes)} classes: {', '.join(classes[:5])}{'...' if len(classes) > 5 else ''}")
    
    Path("models").mkdir(exist_ok=True, parents=True)
    Path("artifacts").mkdir(exist_ok=True, parents=True)
    
    with open("artifacts/labels.json", "w", encoding="utf-8") as f:
        json.dump(classes, f, ensure_ascii=False, indent=2)

    # Create model - try pretrained, fallback to random init
    try:
        model = timm.create_model(backbone, pretrained=True, num_classes=len(classes)).to(DEVICE)
        logger.info(f"Created {backbone} with pretrained weights")
    except Exception as e:
        logger.warning(f"Pretrained weights failed for {backbone}: {e}. Using random initialization.")
        model = timm.create_model(backbone, pretrained=False, num_classes=len(classes)).to(DEVICE)

    criterion = nn.CrossEntropyLoss()
    optimizer = AdamW(model.parameters(), lr=lr, weight_decay=wd)
    scheduler = CosineAnnealingLR(optimizer, T_max=10)

    best_acc = 0.0
    no_imp = 0
    best_path = Path("models") / f"best_{backbone}.pth"

    # Training loop
    for ep in range(1, max_epochs + 1):
        model.train()
        ep_loss = 0.0
        steps = 0
        
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

        # Evaluate
        acc = evaluate(model, va)
        avg_loss = ep_loss / max(1, steps)
        logger.info(f"[{backbone}] Epoch {ep}/{max_epochs}: val_acc={acc:.4f}, train_loss={avg_loss:.4f}")

        # Save best model
        if acc > best_acc:
            best_acc = acc
            no_imp = 0
            torch.save(model.state_dict(), best_path)
            logger.info(f"[{backbone}] New best accuracy: {best_acc:.4f} - model saved")
        else:
            no_imp += 1
        
        # Early stopping
        if no_imp >= patience:
            logger.info(f"[{backbone}] Early stopping triggered after {ep} epochs")
            break

    logger.info(f"[{backbone}] Training completed. Best accuracy: {best_acc:.4f}")
    return {
        "model": backbone,
        "val_acc": float(best_acc),
        "ckpt": str(best_path),
        "epochs_trained": ep
    }

def train_all(
    data_dir: str = "data/clean256",
    backbones: List[str] = None
) -> List[Dict[str, Union[float, str]]]:
    """Train multiple backbones and export the best model.
    
    This function trains multiple deep learning models, compares their performance,
    and exports the best one in multiple formats (PyTorch, TorchScript, ONNX).
    
    Args:
        data_dir: Path to prepared dataset directory
        backbones: List of model architectures to train. If None, uses default set.
        
    Returns:
        List of training results sorted by validation accuracy (best first)
        
    Raises:
        Exception: If training or export fails
    """
    if backbones is None:
        backbones = [
            "efficientnet_b0",
            "convnext_tiny",
            "swin_tiny_patch4_window7_224"
        ]
    
    logger.info(f"Training {len(backbones)} models: {', '.join(backbones)}")
    
    results: List[Dict[str, Union[float, str]]] = []
    
    for bb in backbones:
        try:
            result = train_one(bb, data_dir=data_dir)
            results.append(result)
        except Exception as e:
            logger.error(f"Failed to train {bb}: {str(e)}")
            # Continue with other models even if one fails
            continue
    
    if not results:
        raise Exception("All model training failed")
    
    # Sort by validation accuracy (best first)
    results.sort(key=lambda x: x["val_acc"], reverse=True)
    
    # Save results
    Path("artifacts").mkdir(parents=True, exist_ok=True)
    results_path = Path("artifacts") / "finetune_results.json"
    results_path.write_text(json.dumps(results, indent=2, ensure_ascii=False))
    logger.info(f"Training results saved to {results_path}")
    
    # Log summary
    logger.info("=" * 60)
    logger.info("TRAINING SUMMARY")
    logger.info("=" * 60)
    for i, r in enumerate(results, 1):
        logger.info(f"{i}. {r['model']}: {r['val_acc']:.4f} accuracy")
    logger.info("=" * 60)
    
    # Export best model
    best = results[0]
    logger.info(f"Exporting best model: {best['model']} with accuracy {best['val_acc']:.4f}")
    
    try:
        # Load labels and model
        labels = json.loads((Path("artifacts") / "labels.json").read_text(encoding="utf-8"))
        model = timm.create_model(best["model"], pretrained=False, num_classes=len(labels))
        model.load_state_dict(torch.load(best["ckpt"], map_location=DEVICE))
        model.to(DEVICE).eval()

        # Export TorchScript
        ex = torch.randn(1, 3, 256, 256).to(DEVICE)
        traced = torch.jit.trace(model, ex)
        torchscript_path = "artifacts/model.ts"
        traced.save(torchscript_path)
        logger.info(f"Exported TorchScript model to {torchscript_path}")

        # Export ONNX
        import torch.onnx
        onnx_path = "artifacts/model.onnx"
        torch.onnx.export(
            model,
            ex,
            onnx_path,
            input_names=["input"],
            output_names=["logits"],
            opset_version=13,
            dynamic_axes={
                'input': {0: 'batch_size'},
                'logits': {0: 'batch_size'}
            }
        )
        logger.info(f"Exported ONNX model to {onnx_path}")
        
        logger.info("=" * 60)
        logger.info("MODEL EXPORT COMPLETE")
        logger.info(f"PyTorch checkpoint: {best['ckpt']}")
        logger.info(f"TorchScript: {torchscript_path}")
        logger.info(f"ONNX: {onnx_path}")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Failed to export models: {str(e)}")
        raise

    return results
