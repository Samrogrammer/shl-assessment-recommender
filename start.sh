#!/bin/bash

# Start FastAPI backnd
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} &

# Start Streamlit frontend
streamlit run streamlit_app.py --server.port 8501