"""HuggingFace Streaming Dataset Module for Furniture AI Suite.

This module provides functionality to load public furniture datasets from
HuggingFace Hub in streaming mode without downloading or caching locally.
The data is processed on-the-fly for model training.

Example usage:
    >>> from hf_streaming_dataset import create_streaming_dataloader
    >>> train_loader = create_streaming_dataloader(
    ...     dataset_name="huggan/smithsonian_butterflies_subset",
    ...     split="train",
    ...     batch_size=32
    ... )
    >>> for batch in train_loader:
    ...     images, labels = batch
    ...     # Train model
"""
import io
import logging
from typing import Optional, Tuple, Iterator, Callable, Dict, Any

import numpy as np
import torch
from torch.utils.data import IterableDataset, DataLoader
from PIL import Image

try:
    from datasets import load_dataset, IterableDataset as HFIterableDataset
    HF_DATASETS_AVAILABLE = True
except ImportError:
    HF_DATASETS_AVAILABLE = False

try:
    import albumentations as A
    from albumentations.pytorch import ToTensorV2
    ALBUMENTATIONS_AVAILABLE = True
except ImportError:
    ALBUMENTATIONS_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Example streaming datasets for testing
# Note: Add furniture-specific datasets from HuggingFace when available
DEFAULT_EXAMPLE_DATASETS = [
    "cifar10",  # Small dataset for testing streaming
    "food101",  # Large image dataset for testing
]


def get_default_transform() -> Callable:
    """Create default image transformation pipeline.
    
    Returns:
        Albumentations transform or fallback torchvision-style transform
    """
    if ALBUMENTATIONS_AVAILABLE:
        return A.Compose([
            A.Resize(256, 256),
            A.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
            ToTensorV2()
        ])
    else:
        # Fallback to manual normalization
        def manual_transform(image: np.ndarray) -> torch.Tensor:
            """Apply basic transform without albumentations."""
            from PIL import Image as PILImage
            if isinstance(image, PILImage.Image):
                image = image.resize((256, 256))
                image = np.array(image)
            
            # Normalize to [0, 1] then apply ImageNet stats
            image = image.astype(np.float32) / 255.0
            mean = np.array([0.485, 0.456, 0.406])
            std = np.array([0.229, 0.224, 0.225])
            image = (image - mean) / std
            
            # HWC -> CHW
            image = np.transpose(image, (2, 0, 1))
            return torch.from_numpy(image).float()
        
        return manual_transform


