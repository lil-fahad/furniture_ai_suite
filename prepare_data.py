"""Data preparation module for interior design classification.

This module handles scanning, validating, cleaning, and preparing image datasets
for training deep learning models.
"""
import os
import pandas as pd
from pathlib import Path
from PIL import Image, ImageFile
from tqdm import tqdm
import imagehash
from sklearn.model_selection import train_test_split
from typing import List, Dict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ImageFile.LOAD_TRUNCATED_IMAGES = True
IMG_EXT = {'.jpg', '.jpeg', '.png', '.bmp', '.webp'}

def scan_images(root: str, source_name: str) -> List[Dict[str, str]]:
    """Walk a directory tree and gather image metadata.

    Args:
        root: Directory to recursively scan for images.
        source_name: Identifier for the image source (e.g., dataset name).

    Returns:
        List of dictionaries describing discovered images with filepath, label
        and source information.
        
    Example:
        >>> rows = scan_images("data/raw/bedroom", "bedroom_dataset")
        >>> len(rows)
        1250
    """
    rows: List[Dict[str, str]] = []
    root = root.rstrip("/\\")
    
    logger.info(f"Scanning images in {root} from source {source_name}")
    
    for dirpath, _, filenames in os.walk(root):
        for fn in filenames:
            ext = os.path.splitext(fn)[1].lower()
            if ext in IMG_EXT:
                fp = os.path.join(dirpath, fn)
                rel = dirpath.replace(root, "").strip("/\\")
                label = rel.split(os.sep)[0] if rel else "unknown"
                rows.append({
                    "filepath": fp,
                    "label": label,
                    "source": source_name
                })
    
    logger.info(f"Found {len(rows)} images from {source_name}")
    return rows

def unify_and_clean(
    catalog_rows: List[Dict[str, str]],
    min_size: int = 256,
    csv_out: str = "data/unified_images.csv",
) -> pd.DataFrame:
    """Validate, deduplicate and export a catalog of images.

    This function performs comprehensive data quality checks:
    - Validates image files can be opened
    - Removes images smaller than min_size
    - Removes duplicate images based on perceptual hash
    - Exports cleaned catalog to CSV

    Args:
        catalog_rows: Output from :func:`scan_images`.
        min_size: Minimum width/height to keep an image.
        csv_out: Destination CSV path for the cleaned catalog.

    Returns:
        Cleaned DataFrame of image metadata.
        
    Raises:
        ValueError: If no valid images remain after cleaning.
    """
    logger.info(f"Starting validation and cleaning of {len(catalog_rows)} images")
    
    df = pd.DataFrame(catalog_rows).drop_duplicates(subset=["filepath"]).reset_index(drop=True)
    logger.info(f"After removing filepath duplicates: {len(df)} images")
    
    W, H, ok, ahash = [], [], [], []

    for p in tqdm(df["filepath"], desc="Validating images"):
        try:
            # Verify image can be opened
            with Image.open(p) as im:
                im.verify()
            
            # Get dimensions and hash
            with Image.open(p) as im:
                w, h = im.size
                W.append(w)
                H.append(h)
                ok.append(True)
                ahash.append(str(imagehash.average_hash(im)))
        except Exception as e:
            # Image is corrupted or unreadable
            W.append(None)
            H.append(None)
            ok.append(False)
            ahash.append(None)

    df["width"] = W
    df["height"] = H
    df["is_valid"] = ok
    df["ahash"] = ahash
    
    # Filter valid images
    df = df[df["is_valid"] == True]
    logger.info(f"After removing invalid images: {len(df)} images")
    
    # Filter by minimum size
    df = df[(df["width"] >= min_size) & (df["height"] >= min_size)]
    logger.info(f"After size filtering (min {min_size}px): {len(df)} images")
    
    # Remove perceptual duplicates
    df = df.drop_duplicates(subset=["ahash"]).drop(columns=["is_valid"]).reset_index(drop=True)
    logger.info(f"After removing perceptual duplicates: {len(df)} images")
    
    if len(df) == 0:
        raise ValueError("No valid images remaining after cleaning")

    # Save to CSV
    Path(csv_out).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(csv_out, index=False, encoding="utf-8")
    logger.info(f"Saved cleaned catalog to {csv_out}")
    
    return df

