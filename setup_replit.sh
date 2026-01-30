#!/usr/bin/env bash
# Setup script for Replit environment
# يستخدم هذا السكريبت لإعداد البيئة على Replit

echo "🚀 Setting up Interior Design AI Suite for Replit..."
echo "إعداد نظام تصميم الديكور الداخلي على Replit..."

# Install lightweight dependencies
echo "📦 Installing dependencies..."
pip install -q -r requirements-replit.txt

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p data/raw data/clean256 models artifacts

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚙️ Creating .env template..."
    cat > .env << 'EOF'
# Environment variables for Replit
# متغيرات البيئة لـ Replit

# CORS Configuration (allow all origins in development)
ALLOWED_ORIGINS=*

# GitHub Token (optional)
# GITHUB_TOKEN=your_token_here

# Kaggle Credentials (optional, for dataset downloads)
# KAGGLE_USERNAME=your_username
# KAGGLE_KEY=your_api_key
EOF
fi

echo "✅ Setup complete!"
echo "اكتمل الإعداد!"
echo ""
echo "🌐 To start the server, run:"
echo "لتشغيل الخادم، قم بتشغيل:"
echo "   uvicorn app:app --host 0.0.0.0 --port 8000"
echo ""
echo "📚 API documentation will be available at:"
echo "ستكون وثائق API متاحة على:"
echo "   http://localhost:8000/docs"
