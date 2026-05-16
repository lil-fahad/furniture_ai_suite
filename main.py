#!/usr/bin/env python3
"""
نقطة الدخول الموحدة لـ Interior Design AI Suite
Unified Entry Point for the Interior Design AI Suite

الاستخدام / Usage:
  python main.py           → يشغّل FastAPI + Streamlit معاً  (API + Web)
  python main.py --api     → يشغّل FastAPI فقط   (port 8000)
  python main.py --web     → يشغّل Streamlit فقط  (port 8501)
"""

import argparse
import logging
import os
import subprocess
import sys
import threading

import uvicorn

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

API_PORT = int(os.getenv("PORT", 8000))
WEB_PORT = int(os.getenv("STREAMLIT_PORT", 8501))


def run_api() -> None:
    """تشغيل خادم FastAPI / Start the FastAPI server."""
    logger.info("🚀 Starting FastAPI server on port %d ...", API_PORT)
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=API_PORT,
        log_level="info",
    )


def run_web() -> None:
    """تشغيل واجهة Streamlit / Start the Streamlit web interface."""
    logger.info("🌐 Starting Streamlit interface on port %d ...", WEB_PORT)
    subprocess.run(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            "streamlit_app.py",
            "--server.port",
            str(WEB_PORT),
            "--server.address",
            "0.0.0.0",
            "--server.headless",
            "true",
            "--browser.gatherUsageStats",
            "false",
        ],
        check=True,
    )


def run_all() -> None:
    """تشغيل FastAPI و Streamlit معاً / Run both FastAPI and Streamlit."""
    logger.info("🎨 Starting Interior Design AI Suite (API + Web Interface)")

    # Start FastAPI in a background daemon thread so it stops when Streamlit exits
    api_thread = threading.Thread(target=run_api, daemon=True, name="FastAPI")
    api_thread.start()

    logger.info("✅ FastAPI running at  http://0.0.0.0:%d", API_PORT)
    logger.info("📚 API docs at         http://localhost:%d/docs", API_PORT)
    logger.info("🌐 Streamlit UI at     http://localhost:%d", WEB_PORT)

    # Run Streamlit in the main thread (blocking — process ends when Streamlit exits)
    run_web()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Interior Design AI Suite — Unified Entry Point"
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--api",
        action="store_true",
        help="Run the FastAPI backend only (port %(default)s)",
    )
    group.add_argument(
        "--web",
        action="store_true",
        help="Run the Streamlit web interface only (port %(default)s)",
    )
    args = parser.parse_args()

    if args.api:
        run_api()
    elif args.web:
        run_web()
    else:
        run_all()


if __name__ == "__main__":
    main()
