import os, pandas as pd
from pathlib import Path
from PIL import Image, ImageFile
from tqdm import tqdm
import imagehash
from sklearn.model_selection import train_test_split

ImageFile.LOAD_TRUNCATED_IMAGES = True
IMG_EXT = {'.jpg', '.jpeg', '.png', '.bmp', '.webp'}

def scan_images(root: str, source_name: str) -> list[dict[str, str]]:
    """Walk a directory tree and gather image metadata.

    Args:
        root: Directory to recursively scan.
        source_name: Identifier for the image source.

    Returns:
        List of dictionaries describing discovered images with filepath, label
        and source information.
    """
    rows: list[dict[str, str]] = []
    root = root.rstrip("/\\")
    for dirpath, _, filenames in os.walk(root):
        for fn in filenames:
            ext = os.path.splitext(fn)[1].lower()
            if ext in IMG_EXT:
                fp = os.path.join(dirpath, fn)
                rel = dirpath.replace(root, "").strip("/\\")
                label = rel.split(os.sep)[0] if rel else "unknown"
                rows.append({"filepath": fp, "label": label, "source": source_name})
    return rows

def unify_and_clean(
    catalog_rows: list[dict[str, str]],
    min_size: int = 256,
    csv_out: str = "data/unified_images.csv",
) -> pd.DataFrame:
    """Validate, deduplicate and export a catalog of images.

    Args:
        catalog_rows: Output from :func:`scan_images`.
        min_size: Minimum width/height to keep an image.
        csv_out: Destination CSV path for the cleaned catalog.

    Returns:
        Cleaned DataFrame of image metadata.
    """
    df = pd.DataFrame(catalog_rows).drop_duplicates(subset=["filepath"]).reset_index(drop=True)
    W, H, ok, ahash = [], [], [], []

    for p in tqdm(df["filepath"], desc="Validating"):
        try:
            with Image.open(p) as im: im.verify()
            with Image.open(p) as im:
                w, h = im.size
                W.append(w); H.append(h); ok.append(True)
                ahash.append(str(imagehash.average_hash(im)))
        except Exception:
            W.append(None); H.append(None); ok.append(False); ahash.append(None)

    df["width"] = W; df["height"] = H; df["is_valid"] = ok; df["ahash"] = ahash
    df = df[df["is_valid"] == True]
    df = df[(df["width"] >= min_size) & (df["height"] >= min_size)]
    df = df.drop_duplicates(subset=["ahash"]).drop(columns=["is_valid"]).reset_index(drop=True)

    Path(csv_out).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(csv_out, index=False, encoding="utf-8")
    return df

def export_clean_256(
    csv_path: str = "data/unified_images.csv",
    out_dir: str = "data/clean256",
    img_size: int = 256,
    val_ratio: float = 0.2,
    seed: int = 42,
) -> str:
    """Resize images to a square dataset and export train/val splits.

    Args:
        csv_path: Path to the cleaned catalog CSV.
        out_dir: Root directory to write processed images.
        img_size: Target width/height of resized images.
        val_ratio: Fraction of images used for validation.
        seed: Random seed for splitting.

    Returns:
        The directory containing the exported dataset.
    """
    from PIL import Image

    df = pd.read_csv(csv_path)
    Path(out_dir).mkdir(parents=True, exist_ok=True)

    try:
        train_df, val_df = train_test_split(
            df,
            test_size=val_ratio,
            random_state=seed,
            stratify=df['label'].fillna('unknown')
        )
    except Exception:
        train_df, val_df = train_test_split(df, test_size=val_ratio, random_state=seed)

    def _export(split_df: pd.DataFrame, split: str) -> None:
        """Export a split of the dataset to disk."""
        for _, row in tqdm(split_df.iterrows(), total=len(split_df), desc=f"Export {split}"):
            lbl = row['label'] if pd.notna(row['label']) else 'unknown'
            src = row['filepath']
            dst_dir = Path(out_dir) / split / str(lbl)
            dst_dir.mkdir(parents=True, exist_ok=True)
            try:
                with Image.open(src) as im:
                    im = im.convert('RGB').resize((img_size, img_size))
                    out_path = dst_dir / Path(src).name
                    base = out_path.with_suffix(''); ext = out_path.suffix; k = 1
                    while out_path.exists():
                        out_path = Path(str(base) + f"_{k}{ext}"); k += 1
                    im.save(out_path)
            except Exception:
                pass

    _export(train_df, "train")
    _export(val_df, "val")
    return out_dir
