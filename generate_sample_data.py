"""Generate synthetic sample dataset for training when Kaggle datasets are unavailable.

This module creates synthetic images representing different interior design categories
for training and testing the classification model. The generated images use color
palettes and geometric patterns characteristic of each room type.

Usage:
    python generate_sample_data.py

This will create a dataset in data/clean256/ with train/ and val/ splits.
"""
import os
import random
import numpy as np
from PIL import Image, ImageDraw
from pathlib import Path
from typing import List, Tuple, Dict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set seeds for reproducibility
random.seed(42)
np.random.seed(42)

# Interior design categories
CLASSES = [
    "bedroom",
    "bathroom", 
    "kitchen",
    "living_room",
    "dining_room"
]

# Color palettes for different room types (RGB tuples)
# Each palette contains characteristic colors for that room type
COLOR_PALETTES: Dict[str, List[Tuple[int, int, int]]] = {
    "bedroom": [
        (139, 90, 43),    # Warm brown (wooden furniture)
        (210, 180, 140),  # Tan/beige (bedding)
        (70, 130, 180),   # Steel blue (accent)
        (255, 248, 220),  # Cornsilk (walls)
        (169, 169, 169),  # Dark gray (accents)
    ],
    "bathroom": [
        (173, 216, 230),  # Light blue (water theme)
        (255, 255, 255),  # White (tiles)
        (0, 128, 128),    # Teal (accents)
        (176, 196, 222),  # Light steel blue
        (192, 192, 192),  # Silver (fixtures)
    ],
    "kitchen": [
        (192, 192, 192),  # Silver (appliances)
        (139, 69, 19),    # Saddle brown (cabinets)
        (255, 255, 255),  # White (counters)
        (105, 105, 105),  # Dim gray (stainless)
        (245, 222, 179),  # Wheat (countertops)
    ],
    "living_room": [
        (101, 67, 33),    # Dark brown (furniture)
        (245, 245, 220),  # Beige (walls)
        (128, 0, 0),      # Maroon (accent pillows)
        (255, 215, 0),    # Gold (decor)
        (34, 139, 34),    # Forest green (plants)
    ],
    "dining_room": [
        (139, 90, 43),    # Warm brown (table)
        (160, 82, 45),    # Sienna (chairs)
        (245, 245, 220),  # Beige (tablecloth)
        (218, 165, 32),   # Goldenrod (chandelier)
        (250, 250, 250),  # Off-white (walls)
    ],
}

# Default samples per class
DEFAULT_TRAIN_SAMPLES = 50
DEFAULT_VAL_SAMPLES = 15


