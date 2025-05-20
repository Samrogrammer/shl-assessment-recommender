@echo off
echo SHL Assessment Recommendation Engine Launcher

REM Check if virtual environment exists
if not exist venv\ (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install requirements
echo Installing requirements...
pip install -r requirements.txt

REM Start API server in a new window
echo Starting FastAPI server...
start cmd /k "cd app && python -m uvicorn main:app --reload --port 8000"

REM Wait for API to start
echo Waiting for API to start...
timeout /t 3 /nobreak > nul

REM Start Streamlit frontend
echo Starting Streamlit frontend...
streamlit run streamlit_app.py


echo Shutting down...
