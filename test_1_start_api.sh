#!/bin/bash
# Test 1: FastAPI Web Application
echo "🚀 STARTING AI VIDEO AUTOMATION API SERVER"
echo
echo "The server will start on: http://localhost:8000"
echo "API Documentation: http://localhost:8000/docs"
echo "Health Check: http://localhost:8000/api/v1/health"
echo
echo "Press Ctrl+C to stop the server"
echo "================================"
echo

cd /home/labber/AI_VOICE_AUTOMATION
source venv/bin/activate
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000