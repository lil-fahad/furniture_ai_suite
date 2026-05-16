@echo off
REM تشغيل المشروع الكامل (FastAPI + Streamlit)
REM Run the full suite (FastAPI + Streamlit)

python -m venv .venv
call .venv\Scripts\activate
pip install -r requirements.txt
python main.py
