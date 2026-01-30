#!/usr/bin/env python3
"""
Main entry point for Replit deployment.
This file can be used as an alternative to running uvicorn directly.

نقطة الدخول الرئيسية لنشر Replit
"""

import os
import uvicorn

if __name__ == "__main__":
    # Get port from environment (Replit uses this)
    port = int(os.getenv("PORT", 8000))
    
    # Start the server
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )
