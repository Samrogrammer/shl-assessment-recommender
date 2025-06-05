#!/bin/bash

# Start FastAPI
cd app && \
uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} &

# Start Streamlit with correct API URL
cd .. && \
streamlit run streamlit_app.py \
    --server.port ${STREAMLIT_PORT:-8501} \
    --server.address=0.0.0.0 \
    --server.headless=true \
    --browser.gatherUsageStats=false