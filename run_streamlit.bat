@echo off
REM Script to run Streamlit web interface
REM سكريبت لتشغيل واجهة Streamlit

echo Starting Streamlit Web Interface...
echo تشغيل واجهة Streamlit...

REM Check if streamlit is installed
streamlit --version >nul 2>&1
if errorlevel 1 (
    echo Streamlit not found. Installing...
    pip install streamlit
)

REM Run Streamlit
streamlit run streamlit_app.py

REM If you want to run on a different port:
REM streamlit run streamlit_app.py --server.port 8502
