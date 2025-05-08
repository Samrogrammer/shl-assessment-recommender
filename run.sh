#!/bin/bash

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install requirements if needed
pip install -r requirements.txt

# Start API server in background
echo "Starting FastAPI server..."
cd app
python -m uvicorn main:app --reload --port 8000 &
API_PID=$!
cd ..

# Wait a moment for API to start
sleep 2

# Start Streamlit frontend
echo "Starting Streamlit frontend..."
streamlit run streamlit_app.py

# Clean up when done
kill $API_PID