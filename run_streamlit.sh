#!/usr/bin/env bash
# Script to run Streamlit web interface
# سكريبت لتشغيل واجهة Streamlit

echo "🚀 Starting Streamlit Web Interface..."
echo "تشغيل واجهة Streamlit..."

# Check if streamlit is installed
if ! command -v streamlit &> /dev/null; then
    echo "⚠️ Streamlit not found. Installing..."
    pip install streamlit
fi

# Run Streamlit
streamlit run streamlit_app.py --server.port 8501 --server.address 0.0.0.0

# If you want to run on a different port:
# streamlit run streamlit_app.py --server.port 8502
