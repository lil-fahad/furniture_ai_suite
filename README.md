# Professional Interior Design AI Suite

A state-of-the-art interior design classification system powered by deep learning. This professional-grade application provides a complete workflow from data acquisition to model training and inference.

## 🎨 Available Interfaces

This suite provides **three different ways** to interact with the system:

### 1. 🌐 Streamlit Web Interface (NEW!)
**User-friendly web interface for non-technical users**
- Beautiful, intuitive UI
- No coding required
- Perfect for demos and end-users
- Access: `http://localhost:8501`
- [Documentation](STREAMLIT_GUIDE.md)

### 2. 🔧 FastAPI REST API
**Professional API for developers and integrations**
- RESTful endpoints
- Swagger documentation
- Perfect for integrations
- Access: `http://localhost:8000/docs`
- [API Examples](API_EXAMPLES.md)

### 3. 💻 Command Line Interface
**Direct Python scripts for advanced users**
- Full control and customization
- Perfect for automation
- Training and batch processing

## 🌟 Features

- **Multi-Source Dataset Integration**: Automatic download and integration of multiple interior design datasets from Kaggle and Hugging Face (including DeepFurniture dataset)
- **Advanced Data Processing**: Intelligent image validation, deduplication, and quality assurance
- **State-of-the-Art Models**: Training with multiple architectures (EfficientNet, ConvNeXt, Swin Transformer)
- **Floor Plan Analysis**: Advanced floor plan reading and room detection capabilities
- **Furniture Recommendations**: AI-powered furniture recommendations based on room analysis
- **Alibaba Integration**: Search and retrieve furniture products from Alibaba marketplace
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

**On Streamlit (Web Interface):** 🌐 **NEW!**
```bash
# Install dependencies
pip install -r requirements.txt

# Run Streamlit web interface
streamlit run streamlit_app.py

# Or use the provided script
bash run_streamlit.sh  # Linux/Mac
run_streamlit.bat      # Windows
```
Access at: `http://localhost:8501`

See [STREAMLIT_GUIDE.md](STREAMLIT_GUIDE.md) for detailed Streamlit instructions.

**On Replit:** 🌐
```bash
# Simply click the "Run" button or use:
bash setup_replit.sh
# Then the app starts automatically
```
See [REPLIT_GUIDE.md](REPLIT_GUIDE.md) for detailed Replit deployment instructions.

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
Downloads all datasets specified in `datasets_catalog.json` from Kaggle and Hugging Face.
- Supports both Kaggle datasets and Hugging Face repositories
- Skips already downloaded datasets by default
- Validates dataset integrity

#### 1b. **POST /clone-deepfurniture** - Clone DeepFurniture Dataset
Clone the DeepFurniture dataset from Hugging Face:
- Clones from https://huggingface.co/datasets/byliu/DeepFurniture
- Uses git for efficient cloning
- Skips if already cloned by default
- Can also be run via command line: `python clone_deepfurniture.py`

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

#### 9. **POST /alibaba/search** - Search Alibaba Furniture (NEW)
Search for furniture products on Alibaba:
- Search by keyword (sofa, table, chair, etc.)
- Filter by category, price range
- Paginated results with product details
- Cached for performance
- Mock data for demonstration (production requires API access)

#### 10. **GET /alibaba/product/{id}** - Get Product Details (NEW)
Get detailed information about specific Alibaba product:
- Full specifications and pricing
- Supplier information and ratings
- Bulk pricing tiers
- Customer reviews and ratings

#### 11. **POST /alibaba/save-products** - Save Product Catalog (NEW)
Save searched products to local JSON file:
- Build local furniture catalog
- Batch product download
- Organized by search keyword

#### 12. **GET /alibaba/categories** - List Furniture Categories (NEW)
Get available furniture categories for search

#### 13. **GET /health** - Health Check
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

### Kaggle Datasets
1. **Bedroom Interior Dataset** - Bedroom design styles and layouts
2. **House Rooms Dataset** - Various room types and configurations
3. **Indoor Scenes** - General indoor environments
4. **Furniture Images** - Furniture classification dataset
5. **Architecture Images** - Architectural styles and interior designs
6. **Furniture Detection Dataset** - Rooms with and without furniture
7. **Home Depot Furniture** - Extensive home depot furniture catalog
8. **Product Images** - Additional home decor and furniture items

