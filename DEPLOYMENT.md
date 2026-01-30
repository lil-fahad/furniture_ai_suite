# Deployment Guide

This guide covers various deployment options for the Professional Interior Design AI Suite.

## Table of Contents

1. [Local Development](#local-development)
2. [Docker Deployment](#docker-deployment)
3. [Cloud Deployment](#cloud-deployment)
4. [Production Considerations](#production-considerations)
5. [Performance Optimization](#performance-optimization)

## Local Development

### Prerequisites

- Python 3.8 or higher
- 8GB+ RAM recommended
- GPU with CUDA support (optional, for training)
- 20GB+ free disk space for datasets and models

### Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/lil-fahad/furniture_ai_suite.git
   cd furniture_ai_suite
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   
   # Activate on Windows
   venv\Scripts\activate
   
   # Activate on Mac/Linux
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Kaggle credentials:**
   
   Place your `kaggle.json` in one of these locations:
   - `~/.kaggle/kaggle.json` (recommended)
   - Project root: `./kaggle.json`
   - Or set environment variables:
     ```bash
     export KAGGLE_USERNAME="your_username"
     export KAGGLE_KEY="your_api_key"
     ```

5. **Run the application:**
   ```bash
   # Windows
   run_windows.bat
   
   # Mac/Linux
   bash run_unix.sh
   
   # Or directly with uvicorn
   uvicorn app:app --host 0.0.0.0 --port 8000 --reload
   ```

6. **Access the API:**
   - API Documentation: http://localhost:8000/docs
   - Alternative Docs: http://localhost:8000/redoc
   - Health Check: http://localhost:8000/health

## Docker Deployment

### Option 1: Build Custom Image

1. **Create Dockerfile:**

```dockerfile
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p data models artifacts

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

2. **Create docker-compose.yml:**

```yaml
version: '3.8'

services:
  interior-ai:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - ./models:/app/models
      - ./artifacts:/app/artifacts
      - ~/.kaggle:/root/.kaggle:ro
    environment:
      - PYTHONUNBUFFERED=1
    restart: unless-stopped
```

3. **Build and run:**
   ```bash
   docker-compose up -d
   ```

### Option 2: Use Pre-built Image

```bash
# Pull image (when available)
docker pull your-registry/interior-ai-suite:latest

# Run container
docker run -d \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/models:/app/models \
  -v $(pwd)/artifacts:/app/artifacts \
  -v ~/.kaggle:/root/.kaggle:ro \
  --name interior-ai \
  your-registry/interior-ai-suite:latest
```

## Cloud Deployment

### AWS Deployment

#### Option A: EC2 Instance

1. **Launch EC2 Instance:**
   - AMI: Amazon Linux 2 or Ubuntu 20.04
   - Instance Type: t3.medium (minimum), p3.2xlarge (for training with GPU)
   - Storage: 50GB+ EBS volume
   - Security Group: Open port 8000

2. **Setup on EC2:**
   ```bash
   # Install dependencies
   sudo yum update -y
   sudo yum install -y python3 python3-pip git
   
   # Clone and setup application
   git clone https://github.com/lil-fahad/furniture_ai_suite.git
   cd furniture_ai_suite
   pip3 install -r requirements.txt
   
   # Configure and run
   uvicorn app:app --host 0.0.0.0 --port 8000
   ```

3. **Use systemd for auto-restart:**
   
   Create `/etc/systemd/system/interior-ai.service`:
   ```ini
   [Unit]
   Description=Interior Design AI Suite
   After=network.target
   
   [Service]
   Type=simple
   User=ec2-user
   WorkingDirectory=/home/ec2-user/furniture_ai_suite
   ExecStart=/usr/local/bin/uvicorn app:app --host 0.0.0.0 --port 8000
   Restart=always
   
   [Install]
   WantedBy=multi-user.target
   ```
   
   Enable and start:
   ```bash
   sudo systemctl enable interior-ai
   sudo systemctl start interior-ai
   ```

#### Option B: AWS Elastic Beanstalk

1. **Install EB CLI:**
   ```bash
   pip install awsebcli
   ```

2. **Initialize:**
   ```bash
   eb init -p python-3.10 interior-ai-suite
   ```

3. **Create environment:**
   ```bash
   eb create interior-ai-prod
   ```

4. **Deploy updates:**
   ```bash
   eb deploy
   ```

#### Option C: AWS Lambda + API Gateway (Inference Only)

For serving predictions without training:

1. Package the application with dependencies
2. Create Lambda function with container image
3. Set up API Gateway to trigger Lambda
4. Store model in S3 and load on cold start

### Google Cloud Platform

#### Using Cloud Run

1. **Build container:**
   ```bash
   gcloud builds submit --tag gcr.io/your-project/interior-ai
   ```

2. **Deploy:**
   ```bash
   gcloud run deploy interior-ai \
     --image gcr.io/your-project/interior-ai \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --memory 4Gi \
     --cpu 2
   ```

### Microsoft Azure

#### Using Azure Container Instances

```bash
az container create \
  --resource-group interior-ai-rg \
  --name interior-ai \
  --image your-registry/interior-ai:latest \
  --dns-name-label interior-ai \
  --ports 8000
```

## Production Considerations

### Security

1. **API Authentication:**
   
   Add authentication middleware to `app.py`:
   ```python
   from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
   
   security = HTTPBearer()
   
   @app.middleware("http")
   async def verify_token(request: Request, call_next):
       # Implement your auth logic
       response = await call_next(request)
       return response
   ```

2. **HTTPS/SSL:**
   - Use reverse proxy (nginx, Caddy) with SSL certificates
   - Or use cloud load balancer with SSL termination

3. **Rate Limiting:**
   ```bash
   pip install slowapi
   ```
   
   Add to app.py:
   ```python
   from slowapi import Limiter, _rate_limit_exceeded_handler
   from slowapi.util import get_remote_address
   from slowapi.errors import RateLimitExceeded
   
   limiter = Limiter(key_func=get_remote_address)
   app.state.limiter = limiter
   app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
   
   @app.post("/predict")
   @limiter.limit("10/minute")
   async def predict(...):
       ...
   ```

### Monitoring and Logging

1. **Application Monitoring:**
   - Use Prometheus + Grafana
   - CloudWatch (AWS)
   - Stackdriver (GCP)
   - Application Insights (Azure)

2. **Error Tracking:**
   - Sentry integration
   - CloudWatch Logs
   - ELK Stack

3. **Add health checks:**
   Already implemented at `/health` endpoint

### Database Integration

For production use cases with user management:

```python
# Install SQLAlchemy
pip install sqlalchemy psycopg2-binary

# Add database models for users, predictions, etc.
```

### Caching

For improved performance:

```python
# Install Redis
pip install redis

# Cache predictions
from redis import Redis
cache = Redis(host='localhost', port=6379, db=0)
```

## Performance Optimization

### Model Serving

1. **Use TorchScript:**
   The system already exports TorchScript models. Load them for faster inference:
   ```python
   model = torch.jit.load('artifacts/model.ts')
   ```

2. **Batch Predictions:**
   Modify predict endpoint to accept multiple images

3. **Model Quantization:**
   ```python
   quantized_model = torch.quantization.quantize_dynamic(
       model, {torch.nn.Linear}, dtype=torch.qint8
   )
   ```

### Infrastructure

1. **Use CDN:**
   - CloudFront (AWS)
   - Cloud CDN (GCP)
   - Azure CDN

2. **Load Balancing:**
   - Multiple API instances behind load balancer
   - Auto-scaling based on traffic

3. **GPU Optimization:**
   - Use GPU instances for training
   - Consider mixed precision training (FP16)

### Code Optimization

1. **Async/Await:**
   Already implemented in the API

2. **Connection Pooling:**
   For database connections

3. **Caching:**
   Cache model loading, frequently accessed data

## Scaling Strategy

### Horizontal Scaling

1. **Separate Services:**
   - Training service (background workers)
   - Inference service (API)
   - Data processing service

2. **Use Message Queue:**
   - RabbitMQ or AWS SQS for training jobs
   - Celery for task distribution

### Vertical Scaling

1. **Training:**
   - Use larger GPU instances (p3.8xlarge, p3.16xlarge)
   - Multi-GPU training

2. **Inference:**
   - Increase CPU/RAM for API servers
   - Use GPU for batch inference

## Backup and Recovery

1. **Model Checkpoints:**
   - Regularly backup `models/` and `artifacts/` directories
   - Use versioned storage (S3 versioning, GCS versioning)

2. **Data Backup:**
   - Backup processed datasets
   - Store in cloud storage with redundancy

3. **Configuration:**
   - Version control all configuration files
   - Document environment-specific settings

## Cost Optimization

1. **Use Spot Instances:**
   For training jobs (AWS Spot, GCP Preemptible)

2. **Storage Classes:**
   - Use cheaper storage for infrequently accessed data
   - S3 Intelligent-Tiering, Glacier for archives

3. **Auto-scaling:**
   - Scale down during low traffic
   - Schedule training jobs during off-peak hours

## Monitoring Checklist

- [ ] API response times
- [ ] Error rates
- [ ] Model prediction latency
- [ ] System resource usage (CPU, RAM, GPU)
- [ ] Disk space
- [ ] Network traffic
- [ ] Request counts by endpoint
- [ ] Training job success/failure rates

## Security Checklist

- [ ] HTTPS enabled
- [ ] Authentication implemented
- [ ] Rate limiting configured
- [ ] Input validation on all endpoints
- [ ] Secrets stored securely (not in code)
- [ ] Regular security updates
- [ ] Firewall rules configured
- [ ] Data encryption at rest and in transit

---

For questions or issues, please open an issue on GitHub.
