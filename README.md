# Professional Interior Design AI Suite

A state-of-the-art interior design classification system powered by deep learning. This professional-grade application provides a complete workflow from data acquisition to model training and inference.

## 🌟 Features

- **Multi-Source Dataset Integration**: Automatic download and integration of multiple interior design datasets from Kaggle
- **Advanced Data Processing**: Intelligent image validation, deduplication, and quality assurance
- **State-of-the-Art Models**: Training with multiple architectures (EfficientNet, ConvNeXt, Swin Transformer)
- **Floor Plan Analysis**: Advanced floor plan reading and room detection capabilities
- **Furniture Recommendations**: AI-powered furniture recommendations based on room analysis
- **Professional API**: RESTful API with comprehensive error handling and validation
- **Model Export**: Multiple format support (PyTorch, TorchScript, ONNX) for flexible deployment
- **Comprehensive Logging**: Detailed logging throughout the entire pipeline
- **High-Quality Documentation**: Well-documented codebase with type hints and docstrings
- **Extensive Furniture Database**: Large collection of furniture and interior design images

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- CUDA-capable GPU (optional, but recommended for training)
- Kaggle account and API credentials

### Installation

```bash
# Clone the repository
git clone https://github.com/lil-fahad/furniture_ai_suite.git
cd furniture_ai_suite

# Install dependencies
pip install -r requirements.txt
```

### Configuration

Set up your Kaggle credentials (choose one method):

1. **Default location**: Place `kaggle.json` in `~/.kaggle/`
2. **Project root**: Place `kaggle.json` in the project directory
3. **Environment variables**: Set `KAGGLE_USERNAME` and `KAGGLE_KEY`

### Running the Application

**Windows:**
```bash
run_windows.bat
```

**Mac/Linux:**
```bash
bash run_unix.sh
```

Then open your browser to: **http://localhost:8000/docs**

## 📖 API Documentation

### Complete Workflow

The system provides a structured workflow through the Swagger UI at `/docs`:

#### 1. **POST /download** - Download Datasets
Downloads all datasets specified in `datasets_catalog.json` from Kaggle.
- Skips already downloaded datasets by default
- Validates dataset integrity

#### 2. **POST /prepare** - Prepare Data
Processes raw images for training:
- Scans and validates all images
- Removes duplicates using perceptual hashing
- Filters by minimum size requirements
- Creates train/validation splits
- Resizes to uniform dimensions (256x256)

#### 3. **POST /train** - Train Models
Trains multiple deep learning models:
- EfficientNet-B0
- ConvNeXt Tiny
- Swin Transformer Tiny
- Automatic model selection based on validation accuracy
- Exports best model in multiple formats

#### 4. **POST /predict** - Make Predictions
Classifies interior design images:
- Upload any interior/furniture image
- Returns top-K predictions with confidence scores
- Uses the best trained model automatically

#### 5. **POST /analyze-floor-plan** - Analyze Floor Plans (NEW)
Analyzes floor plan images to extract architectural information:
- Detects individual rooms and their types
- Identifies walls, doors, and windows
- Estimates room dimensions and areas
- Provides furniture recommendations for each room
- Optional visualization output

#### 6. **POST /furniture-recommendations** - Get Furniture Suggestions (NEW)
Get AI-powered furniture recommendations:
- Specify room type and size
- Receive tailored furniture suggestions
- Prioritized recommendations (essential, recommended, optional)

#### 7. **GET /labels** - View Categories
Returns all possible classification categories.

#### 8. **GET /results** - View Training Results
Shows performance metrics for all trained models.

#### 9. **GET /health** - Health Check
Verifies API service status.

## 🏗️ Architecture

### Data Pipeline
```
Raw Datasets → Validation → Deduplication → Resizing → Train/Val Split
```

### Model Training
```
Multiple Architectures → Fine-tuning → Validation → Best Model Selection → Export
```

### Inference
```
Image Upload → Preprocessing → Model Prediction → Top-K Results
```

## 📊 Dataset Sources

The application integrates multiple high-quality interior design and furniture datasets:

1. **Bedroom Interior Dataset** - Bedroom design styles and layouts
2. **House Rooms Dataset** - Various room types and configurations
3. **Indoor Scenes** - General indoor environments
4. **Furniture Images** - Furniture classification dataset
5. **Architecture Images** - Architectural styles and interior designs (NEW)
6. **Furniture Detection Dataset** - Rooms with and without furniture (NEW)
7. **Home Depot Furniture** - Extensive home depot furniture catalog (NEW)
8. **Product Images** - Additional home decor and furniture items (NEW)

All datasets are automatically downloaded and integrated from Kaggle.

## 🏗️ Floor Plan Analysis

The system now includes advanced floor plan analysis capabilities:

### Features
- **Room Detection**: Automatically identify individual rooms in floor plans
- **Room Classification**: Estimate room types (bedroom, living room, kitchen, etc.)
- **Dimension Analysis**: Calculate room areas and aspect ratios
- **Wall Detection**: Identify walls and boundaries
- **Opening Detection**: Detect doors and windows
- **Furniture Recommendations**: Get AI-powered furniture suggestions for each room
- **Visualization**: Generate annotated floor plan images

### Usage Example
```python
# Analyze a floor plan
with open("floor_plan.jpg", "rb") as f:
    response = requests.post(
        "http://localhost:8000/analyze-floor-plan",
        files={"file": f},
        params={"save_visualization": True}
    )

results = response.json()
for room in results["analysis"]["rooms"]:
    print(f"Room {room['id']}: {room['type']}")
    print(f"  Area: {room['area_pixels']} pixels")
    print(f"  Furniture recommendations:")
    for item in room["furniture_recommendations"]:
        print(f"    - {item['item']} ({item['priority']})")
```

## 🔧 Technical Details

### Key Technologies
- **Framework**: FastAPI for high-performance API
- **Deep Learning**: PyTorch + timm for state-of-the-art models
- **Data Processing**: Pandas, PIL, Albumentations
- **Validation**: Perceptual hashing for duplicate detection
- **Export Formats**: PyTorch, TorchScript, ONNX

### Model Features
- Transfer learning from ImageNet
- Advanced data augmentation
- Early stopping with patience
- Cosine annealing learning rate schedule
- Mixed precision training support

### Data Quality
- Image validation and verification
- Minimum size filtering
- Perceptual duplicate detection
- Stratified train/validation splits
- High-quality image resampling (LANCZOS)

## 📝 Code Quality

This is a professional-grade codebase featuring:
- ✅ Comprehensive error handling
- ✅ Input validation on all endpoints
- ✅ Type hints throughout
- ✅ Detailed docstrings
- ✅ Structured logging
- ✅ CORS support for API accessibility
- ✅ RESTful API design
- ✅ Modular architecture

## 🛡️ Error Handling

The application provides detailed error messages for:
- Missing dependencies
- Invalid configurations
- Data processing failures
- Model training issues
- Prediction errors

## 📈 Performance

- Automatic device selection (CUDA/CPU)
- Efficient data loading with multi-worker support
- Pin memory for faster GPU transfers
- Batch processing for optimal throughput
- Model optimization with TorchScript

## 🌐 Deployment Ready

Multiple export formats for various deployment scenarios:
- **PyTorch (.pth)**: Full model flexibility
- **TorchScript (.ts)**: Production deployment
- **ONNX (.onnx)**: Cross-platform compatibility

## 📄 License

This project is open source and available under the MIT License.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📞 Support

For issues, questions, or suggestions, please open an issue on GitHub.

---

**Built with ❤️ for professional interior design AI applications**
