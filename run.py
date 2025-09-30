"""
Application entry point.

Run the FastAPI application using Uvicorn server.
"""

import uvicorn

from app.main import app

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
        workers=1
    )