def export_clean_256(
    csv_path: str = "data/unified_images.csv",
    out_dir: str = "data/clean256",
    img_size: int = 256,
    val_ratio: float = 0.2,
    seed: int = 42,
) -> str:
    """Resize images to a square dataset and export train/val splits.

    This function:
    - Loads the cleaned image catalog
    - Splits into train/validation sets (stratified by label)
    - Resizes all images to a uniform size
    - Organizes images in class-based directory structure

    Args:
        csv_path: Path to the cleaned catalog CSV.
        out_dir: Root directory to write processed images.
        img_size: Target width/height of resized images.
        val_ratio: Fraction of images used for validation (0-1).
        seed: Random seed for reproducible splitting.

    Returns:
        The directory containing the exported dataset.
        
    Raises:
        FileNotFoundError: If csv_path doesn't exist.
        ValueError: If parameters are invalid.
    """
    if not Path(csv_path).exists():
        raise FileNotFoundError(f"CSV catalog not found: {csv_path}")
    
    if not 0 < val_ratio < 1:
        raise ValueError(f"val_ratio must be between 0 and 1, got {val_ratio}")
    
    if img_size < 32:
        raise ValueError(f"img_size too small: {img_size}. Minimum is 32")
    
    logger.info(f"Loading catalog from {csv_path}")
    df = pd.read_csv(csv_path)
    logger.info(f"Loaded {len(df)} images")
    
    Path(out_dir).mkdir(parents=True, exist_ok=True)

    # Split train/val with stratification
    try:
        train_df, val_df = train_test_split(
            df,
            test_size=val_ratio,
            random_state=seed,
            stratify=df['label'].fillna('unknown')
        )
        logger.info(f"Split dataset: {len(train_df)} train, {len(val_df)} validation (stratified)")
    except Exception as e:
        logger.warning(f"Stratified split failed: {e}. Using random split.")
        train_df, val_df = train_test_split(df, test_size=val_ratio, random_state=seed)
        logger.info(f"Split dataset: {len(train_df)} train, {len(val_df)} validation (random)")

    def _export(split_df: pd.DataFrame, split: str) -> None:
        """Export a split of the dataset to disk.
        
        Args:
            split_df: DataFrame containing image metadata for this split
            split: Name of the split ('train' or 'val')
        """
        exported_count = 0
        failed_count = 0
        
        for _, row in tqdm(split_df.iterrows(), total=len(split_df), desc=f"Exporting {split}"):
            lbl = row['label'] if pd.notna(row['label']) else 'unknown'
            src = row['filepath']
            dst_dir = Path(out_dir) / split / str(lbl)
            dst_dir.mkdir(parents=True, exist_ok=True)
            
            try:
                with Image.open(src) as im:
                    # Convert to RGB and resize with high-quality resampling
                    im = im.convert('RGB').resize(
                        (img_size, img_size),
                        Image.Resampling.LANCZOS
                    )
                    
                    # Handle filename collisions
                    out_path = dst_dir / Path(src).name
                    base = out_path.with_suffix('')
                    ext = out_path.suffix
                    k = 1
                    while out_path.exists():
                        out_path = Path(str(base) + f"_{k}{ext}")
                        k += 1
                    
                    im.save(out_path, quality=95)
                    exported_count += 1
            except Exception as e:
                failed_count += 1
                logger.debug(f"Failed to export {src}: {e}")
        
        logger.info(f"Exported {exported_count} images to {split}, {failed_count} failed")

    _export(train_df, "train")
    _export(val_df, "val")
    
    logger.info(f"Dataset export complete: {out_dir}")
    return out_dir
