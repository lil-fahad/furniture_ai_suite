# API Usage Examples

This document provides practical examples for using the Interior Design AI Suite API.

## Base URL

When running locally:
```
http://localhost:8000
```

## Interactive Documentation

Visit these URLs for interactive API documentation:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Example Workflows

### Complete Pipeline

```bash
# 1. Check health
curl http://localhost:8000/health

# 2. Download datasets
curl -X POST http://localhost:8000/download

# 3. Prepare data
curl -X POST http://localhost:8000/prepare

# 4. Train models
curl -X POST http://localhost:8000/train

# 5. Get available labels
curl http://localhost:8000/labels

# 6. Predict on an image
curl -X POST http://localhost:8000/predict \
  -F "file=@/path/to/your/image.jpg" \
  -F "topk=5"

# 7. Analyze a floor plan (NEW)
curl -X POST http://localhost:8000/analyze-floor-plan \
  -F "file=@/path/to/floor_plan.jpg" \
  -F "save_visualization=true"

# 8. Get furniture recommendations (NEW)
curl -X GET "http://localhost:8000/furniture-recommendations?room_type=bedroom&area_sqm=20"
```

### Using Python

```python
import requests

BASE_URL = "http://localhost:8000"

# Health check
response = requests.get(f"{BASE_URL}/health")
print(response.json())

# Download datasets
response = requests.post(f"{BASE_URL}/download")
print(response.json())

# Prepare data
response = requests.post(f"{BASE_URL}/prepare")
print(response.json())

# Train models
response = requests.post(f"{BASE_URL}/train")
results = response.json()
print(f"Best model: {results['best_model']} with accuracy: {results['best_accuracy']}")

# Get labels
response = requests.get(f"{BASE_URL}/labels")
labels = response.json()
print(f"Available categories: {labels['labels']}")

# Make prediction
with open("interior_image.jpg", "rb") as f:
    files = {"file": f}
    params = {"topk": 3}
    response = requests.post(f"{BASE_URL}/predict", files=files, params=params)
    
predictions = response.json()
print("Predictions:")
for pred in predictions["predictions"]:
    print(f"  {pred['label']}: {pred['confidence']:.2%} (Rank {pred['rank']})")

# Analyze floor plan (NEW)
with open("floor_plan.jpg", "rb") as f:
    files = {"file": f}
    params = {"save_visualization": True}
    response = requests.post(f"{BASE_URL}/analyze-floor-plan", files=files, params=params)

floor_plan_analysis = response.json()
print(f"Detected {floor_plan_analysis['analysis']['total_rooms']} rooms")
for room in floor_plan_analysis['analysis']['rooms']:
    print(f"\nRoom {room['id']}: {room['type']}")
    print(f"  Area: {room['area_pixels']} pixels")
    if 'furniture_recommendations' in room:
        print("  Recommended furniture:")
        for item in room['furniture_recommendations']:
            print(f"    - {item['item']} ({item['priority']})")

# Get furniture recommendations (NEW)
response = requests.get(
    f"{BASE_URL}/furniture-recommendations",
    params={"room_type": "bedroom", "area_sqm": 20}
)
recommendations = response.json()
print(f"\nFurniture recommendations for {recommendations['room_type']}:")
for item in recommendations['recommendations']:
    print(f"  - {item['item']} ({item['priority']})")
```

### Using JavaScript (fetch)