def create_synthetic_room_image(
    class_name: str,
    img_size: int = 256,
    variation_seed: int = None
) -> Image.Image:
    """Create a synthetic room image with characteristic features.
    
    Args:
        class_name: Type of room to generate (bedroom, kitchen, etc.)
        img_size: Size of the output image (square)
        variation_seed: Optional seed for this specific image
        
    Returns:
        PIL Image object
    """
    if variation_seed is not None:
        random.seed(variation_seed)
        np.random.seed(variation_seed)
    
    # Get color palette for this room type
    palette = COLOR_PALETTES.get(class_name, COLOR_PALETTES["living_room"])
    
    # Create base image with background color
    bg_color = random.choice(palette)
    img = Image.new('RGB', (img_size, img_size), bg_color)
    draw = ImageDraw.Draw(img)
    
    # Add floor area (bottom third)
    floor_color = tuple(max(0, c - 30) for c in random.choice(palette))
    draw.rectangle([0, img_size * 2 // 3, img_size, img_size], fill=floor_color)
    
    # Add random geometric shapes to simulate furniture
    num_shapes = random.randint(4, 10)
    for _ in range(num_shapes):
        shape_type = random.choice(['rectangle', 'ellipse', 'rectangle'])
        color = random.choice(palette)
        
        # Random position and size
        x1 = random.randint(0, img_size - 60)
        y1 = random.randint(img_size // 4, img_size - 60)
        width = random.randint(40, 120)
        height = random.randint(30, 100)
        x2 = min(x1 + width, img_size)
        y2 = min(y1 + height, img_size)
        
        if shape_type == 'rectangle':
            draw.rectangle([x1, y1, x2, y2], fill=color)
        else:
            draw.ellipse([x1, y1, x2, y2], fill=color)
    
    # Add some lines to simulate furniture edges/frames
    num_lines = random.randint(3, 8)
    for _ in range(num_lines):
        color = random.choice(palette)
        x1 = random.randint(0, img_size)
        y1 = random.randint(0, img_size)
        x2 = random.randint(0, img_size)
        y2 = random.randint(0, img_size)
        line_width = random.randint(2, 6)
        draw.line([x1, y1, x2, y2], fill=color, width=line_width)
    
    # Add a window or door frame (rectangle outline)
    if random.random() > 0.3:
        frame_color = (80, 80, 80)
        fx1 = random.randint(20, img_size // 2)
        fy1 = random.randint(10, img_size // 3)
        fw = random.randint(60, 100)
        fh = random.randint(80, 120)
        draw.rectangle(
            [fx1, fy1, fx1 + fw, fy1 + fh],
            outline=frame_color,
            width=3
        )
    
    # Add some noise for realism
    arr = np.array(img)
    noise = np.random.normal(0, 12, arr.shape).astype(np.int16)
    arr = np.clip(arr.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    img = Image.fromarray(arr)
    
    return img


def generate_dataset(
    output_dir: str = "data/clean256",
    train_samples_per_class: int = DEFAULT_TRAIN_SAMPLES,
    val_samples_per_class: int = DEFAULT_VAL_SAMPLES,
    img_size: int = 256,
    classes: List[str] = None
) -> Dict[str, int]:
    """Generate a complete synthetic dataset with train/val splits.
    
    Args:
        output_dir: Root directory for the dataset
        train_samples_per_class: Number of training images per class
        val_samples_per_class: Number of validation images per class
        img_size: Size of generated images (square)
        classes: List of class names to generate (defaults to CLASSES)
        
    Returns:
        Dictionary with statistics about generated dataset
    """
    if classes is None:
        classes = CLASSES
    
    output_path = Path(output_dir)
    train_dir = output_path / "train"
    val_dir = output_path / "val"
    
    logger.info(f"Generating synthetic dataset in {output_dir}")
    logger.info(f"Classes: {classes}")
    logger.info(f"Train samples per class: {train_samples_per_class}")
    logger.info(f"Val samples per class: {val_samples_per_class}")
    
    # Create directories
    for class_name in classes:
        (train_dir / class_name).mkdir(parents=True, exist_ok=True)
        (val_dir / class_name).mkdir(parents=True, exist_ok=True)
    
    total_train = 0
    total_val = 0
    
    # Generate training images
    logger.info("Generating training images...")
    for class_name in classes:
        for i in range(train_samples_per_class):
            # Use unique seed for each image for variety
            seed = hash(f"{class_name}_train_{i}") % (2**31)
            img = create_synthetic_room_image(class_name, img_size, seed)
            img_path = train_dir / class_name / f"{class_name}_{i:04d}.jpg"
            img.save(img_path, quality=95)
            total_train += 1
        logger.info(f"  Created {train_samples_per_class} training images for '{class_name}'")
    
    # Generate validation images
    logger.info("Generating validation images...")
    for class_name in classes:
        for i in range(val_samples_per_class):
            # Use different seed pattern for validation
            seed = hash(f"{class_name}_val_{i}") % (2**31)
            img = create_synthetic_room_image(class_name, img_size, seed)
            img_path = val_dir / class_name / f"{class_name}_val_{i:04d}.jpg"
            img.save(img_path, quality=95)
            total_val += 1
        logger.info(f"  Created {val_samples_per_class} validation images for '{class_name}'")
    
    stats = {
        "total_train": total_train,
        "total_val": total_val,
        "total_images": total_train + total_val,
        "num_classes": len(classes),
        "classes": classes,
        "output_dir": str(output_dir)
    }
    
    logger.info("=" * 60)
    logger.info("DATASET GENERATION COMPLETE")
    logger.info("=" * 60)
    logger.info(f"Total training images: {total_train}")
    logger.info(f"Total validation images: {total_val}")
    logger.info(f"Total images: {total_train + total_val}")
    logger.info(f"Number of classes: {len(classes)}")
    logger.info(f"Output directory: {output_dir}")
    logger.info("=" * 60)
    
    return stats


def main():
    """Main entry point for dataset generation."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Generate synthetic interior design dataset for training"
    )
    parser.add_argument(
        "--output-dir", "-o",
        default="data/clean256",
        help="Output directory for the dataset"
    )
    parser.add_argument(
        "--train-samples", "-t",
        type=int,
        default=DEFAULT_TRAIN_SAMPLES,
        help=f"Training samples per class (default: {DEFAULT_TRAIN_SAMPLES})"
    )
    parser.add_argument(
        "--val-samples", "-v",
        type=int,
        default=DEFAULT_VAL_SAMPLES,
        help=f"Validation samples per class (default: {DEFAULT_VAL_SAMPLES})"
    )
    parser.add_argument(
        "--img-size", "-s",
        type=int,
        default=256,
        help="Image size in pixels (default: 256)"
    )
    
    args = parser.parse_args()
    
    generate_dataset(
        output_dir=args.output_dir,
        train_samples_per_class=args.train_samples,
        val_samples_per_class=args.val_samples,
        img_size=args.img_size
    )


if __name__ == "__main__":
    main()