class HFStreamingDataset(IterableDataset):
    """PyTorch IterableDataset wrapper for HuggingFace streaming datasets.
    
    This class loads datasets from HuggingFace Hub in streaming mode,
    meaning data is processed on-the-fly without local download or caching.
    
    Attributes:
        dataset_name: Name of the HuggingFace dataset
        split: Dataset split to use (train, validation, test)
        transform: Image transformation function
        image_column: Name of the column containing images
        label_column: Name of the column containing labels
    """
    
    def __init__(
        self,
        dataset_name: str,
        split: str = "train",
        transform: Optional[Callable] = None,
        image_column: str = "image",
        label_column: str = "label",
        trust_remote_code: bool = False,
        max_samples: Optional[int] = None,
    ):
        """Initialize the streaming dataset.
        
        Args:
            dataset_name: Name of the HuggingFace dataset (e.g., "food101")
            split: Dataset split to use (train, validation, test)
            transform: Optional image transformation function
            image_column: Name of the column containing images
            label_column: Name of the column containing labels  
            trust_remote_code: Whether to trust remote code for custom datasets
            max_samples: Optional limit on number of samples to iterate
        
        Raises:
            ImportError: If datasets library is not installed
        """
        if not HF_DATASETS_AVAILABLE:
            raise ImportError(
                "HuggingFace datasets library not installed. "
                "Install it with: pip install datasets"
            )
        
        self.dataset_name = dataset_name
        self.split = split
        self.transform = transform or get_default_transform()
        self.image_column = image_column
        self.label_column = label_column
        self.trust_remote_code = trust_remote_code
        self.max_samples = max_samples
        
        # Initialize the streaming dataset
        self._dataset = None
        self._label_to_id: Dict[str, int] = {}
        self._id_to_label: Dict[int, str] = {}
        
        logger.info(
            f"Initialized HFStreamingDataset: {dataset_name}, split={split}, "
            f"streaming=True, download=False"
        )
    
    def _get_dataset(self) -> HFIterableDataset:
        """Lazily load the streaming dataset.
        
        Returns:
            HuggingFace IterableDataset in streaming mode
        """
        if self._dataset is None:
            logger.info(f"Loading dataset '{self.dataset_name}' in streaming mode...")
            self._dataset = load_dataset(
                self.dataset_name,
                split=self.split,
                streaming=True,
                trust_remote_code=self.trust_remote_code,
            )
            logger.info("Dataset loaded successfully (streaming mode)")
        return self._dataset
    
    def _process_image(self, image) -> torch.Tensor:
        """Process a single image from the dataset.
        
        Args:
            image: PIL Image or image data from HuggingFace
            
        Returns:
            Transformed image tensor
        """
        # Handle different image formats
        if isinstance(image, Image.Image):
            img_array = np.array(image.convert("RGB"))
        elif isinstance(image, np.ndarray):
            img_array = image
        elif isinstance(image, bytes):
            img_array = np.array(Image.open(io.BytesIO(image)).convert("RGB"))
        elif isinstance(image, dict) and "bytes" in image:
            img_array = np.array(Image.open(io.BytesIO(image["bytes"])).convert("RGB"))
        else:
            raise ValueError(f"Unsupported image type: {type(image)}")
        
        # Apply transform
        if ALBUMENTATIONS_AVAILABLE and hasattr(self.transform, '__call__'):
            if hasattr(self.transform, 'transforms'):
                # Albumentations Compose
                transformed = self.transform(image=img_array)
                return transformed["image"]
            else:
                # Custom callable
                return self.transform(img_array)
        else:
            return self.transform(img_array)
    
    def _process_label(self, label) -> int:
        """Convert label to integer ID.
        
        Args:
            label: Label value (int, str, or other)
            
        Returns:
            Integer label ID
        """
        if isinstance(label, int):
            return label
        
        # Convert string/other to int
        label_str = str(label)
        if label_str not in self._label_to_id:
            new_id = len(self._label_to_id)
            self._label_to_id[label_str] = new_id
            self._id_to_label[new_id] = label_str
        
        return self._label_to_id[label_str]
    
    def __iter__(self) -> Iterator[Tuple[torch.Tensor, int]]:
        """Iterate over the streaming dataset.
        
        Yields:
            Tuple of (image_tensor, label_id)
        """
        dataset = self._get_dataset()
        count = 0
        
        for sample in dataset:
            if self.max_samples is not None and count >= self.max_samples:
                break
            
            try:
                # Get image and label
                image = sample.get(self.image_column)
                label = sample.get(self.label_column, 0)
                
                if image is None:
                    logger.warning(f"No image found in column '{self.image_column}'")
                    continue
                
                # Process image and label
                image_tensor = self._process_image(image)
                label_id = self._process_label(label)
                
                yield image_tensor, label_id
                count += 1
                
            except Exception as e:
                logger.warning(f"Failed to process sample: {e}")
                continue
        
        logger.info(f"Iterated over {count} samples from {self.dataset_name}")
    
    def get_label_mapping(self) -> Dict[int, str]:
        """Get the mapping from label IDs to label names.
        
        Returns:
            Dictionary mapping integer IDs to label names
        """
        return self._id_to_label.copy()


def create_streaming_dataloader(
    dataset_name: str,
    split: str = "train",
    batch_size: int = 32,
    num_workers: int = 0,
    transform: Optional[Callable] = None,
    image_column: str = "image",
    label_column: str = "label",
    max_samples: Optional[int] = None,
    **kwargs
) -> DataLoader:
    """Create a PyTorch DataLoader for streaming HuggingFace datasets.
    
    This function creates a DataLoader that streams data from HuggingFace
    without downloading or caching locally.
    
    Args:
        dataset_name: Name of the HuggingFace dataset
        split: Dataset split to use (train, validation, test)
        batch_size: Number of samples per batch
        num_workers: Number of worker processes (0 for main process)
        transform: Optional image transformation function
        image_column: Name of the column containing images
        label_column: Name of the column containing labels
        max_samples: Optional limit on number of samples
        **kwargs: Additional arguments passed to HFStreamingDataset
        
    Returns:
        PyTorch DataLoader for the streaming dataset
        
    Example:
        >>> loader = create_streaming_dataloader("food101", batch_size=16)
        >>> for images, labels in loader:
        ...     print(images.shape, labels.shape)
        ...     break
        torch.Size([16, 3, 256, 256]) torch.Size([16])
    """
    dataset = HFStreamingDataset(
        dataset_name=dataset_name,
        split=split,
        transform=transform,
        image_column=image_column,
        label_column=label_column,
        max_samples=max_samples,
        **kwargs
    )
    
    # Note: num_workers should be 0 for streaming datasets
    # as the iteration happens in the main process
    return DataLoader(
        dataset,
        batch_size=batch_size,
        num_workers=num_workers,
        pin_memory=torch.cuda.is_available(),
    )


