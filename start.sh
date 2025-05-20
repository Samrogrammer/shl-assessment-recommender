#!/bin/bash

# Start FastAPI (ensure correct directory)
cd /app/app && \
uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} &

# Start Streamlit (with explicit backend URL)
cd /app && \
API_URL="https://shl-assessment-recommender-7znk.onrender.com" \
streamlit run streamlit_app.py --server.port ${STREAMLIT_PORT:-8501} --server.address=0.0.0.0