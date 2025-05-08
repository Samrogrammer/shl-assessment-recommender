from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
import json
import logging
import uvicorn

from recommender import SHLRecommender, get_default_catalog_path


#  logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

#  API models
class RecommendationRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5

class RecommendationResponse(BaseModel):
    recommendations: List[Dict[str, Any]]
    query: str

# Initializes FastAPI app
app = FastAPI(
    title="SHL Assessment Recommendation Engine",
    description="A local vector-search based recommendation system for SHL assessments",
    version="1.0.0"
)

#  CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create a global instance of the recommender
catalog_path = get_default_catalog_path()
recommender = SHLRecommender(catalog_path=catalog_path)

@app.get("/")
def read_root():
    """Root endpoint with basic API information"""
    return {
        "name": "SHL Assessment Recommendation Engine",
        "version": "1.0.0",
        "status": "active",
        "endpoints": [
            {"path": "/recommend", "method": "POST", "description": "Get assessment recommendations"},
            {"path": "/upload", "method": "POST", "description": "Upload and index a new catalog"},
            {"path": "/catalog", "method": "GET", "description": "View current catalog"}
        ]
    }

@app.post("/recommend", response_model=RecommendationResponse)
async def recommend_assessments(request: RecommendationRequest):
    """
    Get SHL assessment recommendations based on job role, skills, or description
    
    Parameters:
    - query: Job role, skills list, or job description
    - top_k: Number of recommendations to return (default: 5)
    
    Returns:
    - List of recommended assessments with similarity scores
    """
    try:
        recommendations = recommender.recommend(query=request.query, top_k=request.top_k)
        return {
            "recommendations": recommendations,
            "query": request.query
        }
    except Exception as e:
        logger.error(f"Error generating recommendations: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating recommendations: {str(e)}")

@app.post("/upload")
async def upload_catalog(file: UploadFile = File(...)):
    """
    Uploads and index a new SHL assessment catalog
    
    Parameters:
    - file: JSON file containing assessment catalog data
    
    Returns:
    - Success message with number of indexed assessments
    """
    if not file.filename.endswith('.json'):
        raise HTTPException(status_code=400, detail="Only JSON files are accepted")
    
    try:
        # Read and parse the uploaded file
        contents = await file.read()
        catalog_data = json.loads(contents)
        
        # Validates catalog structure
        if not isinstance(catalog_data, list):
            raise HTTPException(status_code=400, detail="Catalog must be a JSON array of assessments")
        
        # Updates with new catalog data
        recommender.update_catalog(catalog_data)
        
        return {
            "status": "success",
            "message": f"Successfully indexed {len(catalog_data)} assessments"
        }
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format")
    except Exception as e:
        logger.error(f"Error processing catalog upload: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing catalog: {str(e)}")

@app.get("/catalog")
async def get_catalog(limit: int = Query(10, ge=1, le=100)):
    """
    
    
    Parameters:
    - limit: Maximum number of assessments to return (default: 10)
    
    Returns:
    - List of assessments in the current catalog
    """
    try:
        assessments = recommender.assessments[:limit]
        return {
            "total": len(recommender.assessments),
            "showing": len(assessments),
            "assessments": assessments
        }
    except Exception as e:
        logger.error(f"Error retrieving catalog: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving catalog: {str(e)}")

if __name__ == "__main__":
    # will run the API server when script is executed directly
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