```javascript
const BASE_URL = 'http://localhost:8000';

// Health check
async function checkHealth() {
    const response = await fetch(`${BASE_URL}/health`);
    const data = await response.json();
    console.log(data);
}

// Download datasets
async function downloadDatasets() {
    const response = await fetch(`${BASE_URL}/download`, {
        method: 'POST'
    });
    const data = await response.json();
    console.log(data);
}

// Predict on image
async function predictImage(imageFile) {
    const formData = new FormData();
    formData.append('file', imageFile);
    
    const response = await fetch(`${BASE_URL}/predict?topk=5`, {
        method: 'POST',
        body: formData
    });
    
    const data = await response.json();
    console.log('Predictions:', data.predictions);
    return data;
}

// Analyze floor plan (NEW)
async function analyzeFloorPlan(floorPlanFile, saveVisualization = true) {
    const formData = new FormData();
    formData.append('file', floorPlanFile);
    
    const response = await fetch(
        `${BASE_URL}/analyze-floor-plan?save_visualization=${saveVisualization}`,
        {
            method: 'POST',
            body: formData
        }
    );
    
    const data = await response.json();
    console.log('Floor plan analysis:', data.analysis);
    return data;
}

// Get furniture recommendations (NEW)
async function getFurnitureRecommendations(roomType, areaSqm) {
    const response = await fetch(
        `${BASE_URL}/furniture-recommendations?room_type=${roomType}&area_sqm=${areaSqm}`
    );
    
    const data = await response.json();
    console.log('Recommendations:', data.recommendations);
    return data;
}

// Get training results
async function getResults() {
    const response = await fetch(`${BASE_URL}/results`);
    const data = await response.json();
    console.log('Models:', data.models);
    return data;
}
```

## Response Examples

### Health Check Response

```json
{
  "status": "healthy",
  "service": "Interior Design AI Suite",
  "version": "2.0.0"
}
```

### Download Response

```json
{
  "ok": true,
  "message": "All datasets processed successfully",
  "datasets_processed": 4,
  "downloaded": 0,
  "skipped": 4
}
```

### Prepare Response

```json
{
  "ok": true,
  "message": "Data preparation completed successfully",
  "total_images_found": 15234,
  "valid_images": 14892,
  "output_directory": "data/clean256"
}
```

### Train Response

```json
{
  "ok": true,
  "message": "Model training completed successfully",
  "results": [
    {
      "model": "efficientnet_b0",
      "val_acc": 0.9245,
      "ckpt": "models/best_efficientnet_b0.pth",
      "epochs_trained": 12
    },
    {
      "model": "convnext_tiny",
      "val_acc": 0.9156,
      "ckpt": "models/best_convnext_tiny.pth",
      "epochs_trained": 10
    },
    {
      "model": "swin_tiny_patch4_window7_224",
      "val_acc": 0.9089,
      "ckpt": "models/best_swin_tiny_patch4_window7_224.pth",
      "epochs_trained": 11
    }
  ],
  "best_model": "efficientnet_b0",
  "best_accuracy": 0.9245
}
```

### Predict Response

```json
{
  "ok": true,
  "message": "Prediction completed successfully",
  "model": "efficientnet_b0",
  "model_accuracy": 0.9245,
  "predictions": [
    {
      "label": "bedroom",
      "confidence": 0.8923,
      "rank": 1
    },
    {
      "label": "living_room",
      "confidence": 0.0567,
      "rank": 2
    },
    {
      "label": "dining_room",
      "confidence": 0.0234,
      "rank": 3
    }
  ],
  "top_prediction": {
    "label": "bedroom",
    "confidence": 0.8923,
    "rank": 1
  }
}
```

### Labels Response

```json
{
  "ok": true,
  "count": 15,
  "labels": [
    "bathroom",
    "bedroom",
    "dining_room",
    "kitchen",
    "living_room",
    "office",
    "...and more"
  ]
}
```

### Results Response

```json
{
  "ok": true,
  "count": 3,
  "models": [
    {
      "model": "efficientnet_b0",
      "val_acc": 0.9245,
      "ckpt": "models/best_efficientnet_b0.pth",
      "epochs_trained": 12
    }
  ],
  "best_model": {
    "model": "efficientnet_b0",
    "val_acc": 0.9245,
    "ckpt": "models/best_efficientnet_b0.pth",
    "epochs_trained": 12
  }
}
```

### Floor Plan Analysis Response (NEW)