### Hugging Face Datasets
9. **DeepFurniture Dataset** - Large-scale furniture dataset from Hugging Face (NEW)
   - Repository: https://huggingface.co/datasets/byliu/DeepFurniture
   - Can be cloned via API endpoint `/clone-deepfurniture` or command line script
   - Integrates seamlessly with existing data processing pipeline

All datasets are automatically downloaded and integrated from their respective sources.

## 🛒 Alibaba Integration (NEW)

The system now includes integration with Alibaba to search and retrieve furniture products:

### Features
- **Product Search**: Search furniture by keywords and categories
- **Price Filtering**: Filter products by price range
- **Supplier Information**: View supplier ratings and locations
- **Bulk Pricing**: Access wholesale pricing tiers
- **Caching System**: Reduce API calls with intelligent caching
- **Rate Limiting**: Ethical scraping with configurable rate limits
- **Product Details**: Comprehensive product specifications

### Usage Example
```python
# Search for sofas on Alibaba
response = requests.post(
    "http://localhost:8000/alibaba/search",
    params={
        "keyword": "modern sofa",
        "category": "sofa",
        "min_price": 100,
        "max_price": 500,
        "page": 1
    }
)

products = response.json()["results"]["products"]
for product in products:
    print(f"{product['title']}: ${product['price']['amount']}")
    print(f"  Supplier: {product['supplier']['name']}")
    print(f"  MOQ: {product['moq']} pieces")

# Get detailed product info
product_id = products[0]["id"]
response = requests.get(f"http://localhost:8000/alibaba/product/{product_id}")
details = response.json()["product"]

# Save products to file
response = requests.post(
    "http://localhost:8000/alibaba/save-products",
    params={"keyword": "dining table", "max_results": 100}
)
print(f"Saved to: {response.json()['file_path']}")
```

### Important Notes
- **Demo Mode**: Current implementation uses simulated data for demonstration
- **Production Use**: Requires proper Alibaba API credentials or scraping authorization
- **Terms of Service**: Must comply with Alibaba's terms when scraping
- **Rate Limiting**: Built-in rate limiting to prevent server overload
- **Caching**: Responses cached for 24 hours to reduce API calls


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

### Deployment Options

#### 1. **Replit Deployment** 🌐 (ربط مع Replit)

Deploy easily on Replit for quick demos and testing:

**Quick Start:**
1. Import from GitHub: `https://github.com/lil-fahad/furniture_ai_suite`
2. Click "Run" button
3. Access API at your Replit URL

**Features Available:**
- ✅ Alibaba product search
- ✅ Floor plan analysis
- ✅ Furniture recommendations
- ✅ API documentation

**Read the complete guide:** [REPLIT_GUIDE.md](REPLIT_GUIDE.md)

**Note:** Heavy ML training requires local deployment with GPU.

#### 2. **Local/Server Deployment**

Multiple export formats for various deployment scenarios:
- **PyTorch (.pth)**: Full model flexibility
- **TorchScript (.ts)**: Production deployment
- **ONNX (.onnx)**: Cross-platform compatibility

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment options (Docker, AWS, GCP, Azure).

## 🧪 Testing & Verification (اختبار والتحقق)

The system has been comprehensively tested and verified:

### Test Results
- **Total Tests**: 5
- **Passed**: 5 ✓
- **Failed**: 0 ✗
- **Overall Accuracy**: 100%

### Run Tests
```bash
# Run accuracy tests
python3 test_accuracy.py

# Run feature demo
python3 demo.py
```

### Test Coverage
- ✓ Module imports and dependencies
- ✓ Alibaba furniture search functionality
- ✓ Floor plan analysis and room detection
- ✓ Furniture recommendations
- ✓ Dataset catalog validation
- ✓ Configuration validation

See [TESTING_REPORT.md](TESTING_REPORT.md) for detailed results.

---

## 📝 License

This project is open source and available under the MIT License.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📞 Support

For issues, questions, or suggestions, please open an issue on GitHub.

---

**Built with ❤️ for professional interior design AI applications**
