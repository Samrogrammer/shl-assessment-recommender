#!/bin/bash

# Start FastAPI backnd
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} &

streamlit run streamlit_app.py --server.port ${STREAMLIT_PORT:-8501} --server.address=0.0.0.0