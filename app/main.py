from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
import json
import logging
import uvicorn
from pathlib import Path

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
    allow_origins=["https://shl-streamlit-frontend-a9d3.onrender.com"],  # or explicitly your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_catalog_path():
    """Get the correct path to the catalog file with comprehensive path resolution"""
    # Get the directory where this main.py file is located
    current_dir = Path(__file__).parent.absolute()
    
    # Define possible catalog file names and paths
    catalog_names = ["shl_catalogue.json", "catalog.json"]
    
    possible_paths = []
    for name in catalog_names:
        possible_paths.extend([
            # If running from app/ directory
            current_dir / "data" / name,
            # If running from project root
            current_dir.parent / "app" / "data" / name,
            # Alternative structure
            current_dir.parent / "data" / name,
            # Direct paths for different deployment scenarios
            Path("app") / "data" / name,
            Path("data") / name,
            Path(name),  # If in same directory
        ])
    
    # Find existing file
    for path in possible_paths:
        if path.exists():
            logger.info(f"Found catalog at: {path.absolute()}")
            return str(path.absolute())
    
    # If none found, log all attempted paths
    logger.error("Catalog file not found. Attempted paths:")
    for path in possible_paths:
        abs_path = path.absolute()
        logger.error(f"  - {abs_path} (exists: {abs_path.exists()})")
    
    # Return the most likely path as fallback
    return str(possible_paths[0].absolute())

def load_catalog():
    """Load the SHL catalog data with better error handling"""
    catalog_path = get_catalog_path()
    
    try:
        with open(catalog_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Validate data structure
        if not isinstance(data, list):
            logger.error("Catalog data is not a list")
            return []
        
        if not data:
            logger.warning("Catalog data is empty")
            return []
        
        # Validate first item structure
        if data and not all(key in data[0] for key in ['id', 'name', 'description']):
            logger.error("Catalog items missing required fields")
            return []
        
        logger.info(f"Successfully loaded {len(data)} assessments from catalog")
        return data
        
    except FileNotFoundError:
        logger.error(f"Catalog file not found at {catalog_path}")
        # Create a minimal default catalog for testing
        default_catalog = [
            {
                "id": "test-001",
                "name": "Test Assessment",
                "description": "A test assessment for system verification",
                "tags": ["test"],
                "category": "Test",
                "duration_minutes": 10,
                "recommended_roles": ["Test Role"]
            }
        ]
        logger.info("Created minimal default catalog for testing")
        return default_catalog
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in catalog file: {e}")
        return []
    except Exception as e:
        logger.error(f"Error loading catalog: {e}")
        return []

# Load catalog data at startup
try:
    catalog_data = load_catalog()
    logger.info(f"Catalog loaded successfully: {len(catalog_data)} items")
except Exception as e:
    logger.error(f"Failed to load catalog at startup: {e}")
    catalog_data = []

@app.get("/")
async def root():
    """Root endpoint with basic information"""
    return {
        "message": "SHL Assessment Recommendation Engine",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "catalog": "/catalog",
            "recommend": "/recommend",
            "docs": "/docs"
        },
        "catalog_status": f"{len(catalog_data)} assessments loaded"
    }

@app.get("/health")
async def health_check():
    """Enhanced health check endpoint"""
    try:
        catalog_path = get_catalog_path()
        return {
            "status": "healthy",
            "catalog_entries": len(catalog_data),
            "version": "1.0.0",
            "catalog_path": catalog_path,
            "catalog_exists": Path(catalog_path).exists(),
            "environment": {
                "python_path": os.getcwd(),
                "file_location": str(Path(__file__).parent.absolute())
            }
        }
    except Exception as e:
        logger.error(f"Health Check Failed: {str(e)}")
        raise HTTPException(status_code=503, detail=f"Service Unhealthy: {str(e)}")

