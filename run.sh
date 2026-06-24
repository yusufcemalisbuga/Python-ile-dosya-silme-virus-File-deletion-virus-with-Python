#!/bin/bash
# Quick start script for Real-Time AI Camera Analytics

echo "=== Real-Time AI Camera Analytics ==="
echo ""

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not installed."
    exit 1
fi

# Install dependencies if needed
if ! python3 -c "import fastapi" 2>/dev/null; then
    echo "Installing dependencies..."
    pip install -e .
fi

# Install yt-dlp for YouTube support
if ! command -v yt-dlp &> /dev/null; then
    echo "Installing yt-dlp for YouTube stream support..."
    pip install yt-dlp
fi

# Check for API key
if [ -z "$ROBOFLOW_API_KEY" ]; then
    echo ""
    echo "⚠️  No ROBOFLOW_API_KEY set - running in DEMO MODE"
    echo "   Get a free API key at: https://universe.roboflow.com/"
    echo "   Set it with: export ROBOFLOW_API_KEY='your_key'"
    echo ""
fi

echo "Starting server at http://localhost:8000"
echo "Press Ctrl+C to stop"
echo ""

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
