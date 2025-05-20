🚀 SHL Assessment Recommendation Engine

This is a  AI-powered recommendation system designed to suggest the most relevant SHL assessments for a given job role, skills list, or job description — all without needing cloud services or external APIs.

Whether you're an HR tech enthusiast or just exploring GenAI projects, this tool gives you a practical example of combining embeddings, vector search, and a modern API layer.
🔍 What It Does

    Locally runs everything – No OpenAI, no cloud. All embeddings and vector searches happen on your machine.

    Smart matching – Uses sentence transformers to understand the meaning of input and catalog descriptions.

    Fast, scalable search – Powered by FAISS for fast vector similarity matching.

    API-first – Built with FastAPI and Swagger docs out of the box.

    Flexible input – Accepts short job titles or detailed descriptions.

🛠️ Tech Stack

    Python 3.10+

    FastAPI

    Sentence-Transformers (all-MiniLM-L6-v2)

    FAISS for indexing & search

    Streamlit (frontend)





🚦 Running the App
Option 1: All-in-one launch

Windows:

run.bat

Linux/macOS:

chmod +x run.sh
./run.sh

This will spin up both the FastAPI backend and Streamlit frontend.
Option 2: Run API and frontend separately
API (FastAPI)

cd app
uvicorn main:app --reload

Docs at: (https://shl-assessment-project.up.railway.app/)/docs
Frontend (Streamlit)

streamlit run streamlit_app.py

UI at: http://localhost:8501


🧠 How It Works

    Embeddings: Converts input and catalog descriptions into embeddings using all-MiniLM-L6-v2.

    FAISS Index: Catalog embeddings are indexed for fast similarity search.

    Query Match: Input queries are matched against catalog embeddings by cosine similarity.

    Top Matches: Returns most relevant assessments in descending order of similarity.

📂 Project Structure

shl-recommendation-engine/
├── app/
│   ├── main.py              # FastAPI backend
│   ├── recommender.py       # Embedding & similarity logic
│   └── data/
│       └── catalog.json     # Sample product catalog
├── evaluate.py              # Scoring and test evaluation
├── streamlit_app.py         # Optional web interface
├── run.sh / run.bat         # Launch scripts
├── requirements.txt
└── README.md


🤝 Contribute or Customize

This project can be a starting point for:

    Building a GenAI-powered HR tool

    Integrating into a recruitment system

    Experimenting with semantic search

Pull requests and feedback welcome!