from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
import json
import logging
import uvicorn

from app.recommender import SHLRecommender, get_default_catalog_path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# API models
class RecommendationRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5

class RecommendationResponse(BaseModel):
    recommendations: List[Dict[str, Any]]
    query: str

# Initialize FastAPI app
app = FastAPI(
    title="SHL Assessment Recommendation Engine",
    description="A local vector-search based recommendation system for SHL assessments",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create a global instance of the recommender
try:
    catalog_path = get_default_catalog_path()
    logger.info(f"Loading catalog from: {catalog_path}")
    
    if not os.path.exists(catalog_path):
        logger.error(f"Catalog file not found at: {catalog_path}")
        # Try alternative path
        alt_catalog_path = os.path.join(os.path.dirname(__file__), "data", "shl_catalogue.json")
        if os.path.exists(alt_catalog_path):
            catalog_path = alt_catalog_path
            logger.info(f"Using alternative catalog path: {catalog_path}")
        else:
            raise FileNotFoundError(f"Catalog file not found at either {catalog_path} or {alt_catalog_path}")
    
    recommender = SHLRecommender(catalog_path=catalog_path)
    logger.info(f"Recommender initialized successfully with {len(recommender.assessments)} assessments")
    
except Exception as e:
    logger.error(f"Failed to initialize recommender: {e}")
    recommender = None

@app.get("/health")
async def health_check():
    """Endpoint for service health monitoring"""
    try:
        # Verify catalog file exists
        catalog_path = get_default_catalog_path()
        if not os.path.exists(catalog_path):
            # Try alternative path
            alt_catalog_path = os.path.join(os.path.dirname(__file__), "data", "shl_catalogue.json")
            if not os.path.exists(alt_catalog_path):
                raise Exception("Catalog file missing")
        
        # Verify recommender is initialized
        if recommender is None or not hasattr(recommender, 'assessments'):
            raise Exception("Recommender not initialized")
        
        return {
            "status": "healthy",
            "catalog_entries": len(recommender.assessments),
            "version": "1.0.0"
        }
    except Exception as e:
        logger.error(f"Health Check Failed: {str(e)}")
        raise HTTPException(status_code=503, detail=f"Service Unhealthy: {str(e)}")

@app.get("/catalog")
async def get_catalog(limit: int = Query(10, ge=1, le=100)):
    """
    Returns paginated catalog data
    
    Parameters:
    - limit: Maximum number of assessments to return (default: 10)
    
    Returns:
    - List of assessments in the current catalog
    """
    try:
        if recommender is None:
            raise HTTPException(status_code=503, detail="Recommender service not initialized")
        
        assessments = recommender.assessments[:limit]
        return {
            "total": len(recommender.assessments),
            "showing": len(assessments),
            "assessments": assessments
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving catalog: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving catalog: {str(e)}")

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
        if recommender is None:
            raise HTTPException(status_code=503, detail="Recommender service not initialized")
        
        recommendations = recommender.recommend(query=request.query, top_k=request.top_k)
        return {
            "recommendations": recommendations,
            "query": request.query
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating recommendations: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating recommendations: {str(e)}")

@app.post("/upload")
async def upload_catalog(file: UploadFile = File(...)):
    """
    Upload and index a new SHL assessment catalog
    
    Parameters:
    - file: JSON file containing assessment catalog data
    
    Returns:
    - Success message with number of indexed assessments
    """
    if not file.filename.endswith('.json'):
        raise HTTPException(status_code=400, detail="Only JSON files are accepted")
    
    try:
        if recommender is None:
            raise HTTPException(status_code=503, detail="Recommender service not initialized")
        
        # Read and parse the uploaded file
        contents = await file.read()
        catalog_data = json.loads(contents)
        
        # Validate catalog structure
        if not isinstance(catalog_data, list):
            raise HTTPException(status_code=400, detail="Catalog must be a JSON array of assessments")
        
        # Update recommender with new catalog data
        recommender.update_catalog(catalog_data)
        
        return {
            "status": "success",
            "message": f"Successfully indexed {len(catalog_data)} assessments"
        }
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing catalog upload: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing catalog: {str(e)}")

if __name__ == "__main__":
    # Run the API server when script is executed directly
    # Render uses PORT environment variable, defaults to 10000
    port = int(os.getenv("PORT", 10000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=False)