@app.get("/catalog")
async def get_catalog(limit: int = Query(25, ge=1, le=100)):
    """Returns paginated catalog data with better error handling"""
    global catalog_data  # ✅ declare global early

    try:
        if not catalog_data:
            catalog_data = load_catalog()
        
        assessments = catalog_data[:limit] if catalog_data else []
        return {
            "total": len(catalog_data),
            "showing": len(assessments),
            "assessments": assessments,
            "status": "success"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving catalog: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving catalog: {str(e)}")


@app.post("/recommend", response_model=RecommendationResponse)
async def recommend_assessments(request: RecommendationRequest):
    """Enhanced recommendation endpoint with better matching"""
    global catalog_data
    try:
        if not catalog_data:
            # Try to reload catalog
            catalog_data = load_catalog()
            
            if not catalog_data:
                raise HTTPException(
                    status_code=404, 
                    detail="No recommendations found. Try a different query."
                )
        
        query_lower = request.query.lower().strip()
        if not query_lower:
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        recommendations = []
        query_words = set(query_lower.split())
        
        for assessment in catalog_data:
            # Enhanced scoring algorithm
            score = 0
            
            # Create searchable text from assessment
            searchable_fields = [
                assessment.get('name', ''),
                assessment.get('description', ''),
                assessment.get('category', ''),
                ' '.join(assessment.get('tags', [])),
                ' '.join(assessment.get('recommended_roles', []))
            ]
            
            assessment_text = ' '.join(searchable_fields).lower()
            
            # Word matching with different weights
            for word in query_words:
                # Exact word matches
                if word in assessment_text:
                    score += 1
                
                # Partial matches for longer words
                if len(word) > 3:
                    for text_word in assessment_text.split():
                        if word in text_word or text_word in word:
                            score += 0.5
            
            # Bonus for category matches
            if any(word in assessment.get('category', '').lower() for word in query_words):
                score += 2
            
            # Bonus for role matches
            for role in assessment.get('recommended_roles', []):
                if any(word in role.lower() for word in query_words):
                    score += 1.5
            
            if score > 0:
                assessment_copy = assessment.copy()
                assessment_copy['similarity_score'] = round(score / len(query_words), 4)
                recommendations.append(assessment_copy)
        
        # Sort by score and return top_k
        recommendations.sort(key=lambda x: x['similarity_score'], reverse=True)
        recommendations = recommendations[:request.top_k]
        
        if not recommendations:
            logger.warning(f"No recommendations found for query: {request.query}")
        
        return RecommendationResponse(
            recommendations=recommendations,
            query=request.query
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating recommendations for query '{request.query}': {e}")
        raise HTTPException(status_code=500, detail=f"Error generating recommendations: {str(e)}")

@app.post("/upload")
async def upload_catalog(file: UploadFile = File(...)):
    """Enhanced catalog upload with validation"""
    if not file.filename.endswith('.json'):
        raise HTTPException(status_code=400, detail="Only JSON files are accepted")
    
    try:
        # Read and parse the uploaded file
        contents = await file.read()
        new_catalog_data = json.loads(contents)
        
        # Validate catalog structure
        if not isinstance(new_catalog_data, list):
            raise HTTPException(status_code=400, detail="Catalog must be a JSON array of assessments")
        
        if not new_catalog_data:
            raise HTTPException(status_code=400, detail="Catalog cannot be empty")
        
        # Validate required fields in first item
        required_fields = ['id', 'name', 'description', 'tags', 'category', 'recommended_roles']
        if not all(field in new_catalog_data[0] for field in required_fields):
            raise HTTPException(
                status_code=400, 
                detail=f"Catalog items must have these fields: {required_fields}"
            )
        
        # Update global catalog data
        global catalog_data
        catalog_data = new_catalog_data
        
        logger.info(f"Catalog updated with {len(new_catalog_data)} assessments")
        
        return {
            "status": "success",
            "message": f"Successfully indexed {len(new_catalog_data)} assessments",
            "catalog_size": len(new_catalog_data)
        }
        
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON format: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing catalog upload: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing catalog: {str(e)}")

@app.get("/debug")
async def debug_info():
    """Debug endpoint to help troubleshoot issues"""
    current_dir = Path(__file__).parent.absolute()
    
    # Check for catalog files
    catalog_files = []
    for name in ["shl_catalogue.json", "catalog.json"]:
        for path in [
            current_dir / "data" / name,
            current_dir.parent / "app" / "data" / name,
            Path("app") / "data" / name,
        ]:
            if path.exists():
                try:
                    with open(path, 'r') as f:
                        data = json.load(f)
                    catalog_files.append({
                        "path": str(path.absolute()),
                        "exists": True,
                        "size": len(data) if isinstance(data, list) else "Invalid format"
                    })
                except Exception as e:
                    catalog_files.append({
                        "path": str(path.absolute()),
                        "exists": True,
                        "error": str(e)
                    })
    
    return {
        "current_directory": str(current_dir),
        "catalog_data_loaded": len(catalog_data),
        "catalog_files_found": catalog_files,
        "environment_vars": {
            "PORT": os.getenv("PORT", "Not set"),
            "API_URL": os.getenv("API_URL", "Not set")
        }
    }

if __name__ == "__main__":
    import os
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
