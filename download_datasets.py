#!/usr/bin/env python3
"""CLI helper to download datasets from the catalog."""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import List, Dict, Any

from utils_kaggle import ensure_pkg, ensure_kaggle_token, kaggle_download

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _load_catalog(catalog_path: str) -> List[Dict[str, Any]]:
    catalog_file = Path(catalog_path)
    if not catalog_file.exists():
        raise FileNotFoundError(f"Catalog not found: {catalog_file}")

    with catalog_file.open("r", encoding="utf-8") as handle:
        catalog = json.load(handle)

    if not isinstance(catalog, list):
        raise ValueError("Dataset catalog must be a list of entries")

    return catalog


def _filter_catalog(catalog: List[Dict[str, Any]], slug: str | None) -> List[Dict[str, Any]]:
    if not slug:
        return catalog

    matches = [item for item in catalog if item.get("slug") == slug]
    if not matches:
        raise ValueError(f"No dataset found for slug: {slug}")

    return matches


def download_datasets(
    catalog_path: str = "datasets_catalog.json",
    slug: str | None = None,
    skip_if_exists: bool = True,
    dry_run: bool = False,
) -> List[str]:
    """Download datasets defined in the catalog.

    Args:
        catalog_path: Path to the JSON catalog file.
        slug: Optional dataset slug to download a single dataset.
        skip_if_exists: Skip download if destination already has content.
        dry_run: When True, only list the datasets without downloading.

    Returns:
        List of dataset slugs that were processed.
    """
    catalog = _load_catalog(catalog_path)
    items = _filter_catalog(catalog, slug)

    if dry_run:
        for item in items:
            logger.info("DRY RUN: %s -> %s", item.get("slug"), item.get("dest"))
        return [item.get("slug", "") for item in items]

    ensure_pkg("kaggle")
    ensure_kaggle_token()

    for item in items:
        kaggle_download(item["slug"], item["dest"], skip_if_exists=skip_if_exists)

    return [item.get("slug", "") for item in items]


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download datasets from the catalog.")
    parser.add_argument(
        "--catalog",
        default="datasets_catalog.json",
        help="Path to datasets catalog JSON file.",
    )
    parser.add_argument(
        "--slug",
        help="Download a single dataset by slug (e.g. username/dataset-name).",
    )
    parser.add_argument(
        "--no-skip-existing",
        action="store_true",
        help="Download even if destination already has content.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List datasets without downloading.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    try:
        download_datasets(
            catalog_path=args.catalog,
            slug=args.slug,
            skip_if_exists=not args.no_skip_existing,
            dry_run=args.dry_run,
        )
        return 0
    except Exception as exc:
        logger.error("Dataset download failed: %s", exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
