"""
SHL Assessment Recommendation - Streamlit Frontend

A simple web user interface for the SHL Assessment Recommendation .
"""

import streamlit as st
import requests
import json
import os
import pandas as pd
from typing import List, Dict, Any


# Constants
API_URL = os.getenv("API_URL", "shl-assessment-project.up.railway.app")  #  Use Railway URL
RECOMMENDATION_ENDPOINT = f"{API_URL}/recommend"
UPLOAD_ENDPOINT = f"{API_URL}/upload"
CATALOG_ENDPOINT = f"{API_URL}/catalog"

# Page configuration
st.set_page_config(
    page_title="SHL Assessment Recommender",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Helper functions
def get_recommendations(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """Get recommendations from the API"""
    try:
        response = requests.post(
            RECOMMENDATION_ENDPOINT,
            json={"query": query, "top_k": top_k}
        )
        response.raise_for_status()
        return response.json()["recommendations"]
    except Exception as e:
        st.error(f"Error fetching recommendations: {str(e)}")
        return []

def upload_catalog(file):
    """Upload a new catalog to the API"""
    try:
        files = {"file": file}
        response = requests.post(UPLOAD_ENDPOINT, files=files)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error uploading catalog: {str(e)}")
        return None

def get_catalog():
    """Get the current assessment catalog"""
    try:
        response = requests.get(f"{CATALOG_ENDPOINT}?limit=100")
        response.raise_for_status()
        return response.json()["assessments"]
    except Exception as e:
        st.error(f"Error fetching catalog: {str(e)}")
        return []

# Sidebar
st.sidebar.title("SHL Assessment Recommender")
st.sidebar.markdown("A local vector-similarity based recommendation system for SHL assessments that recommends the most relevant assessments based on job descriptions or skills.")

# Sidebar navigation
page = st.sidebar.radio("Navigation", ["Get Recommendations", "View Catalog", "Upload Catalog"])

# Main content
if page == "Get Recommendations":
    st.title("🎯 SHL Assessment Recommender")
    st.markdown("""
    Enter a job title, skills, or full job description to get personalized SHL assessment recommendations.
    The system uses semantic similarity to find the most relevant assessments.
    """)
    
    # Query input
    query = st.text_area(
        "Job Title, Skills, or Description",
        height=150,
        placeholder="e.g., Senior Data Scientist with experience in machine learning, Python, and statistical analysis..."
    )
    
    # Number of recommendations
    top_k = st.slider("Number of recommendations", min_value=1, max_value=10, value=5)
    
    # Get recommendations button
    if st.button("Get Recommendations"):
        if query:
            with st.spinner("Finding the best assessments..."):
                recommendations = get_recommendations(query, top_k)
            
            if recommendations:
                st.success(f"Found {len(recommendations)} relevant assessments")
                
                # Display recommendations
                for i, rec in enumerate(recommendations):
                    with st.expander(f"{i+1}. {rec['name']} (Similarity: {rec['similarity_score']:.4f})", expanded=True):
                        st.markdown(f"**Category:** {rec['category']}")
                        st.markdown(f"**Duration:** {rec['duration_minutes']} minutes")
                        st.markdown(f"**Description:** {rec['description']}")
                        st.markdown(f"**Tags:** {', '.join(rec['tags'])}")
                        st.markdown(f"**Recommended Roles:** {', '.join(rec['recommended_roles'])}")
            else:
                st.warning("No recommendations found. Try a different query.")
        else:
            st.warning("Please enter a job title, skills, or description.")
    
    # Example queries
    with st.expander("Example Queries"):
        example_queries = [
            "Data Scientist with Python and machine learning experience",
            "Sales Manager with customer relationship skills",
            "Software Engineer proficient in Java and cloud technologies",
            "Financial Analyst with Excel and accounting knowledge",
            "Project Manager with Agile methodology experience"
        ]
        
        for example in example_queries:
            if st.button(example):
                st.session_state["query"] = example
                st.experimental_rerun()

elif page == "View Catalog":
    st.title("📚 Assessment Catalog")
    st.markdown("View all available SHL assessments in the system.")
    
    # Fetch catalog
    with st.spinner("Loading catalog..."):
        catalog = get_catalog()
    
    if catalog:
        # Convert to DataFrame for better display
        df = pd.DataFrame(catalog)
        
        # Select columns to display
        display_cols = ["id", "name", "category", "duration_minutes"]
        st.dataframe(df[display_cols])
        
        # Detailed view
        selected_assessment = st.selectbox("Select assessment for details", df["name"].tolist())
        if selected_assessment:
            assessment = next((item for item in catalog if item["name"] == selected_assessment), None)
            if assessment:
                st.subheader(assessment["name"])
                st.markdown(f"**Category:** {assessment['category']}")
                st.markdown(f"**Duration:** {assessment['duration_minutes']} minutes")
                st.markdown(f"**Description:** {assessment['description']}")
                st.markdown(f"**Tags:** {', '.join(assessment['tags'])}")
                st.markdown(f"**Recommended Roles:** {', '.join(assessment['recommended_roles'])}")
    else:
        st.warning("No assessments found in the catalog.")

elif page == "Upload Catalog":
    st.title("📤 Upload New Catalog")
    st.markdown("""
    Upload a new JSON catalog file to replace the current assessment catalog.
    
    **File Format:**
    ```json
    [
        {
            "id": "shl-001",
            "name": "Assessment Name",
            "description": "Description text...",
            "tags": ["tag1", "tag2"],
            "category": "Category",
            "duration_minutes": 30,
            "recommended_roles": ["Role1", "Role2"]
        },
        ...
    ]
    ```
    """)
    
    uploaded_file = st.file_uploader("Choose a JSON file", type="json")
    
    if uploaded_file is not None:
        if st.button("Upload and Replace Catalog"):
            with st.spinner("Uploading and processing catalog..."):
                result = upload_catalog(uploaded_file)
            
            if result:
                st.success(f"Catalog successfully uploaded: {result['message']}")
            else:
                st.error("Failed to upload catalog")

# Add a footer
st.sidebar.markdown("---")
st.sidebar.markdown("SHL Assessment Recommendation Engine")
st.sidebar.markdown("Powered by sentence-transformers & FAISS")