"""Script to clone the DeepFurniture dataset from Hugging Face.

This script provides a command-line interface to clone the DeepFurniture dataset
from the Hugging Face repository using git.
"""
import logging
from pathlib import Path
from utils_kaggle import huggingface_clone

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Clone the DeepFurniture dataset from Hugging Face."""
    repo_url = "https://huggingface.co/datasets/byliu/DeepFurniture"
    dest = "data/raw/deepfurniture"
    
    logger.info("Starting DeepFurniture dataset clone")
    logger.info(f"Repository: {repo_url}")
    logger.info(f"Destination: {dest}")
    
    try:
        # Create the data/raw directory if it doesn't exist
        Path(dest).parent.mkdir(parents=True, exist_ok=True)
        
        # Clone the dataset
        huggingface_clone(repo_url, dest, skip_if_exists=True)
        
        logger.info("✓ DeepFurniture dataset cloned successfully")
        logger.info(f"Dataset location: {Path(dest).absolute()}")
        
    except Exception as e:
        logger.error(f"✗ Failed to clone DeepFurniture dataset: {str(e)}")
        raise


if __name__ == "__main__":
    main()