```json
{
  "ok": true,
  "message": "Floor plan analysis completed successfully",
  "filename": "house_plan.jpg",
  "analysis": {
    "total_rooms": 5,
    "total_area_pixels": 345600,
    "wall_count": 23,
    "rooms": [
      {
        "id": 0,
        "type": "living_room",
        "area_pixels": 89500,
        "bounding_box": {"x": 120, "y": 80, "width": 450, "height": 320},
        "centroid": {"x": 345, "y": 240},
        "aspect_ratio": 1.41,
        "furniture_recommendations": [
          {"item": "sofa", "priority": "essential"},
          {"item": "coffee_table", "priority": "essential"},
          {"item": "tv_stand", "priority": "recommended"},
          {"item": "armchair", "priority": "optional"}
        ]
      },
      {
        "id": 1,
        "type": "bedroom",
        "area_pixels": 67200,
        "bounding_box": {"x": 600, "y": 100, "width": 380, "height": 290},
        "centroid": {"x": 790, "y": 245},
        "aspect_ratio": 1.31,
        "furniture_recommendations": [
          {"item": "bed", "priority": "essential"},
          {"item": "nightstand", "priority": "recommended"},
          {"item": "wardrobe", "priority": "essential"}
        ]
      }
    ],
    "doors": [
      {"x1": 300, "y1": 400, "x2": 360, "y2": 400, "length": 60.0},
      {"x1": 580, "y1": 240, "x2": 640, "y2": 240, "length": 60.0}
    ],
    "windows": [
      {"x1": 150, "y1": 80, "x2": 200, "y2": 80, "length": 50.0},
      {"x1": 720, "y1": 100, "x2": 765, "y2": 100, "length": 45.0}
    ]
  },
  "visualization_path": "artifacts/floor_plans/analyzed_house_plan.jpg"
}
```

### Furniture Recommendations Response (NEW)

```json
{
  "ok": true,
  "room_type": "bedroom",
  "area_sqm": 20,
  "recommendations": [
    {"item": "bed", "priority": "essential"},
    {"item": "nightstand", "priority": "recommended"},
    {"item": "wardrobe", "priority": "essential"},
    {"item": "dresser", "priority": "optional"}
  ],
  "total_items": 4
}
```

## Error Responses

All errors follow this format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

Common HTTP status codes:
- `200`: Success
- `400`: Bad Request (invalid input)
- `404`: Not Found (resource doesn't exist)
- `500`: Internal Server Error

### Example Error Response

```json
{
  "detail": "Training data not found. Please run /prepare endpoint first to prepare the dataset."
}
```

## Tips

1. **Sequential Workflow**: Always follow the order: download → prepare → train → predict
2. **Check Status**: Use `/health` to verify the service is running
3. **View Labels**: Call `/labels` after training to see available categories
4. **File Format**: Supported image formats: JPG, JPEG, PNG, BMP, WEBP
5. **Top-K Predictions**: Adjust `topk` parameter (1-10) to get more or fewer predictions
6. **Training Time**: Training can take several hours depending on your hardware
7. **Skip Downloads**: Set `skip_if_exists=true` (default) to avoid re-downloading datasets

## Troubleshooting

### "Kaggle credentials not found"
- Ensure `kaggle.json` is in `~/.kaggle/` or project root
- Or set `KAGGLE_USERNAME` and `KAGGLE_KEY` environment variables

### "Model not trained yet"
- Run the `/train` endpoint first
- Wait for training to complete (can take hours)

### "Invalid file type"
- Only upload image files (jpg, png, etc.)
- Check file extension is correct

### "Training data not found"
- Run `/download` first to get datasets
- Then run `/prepare` to process the data
- Finally run `/train`

## Advanced Usage

### Custom Training Parameters

Edit `model_config.yml` to customize:
- Batch size
- Learning rate
- Number of epochs
- Model architectures to train
- And more...

### Using Different Models

The system automatically selects the best model. To use a specific model, you can modify the training results file or train only that model.

### Deploying for Production

Export formats available in `artifacts/`:
- `model.pth`: PyTorch checkpoint
- `model.ts`: TorchScript (production)
- `model.onnx`: ONNX (cross-platform)

---

For more information, visit the interactive documentation at `/docs`.
