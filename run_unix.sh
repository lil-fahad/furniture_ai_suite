#!/usr/bin/env bash
# تشغيل المشروع الكامل (FastAPI + Streamlit)
# Run the full suite (FastAPI + Streamlit)

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
