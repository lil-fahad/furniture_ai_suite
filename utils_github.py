"""Utility functions for downloading datasets from GitHub.

This module provides helpers for downloading dataset archives from GitHub
repositories and releases, as an alternative to Kaggle when datasets are
hosted on GitHub.
"""
import os
import zipfile
import tarfile
import tempfile
import shutil
from pathlib import Path
from typing import Optional
import logging
import urllib.request
import urllib.error

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Minimum number of files to consider a dataset as already downloaded
# This prevents re-downloading if destination has some content
MIN_FILES_TO_SKIP = 5


def download_file(url: str, dest_path: str, timeout: int = 300) -> str:
    """Download a file from a URL.
    
    Args:
        url: URL to download from
        dest_path: Destination file path
        timeout: Request timeout in seconds
        
    Returns:
        Path to downloaded file
        
    Raises:
        RuntimeError: If download fails
    """
    logger.info(f"Downloading from {url}")
    
    try:
        # Create parent directory if needed
        Path(dest_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Download with progress
        urllib.request.urlretrieve(url, dest_path)
        
        file_size = os.path.getsize(dest_path)
        logger.info(f"Downloaded {file_size:,} bytes to {dest_path}")
        return dest_path
        
    except urllib.error.URLError as e:
        error_msg = f"Failed to download from {url}: {str(e)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    except Exception as e:
        error_msg = f"Download failed: {str(e)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)


def extract_archive(archive_path: str, dest_dir: str) -> str:
    """Extract a zip or tar archive.
    
    Args:
        archive_path: Path to archive file
        dest_dir: Destination directory for extraction
        
    Returns:
        Path to extraction directory
        
    Raises:
        RuntimeError: If extraction fails
    """
    logger.info(f"Extracting {archive_path} to {dest_dir}")
    
    Path(dest_dir).mkdir(parents=True, exist_ok=True)
    
    try:
        if archive_path.endswith('.zip'):
            with zipfile.ZipFile(archive_path, 'r') as zf:
                zf.extractall(dest_dir)
        elif archive_path.endswith(('.tar.gz', '.tgz')):
            with tarfile.open(archive_path, 'r:gz') as tf:
                tf.extractall(dest_dir)
        elif archive_path.endswith('.tar'):
            with tarfile.open(archive_path, 'r') as tf:
                tf.extractall(dest_dir)
        else:
            raise RuntimeError(f"Unsupported archive format: {archive_path}")
        
        logger.info(f"Extraction complete: {dest_dir}")
        return dest_dir
        
    except Exception as e:
        error_msg = f"Failed to extract {archive_path}: {str(e)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)


def download_github_release(
    owner: str,
    repo: str,
    asset_name: str,
    dest_dir: str,
    tag: str = "latest",
    extract: bool = True,
    skip_if_exists: bool = True
) -> str:
    """Download a release asset from a GitHub repository.
    
    Args:
        owner: GitHub repository owner
        repo: Repository name
        asset_name: Name of the release asset to download
        dest_dir: Destination directory
        tag: Release tag (use "latest" for latest release)
        extract: Whether to extract archive after download
        skip_if_exists: Skip if destination already has content
        
    Returns:
        Path to downloaded/extracted content
        
    Raises:
        RuntimeError: If download fails
        
    Example:
        >>> download_github_release(
        ...     owner="user",
        ...     repo="dataset-repo",
        ...     asset_name="dataset.zip",
        ...     dest_dir="data/raw/dataset",
        ...     tag="v1.0"
        ... )
    """
    dest_path = Path(dest_dir)
    
    # Skip if already exists with sufficient content
    if skip_if_exists and dest_path.exists():
        file_count = sum(1 for _ in dest_path.rglob('*') if _.is_file())
        if file_count >= MIN_FILES_TO_SKIP:
            logger.info(f"Skipping existing dataset at {dest_dir} ({file_count} files)")
            return str(dest_dir)
    
    # Construct download URL
    if tag == "latest":
        # For latest release, we need to redirect
        base_url = f"https://github.com/{owner}/{repo}/releases/latest/download/{asset_name}"
    else:
        base_url = f"https://github.com/{owner}/{repo}/releases/download/{tag}/{asset_name}"
    
    logger.info(f"Downloading GitHub release: {owner}/{repo} @ {tag}")
    
    # Download to temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(asset_name).suffix) as tmp:
        tmp_path = tmp.name
    
    try:
        download_file(base_url, tmp_path)
        
        if extract and (asset_name.endswith('.zip') or 
                       asset_name.endswith('.tar.gz') or 
                       asset_name.endswith('.tgz') or
                       asset_name.endswith('.tar')):
            extract_archive(tmp_path, str(dest_dir))
        else:
            # Just move the file
            dest_path.mkdir(parents=True, exist_ok=True)
            shutil.move(tmp_path, dest_path / asset_name)
        
        return str(dest_dir)
        
    finally:
        # Cleanup temp file
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def download_github_archive(
    owner: str,
    repo: str,
    dest_dir: str,
    ref: str = "main",
    skip_if_exists: bool = True
) -> str:
    """Download and extract a GitHub repository archive.
    
    This downloads the repository source code as a zip archive,
    useful for datasets that are stored directly in a repository.
    
    Args:
        owner: GitHub repository owner
        repo: Repository name
        dest_dir: Destination directory
        ref: Git reference (branch, tag, or commit SHA)
        skip_if_exists: Skip if destination already has content
        
    Returns:
        Path to extracted content
        
    Raises:
        RuntimeError: If download fails
        
    Example:
        >>> download_github_archive(
        ...     "username",
        ...     "dataset-repo",
        ...     "data/raw/dataset"
        ... )
    """
    dest_path = Path(dest_dir)
    
    # Skip if already exists with sufficient content
    if skip_if_exists and dest_path.exists():
        file_count = sum(1 for _ in dest_path.rglob('*') if _.is_file())
        if file_count >= MIN_FILES_TO_SKIP:
            logger.info(f"Skipping existing dataset at {dest_dir} ({file_count} files)")
            return str(dest_dir)
    
    # GitHub archive URL - this format works for branches, tags, and commit SHAs
    archive_url = f"https://github.com/{owner}/{repo}/archive/{ref}.zip"
    
    logger.info(f"Downloading GitHub archive: {owner}/{repo} @ {ref}")
    
    # Download to temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp:
        tmp_path = tmp.name
    
    try:
        download_file(archive_url, tmp_path)
        
        # Extract to temp directory first
        with tempfile.TemporaryDirectory() as tmp_dir:
            extract_archive(tmp_path, tmp_dir)
            
            # Find the extracted folder (usually repo-branch)
            extracted_items = list(Path(tmp_dir).iterdir())
            if len(extracted_items) == 1 and extracted_items[0].is_dir():
                # Move contents from the single folder
                source = extracted_items[0]
            else:
                source = Path(tmp_dir)
            
            # Move to destination
            dest_path.mkdir(parents=True, exist_ok=True)
            for item in source.iterdir():
                dest_item = dest_path / item.name
                if dest_item.exists():
                    if dest_item.is_dir():
                        shutil.rmtree(dest_item)
                    else:
                        dest_item.unlink()
                shutil.move(str(item), str(dest_path))
        
        logger.info(f"Downloaded and extracted to {dest_dir}")
        return str(dest_dir)
        
    finally:
        # Cleanup temp file
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def download_github_raw_file(
    owner: str,
    repo: str,
    file_path: str,
    dest_path: str,
    ref: str = "main"
) -> str:
    """Download a single raw file from GitHub.
    
    Args:
        owner: GitHub repository owner
        repo: Repository name
        file_path: Path to file in repository
        dest_path: Local destination path
        ref: Git reference (branch, tag, or commit SHA)
        
    Returns:
        Path to downloaded file
        
    Example:
        >>> download_github_raw_file(
        ...     "username",
        ...     "repo",
        ...     "data/labels.json",
        ...     "artifacts/labels.json"
        ... )
    """
    url = f"https://raw.githubusercontent.com/{owner}/{repo}/{ref}/{file_path}"
    
    logger.info(f"Downloading raw file: {owner}/{repo}/{file_path}")
    
    return download_file(url, dest_path)
