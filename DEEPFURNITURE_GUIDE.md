# DeepFurniture Dataset Integration Guide

This guide explains how to use the DeepFurniture dataset integration feature in the Furniture AI Suite.

## Overview

The DeepFurniture dataset from Hugging Face (https://huggingface.co/datasets/byliu/DeepFurniture) is now integrated into the Furniture AI Suite. This large-scale furniture dataset can be cloned and used alongside the existing Kaggle datasets for training and inference.

## Features

- **Automatic Cloning**: Clone the dataset with a single command or API call
- **Smart Skip Logic**: Automatically skips re-cloning if the dataset already exists
- **Seamless Integration**: Works with the existing data preparation pipeline
- **Multiple Access Methods**: Use via CLI, API, or as part of the full download workflow

## Usage Methods

### Method 1: Standalone CLI Script

The simplest way to clone the DeepFurniture dataset:

```bash
python clone_deepfurniture.py
```

This script will:
1. Create the `data/raw/deepfurniture` directory
2. Clone the dataset from Hugging Face
3. Skip if the dataset already exists (with 5+ files)

### Method 2: API Endpoint

Use the dedicated API endpoint:

```bash
# Clone the DeepFurniture dataset
curl -X POST "http://localhost:8000/clone-deepfurniture?skip_if_exists=true"
```

Response:
```json
{
  "ok": true,
  "message": "DeepFurniture dataset cloned successfully",
  "repo_url": "https://huggingface.co/datasets/byliu/DeepFurniture",
  "destination": "data/raw/deepfurniture"
}
```

### Method 3: Combined Download

The `/download` endpoint now supports both Kaggle and Hugging Face datasets:

```bash
# Download all datasets (Kaggle + Hugging Face)
curl -X POST "http://localhost:8000/download?skip_if_exists=true"
```

This will:
1. Download all 8 Kaggle datasets
2. Clone the DeepFurniture dataset from Hugging Face
3. Skip any datasets that already exist

## Dataset Integration

After cloning, the DeepFurniture dataset integrates seamlessly with the existing pipeline:

```bash
# 1. Clone/download datasets
python clone_deepfurniture.py

# 2. Prepare data (validates, deduplicates, resizes)
curl -X POST "http://localhost:8000/prepare"

# 3. Train models
curl -X POST "http://localhost:8000/train"

# 4. Run inference
curl -X POST "http://localhost:8000/predict" -F "file=@image.jpg"
```

## Configuration

The DeepFurniture dataset is configured in `datasets_catalog.json`:

```json
{
  "source": "huggingface",
  "repo_url": "https://huggingface.co/datasets/byliu/DeepFurniture",
  "dest": "data/raw/deepfurniture",
  "description": "DeepFurniture dataset from Hugging Face"
}
```

### Parameters

- **source**: `"huggingface"` - Indicates this is a Hugging Face dataset
- **repo_url**: Full URL to the Hugging Face dataset repository
- **dest**: Local destination directory for the cloned dataset
- **description**: Human-readable description

## Requirements

- **Git**: The system uses `git clone` to download the dataset
- **Internet Access**: Required to access huggingface.co
- **Disk Space**: Ensure sufficient space for the dataset

## Troubleshooting

### Error: "git command not found"

Install Git:
```bash
# Ubuntu/Debian
sudo apt-get install git

# macOS
brew install git

# Windows
# Download from https://git-scm.com/download/win
```

### Error: "Could not resolve host: huggingface.co"

Check your internet connection and ensure huggingface.co is accessible:
```bash
ping huggingface.co
```

### Error: "Failed to clone dataset"

1. Check internet connectivity
2. Verify the repository URL is correct
3. Ensure you have sufficient disk space
4. Check that the destination directory is writable

### Dataset Already Exists

If you want to re-clone the dataset:
```bash
# Remove existing dataset
rm -rf data/raw/deepfurniture

# Clone again
python clone_deepfurniture.py
```

Or use the API with `skip_if_exists=false`:
```bash
curl -X POST "http://localhost:8000/clone-deepfurniture?skip_if_exists=false"
```

## Technical Details

### Implementation

The DeepFurniture integration uses:
- `utils_kaggle.huggingface_clone()`: Core cloning function
- `clone_deepfurniture.py`: Standalone CLI script
- `/clone-deepfurniture` endpoint: FastAPI endpoint
- Modified `/download` endpoint: Handles both Kaggle and Hugging Face sources

### Skip Logic

The skip logic checks if:
1. The destination directory exists
2. The directory contains at least 5 files

If both conditions are met and `skip_if_exists=True`, the clone is skipped.

### Data Flow

```
Hugging Face → git clone → data/raw/deepfurniture → prepare_data.py → 
data/clean256 → train_multi.py → models/
```

## Testing

Run the test suite to verify the integration:

```bash
python test_deepfurniture.py
```

This validates:
- Catalog entry configuration
- Skip logic functionality
- Function signatures
- Git availability

## Support

For issues or questions:
1. Check the logs for detailed error messages
2. Ensure all requirements are met
3. Review the troubleshooting section
4. Check the GitHub repository issues

## Next Steps

After cloning the DeepFurniture dataset:

1. **Prepare Data**: Run data preparation to validate and process images
2. **Train Models**: Train on the combined dataset (Kaggle + DeepFurniture)
3. **Run Inference**: Use trained models for furniture classification

See the main [README.md](README.md) for complete workflow instructions.