def train_with_streaming(
    model: torch.nn.Module,
    dataset_name: str,
    epochs: int = 1,
    batch_size: int = 32,
    lr: float = 1e-4,
    max_samples_per_epoch: Optional[int] = None,
    device: str = "cuda" if torch.cuda.is_available() else "cpu",
) -> Dict[str, Any]:
    """Train a model using streaming data from HuggingFace.
    
    This function demonstrates how to train a model using streaming data
    without downloading the dataset locally.
    
    Args:
        model: PyTorch model to train
        dataset_name: Name of the HuggingFace dataset
        epochs: Number of training epochs
        batch_size: Batch size for training
        lr: Learning rate
        max_samples_per_epoch: Optional limit on samples per epoch
        device: Device to train on (cuda/cpu)
        
    Returns:
        Dictionary with training metrics
        
    Example:
        >>> import timm
        >>> model = timm.create_model("efficientnet_b0", num_classes=101)
        >>> results = train_with_streaming(model, "food101", epochs=1)
    """
    model = model.to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr)
    criterion = torch.nn.CrossEntropyLoss()
    
    logger.info(f"Starting streaming training on {dataset_name}")
    logger.info(f"Device: {device}, Batch size: {batch_size}, LR: {lr}")
    
    total_loss = 0.0
    total_samples = 0
    
    for epoch in range(epochs):
        model.train()
        epoch_loss = 0.0
        epoch_samples = 0
        
        # Create a fresh dataloader for each epoch
        dataloader = create_streaming_dataloader(
            dataset_name=dataset_name,
            split="train",
            batch_size=batch_size,
            max_samples=max_samples_per_epoch,
        )
        
        for batch_idx, (images, labels) in enumerate(dataloader):
            images = images.to(device)
            labels = labels.to(device)
            
            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            
            epoch_loss += loss.item() * images.size(0)
            epoch_samples += images.size(0)
            
            if batch_idx % 10 == 0:
                logger.info(
                    f"Epoch {epoch+1}/{epochs}, Batch {batch_idx}, "
                    f"Loss: {loss.item():.4f}, Samples: {epoch_samples}"
                )
        
        avg_epoch_loss = epoch_loss / max(1, epoch_samples)
        total_loss += epoch_loss
        total_samples += epoch_samples
        
        logger.info(
            f"Epoch {epoch+1}/{epochs} complete. "
            f"Avg Loss: {avg_epoch_loss:.4f}, Samples: {epoch_samples}"
        )
    
    avg_loss = total_loss / max(1, total_samples)
    
    return {
        "epochs": epochs,
        "total_samples": total_samples,
        "avg_loss": avg_loss,
        "device": device,
        "dataset": dataset_name,
    }


# Example datasets for streaming (good for testing the streaming functionality)
# Users can specify any HuggingFace image dataset with image/label columns
EXAMPLE_DATASETS = {
    "imagenet-1k": {
        "name": "imagenet-1k",
        "description": "ImageNet dataset - contains some furniture categories",
        "image_column": "image",
        "label_column": "label",
        "requires_auth": True,
    },
    "food101": {
        "name": "food101", 
        "description": "Food images dataset - good for testing streaming",
        "image_column": "image",
        "label_column": "label",
        "requires_auth": False,
    },
    "cifar10": {
        "name": "cifar10",
        "description": "CIFAR-10 images - small dataset for testing",
        "image_column": "img",
        "label_column": "label",
        "requires_auth": False,
    },
}


def list_available_datasets() -> Dict[str, Dict[str, Any]]:
    """List example datasets available for streaming.
    
    These are example datasets that work well for testing the streaming
    functionality. Users can load any HuggingFace image dataset by
    specifying the dataset name and column names.
    
    Returns:
        Dictionary of example dataset information
    """
    return EXAMPLE_DATASETS.copy()


if __name__ == "__main__":
    # Demo: Load and iterate over a streaming dataset
    print("=" * 60)
    print("HuggingFace Streaming Dataset Demo")
    print("=" * 60)
    
    if not HF_DATASETS_AVAILABLE:
        print("ERROR: HuggingFace datasets library not installed")
        print("Install with: pip install datasets")
        exit(1)
    
    # Create streaming dataloader
    print("\nCreating streaming dataloader for 'cifar10'...")
    loader = create_streaming_dataloader(
        dataset_name="cifar10",
        split="train",
        batch_size=8,
        image_column="img",
        label_column="label",
        max_samples=24,  # Limit for demo
    )
    
    print("\nIterating over streaming batches (no local download):")
    for batch_idx, (images, labels) in enumerate(loader):
        print(f"  Batch {batch_idx + 1}: images={images.shape}, labels={labels.shape}")
        if batch_idx >= 2:
            print("  ...")
            break
    
    print("\n✅ Streaming dataset demo complete!")
    print("=" * 60)
