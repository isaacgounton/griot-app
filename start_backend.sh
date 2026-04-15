#!/bin/bash

# Start backend server for testing
echo "🚀 Starting Griot backend for testing..."
echo "📍 Backend will be available at: http://localhost:8000"
echo "📍 Frontend will be available at: http://localhost:3000"
echo "📍 API docs at: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# The .env file is automatically loaded by python-dotenv in app.main.py
# No need to export variables here - it can cause quote issues

# Start the server using UV
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload