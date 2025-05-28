from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
import json
import logging
import uvicorn

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

# Initializes FastAPI app
app = FastAPI(
    title="SHL Assessment Recommendation Engine",
    description="A local vector-search based recommendation system for SHL assessments",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_catalog_path():
    """Get the correct path to the catalog file"""
    # Get the directory where this main.py file is located
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Try different possible paths
    possible_paths = [
        # If running from app/ directory
        os.path.join(current_dir, "data", "shl_catalogue.json"),
        # If running from project root
        os.path.join(current_dir, "app", "data", "shl_catalogue.json"),
        # Alternative structure
        os.path.join(os.path.dirname(current_dir), "data", "shl_catalogue.json"),
        # Direct path for Render deployment
        "app/data/shl_catalogue.json",
        "data/shl_catalogue.json",
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            logger.info(f"Found catalog at: {path}")
            return path
    
    # If none found, log all attempted paths
    logger.error("Catalog file not found. Attempted paths:")
    for path in possible_paths:
        logger.error(f"  - {os.path.abspath(path)} (exists: {os.path.exists(path)})")
    
    return possible_paths[0]  # Return first path as fallback

# Load catalog data
def load_catalog():
    """Load the SHL catalog data"""
    catalog_path = get_catalog_path()
    
    try:
        with open(catalog_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.info(f"Successfully loaded {len(data)} assessments from catalog")
        return data
    except FileNotFoundError:
        logger.error(f"Catalog file not found at {catalog_path}")
        return []
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in catalog file: {e}")
        return []
    except Exception as e:
        logger.error(f"Error loading catalog: {e}")
        return []

# Global catalog data
catalog_data = load_catalog()

@app.get("/health")
async def health_check():
    """Endpoint for service health monitoring"""
    try:
        return {
            "status": "healthy",
            "catalog_entries": len(catalog_data),
            "version": "1.0.0",
            "catalog_path": get_catalog_path()
        }
    except Exception as e:
        logger.error(f"Health Check Failed: {str(e)}")
        raise HTTPException(status_code=503, detail=f"Service Unhealthy: {str(e)}")

@app.get("/catalog")
async def get_catalog(limit: int = Query(10, ge=1, le=100)):
    """
    Returns paginated catalog data
    """
    try:
        if not catalog_data:
            raise HTTPException(status_code=404, detail="No catalog data found")
        
        assessments = catalog_data[:limit]
        return {
            "total": len(catalog_data),
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
    """
    try:
        if not catalog_data:
            raise HTTPException(status_code=404, detail="No catalog data available for recommendations")
        
        # Simple text matching for now - you can enhance this with your NLP model
        query_lower = request.query.lower()
        recommendations = []
        
        for assessment in catalog_data:
            # Simple scoring based on text match
            score = 0
            assessment_text = str(assessment).lower()
            
            for word in query_lower.split():
                if word in assessment_text:
                    score += 1
            
            if score > 0:
                assessment_copy = assessment.copy()
                assessment_copy['similarity_score'] = score / len(query_lower.split())
                recommendations.append(assessment_copy)
        
        # Sort by score and return top_k
        recommendations.sort(key=lambda x: x['similarity_score'], reverse=True)
        recommendations = recommendations[:request.top_k]
        
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
    """
    if not file.filename.endswith('.json'):
        raise HTTPException(status_code=400, detail="Only JSON files are accepted")
    
    try:
        # Read and parse the uploaded file
        contents = await file.read()
        new_catalog_data = json.loads(contents)
        
        # Validate catalog structure
        if not isinstance(new_catalog_data, list):
            raise HTTPException(status_code=400, detail="Catalog must be a JSON array of assessments")
        
        # Update global catalog data
        global catalog_data
        catalog_data = new_catalog_data
        
        return {
            "status": "success",
            "message": f"Successfully indexed {len(new_catalog_data)} assessments"
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