"""Utility functions for Kaggle dataset management.

This module provides helpers for ensuring Kaggle credentials are configured
and downloading datasets from Kaggle.
"""
import os
import json
import stat
import subprocess
import sys
from pathlib import Path
from typing import Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def ensure_pkg(pkg: str) -> None:
    """Ensure that a package is importable.

    If the package cannot be imported, an :class:`ImportError` is raised with
    a message instructing the user to install the dependency manually. This
    avoids implicitly installing packages at runtime and gives clearer feedback
    to the caller.
    
    Args:
        pkg: Name of the package to check
        
    Raises:
        ImportError: If the package is not installed
        
    Example:
        >>> ensure_pkg("kaggle")
    """
    try:
        __import__(pkg)
        logger.debug(f"Package '{pkg}' is available")
    except ImportError as e:
        error_msg = (
            f"Required package '{pkg}' is not installed. "
            f"Please install it manually: pip install {pkg}"
        )
        logger.error(error_msg)
        raise ImportError(error_msg) from e

def ensure_kaggle_token() -> None:
    """Ensure Kaggle API credentials are configured.
    
    This function checks for Kaggle credentials in the following order:
    1. Default location: ~/.kaggle/kaggle.json
    2. Project root: ./kaggle.json (copies to default location)
    3. Environment variables: KAGGLE_USERNAME and KAGGLE_KEY
    
    Raises:
        FileNotFoundError: If no valid Kaggle credentials are found
        
    Example:
        >>> ensure_kaggle_token()
        # Ensures kaggle.json exists in ~/.kaggle/
    """
    home = Path.home()
    default = home / ".kaggle" / "kaggle.json"
    local = Path("kaggle.json")

    # Check if already configured
    if default.exists():
        logger.info(f"Kaggle credentials found at {default}")
        return

    # Try to copy from project root
    if local.exists():
        default.parent.mkdir(parents=True, exist_ok=True)
        default.write_bytes(local.read_bytes())
        os.chmod(default, stat.S_IRUSR | stat.S_IWUSR)
        logger.info(f"Installed local kaggle.json to {default}")
        return

    # Try to create from environment variables
    if os.environ.get("KAGGLE_USERNAME") and os.environ.get("KAGGLE_KEY"):
        default.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "username": os.environ["KAGGLE_USERNAME"],
            "key": os.environ["KAGGLE_KEY"]
        }
        default.write_text(json.dumps(data))
        os.chmod(default, stat.S_IRUSR | stat.S_IWUSR)
        logger.info("Created kaggle.json from environment variables")
        return

    # No credentials found
    error_msg = (
        "Kaggle credentials not found. Please provide them in one of these ways:\n"
        "1. Place kaggle.json in ~/.kaggle/ directory\n"
        "2. Place kaggle.json in project root\n"
        "3. Set KAGGLE_USERNAME and KAGGLE_KEY environment variables"
    )
    logger.error(error_msg)
    raise FileNotFoundError(error_msg)

def folder_has_content(path: str, min_files: int = 5) -> bool:
    """Check if a folder contains a minimum number of files.
    
    Args:
        path: Path to check
        min_files: Minimum number of files required
        
    Returns:
        True if folder has at least min_files, False otherwise
    """
    p = Path(path)
    if not p.exists():
        return False
    
    count = 0
    for _, _, fns in os.walk(path):
        count += len(fns)
        if count >= min_files:
            return True
    
    return False


def kaggle_download(
    slug: str,
    dest: str,
    skip_if_exists: bool = True
) -> None:
    """Download a Kaggle dataset.
    
    Args:
        slug: Kaggle dataset identifier (e.g., 'username/dataset-name')
        dest: Destination directory for the dataset
        skip_if_exists: Skip download if directory already has content
        
    Raises:
        ImportError: If kaggle package is not installed
        RuntimeError: If download fails
        
    Example:
        >>> kaggle_download("prashantsingh001/bedroom-interior-dataset", "data/raw/bedroom")
    """
    from shutil import which
    
    # Ensure kaggle CLI is available
    if which("kaggle") is None:
        ensure_pkg("kaggle")

    dest_p = Path(dest)
    dest_p.mkdir(parents=True, exist_ok=True)
    
    # Skip if already exists and has content
    if skip_if_exists and folder_has_content(dest, 5):
        logger.info(f"Skipping existing dataset: {slug}")
        return

    logger.info(f"Downloading Kaggle dataset: {slug}")
    logger.info(f"Destination: {dest}")
    
    cmd = [
        "kaggle", "datasets", "download",
        "-d", slug,
        "-p", str(dest_p),
        "--unzip"
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.stdout:
            logger.info(result.stdout)
        
        if result.returncode != 0:
            logger.error(result.stderr)
            raise RuntimeError(f"Failed to download dataset: {slug}\n{result.stderr}")
        
        logger.info(f"Successfully downloaded: {slug}")
        
    except Exception as e:
        error_msg = f"Failed to download {slug}: {str(e)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)
