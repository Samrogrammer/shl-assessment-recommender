"""
SHL Assessment Recommendation Engine - Evaluation Script

This script tests the recommendation engine with sample queries and
evaluates the quality of recommendations.
"""

import os
import json
import sys
from pathlib import Path
import logging
from typing import List, Dict, Any
import numpy as np

# Add the app directory to Python path
current_dir = Path(__file__).parent.absolute()
app_dir = current_dir / "app"
sys.path.insert(0, str(app_dir))

try:
    from app.recommender import SHLRecommender
except ImportError:
    print("Error: Cannot import recommender module. Make sure you're running from the project root.")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("evaluation_results.log")
    ]
)
logger = logging.getLogger(__name__)

# Sample test queries covering different job roles and skills
TEST_QUERIES = [
    "Data Scientist with Python and machine learning experience",
    "Sales Manager with customer relationship skills",
    "Software Engineer proficient in Java and cloud technologies", 
    "Financial Analyst with Excel and accounting knowledge",
    "Project Manager with Agile methodology experience",
    "Customer Service Representative with conflict resolution skills",
    "Human Resources Specialist with recruitment experience",
    "Marketing Manager with digital marketing and social media expertise",
    "Mechanical Engineer with CAD design skills",
    "Executive Leadership position requiring strategic decision making",
    "Call center representative with phone support experience",
    "Remote worker needing self-management skills",
    "Coding assessment for software developer",
    "Safety officer for manufacturing environment",
    "Microsoft Office skills for administrative role"
]

def find_catalog_path() -> str:
    """Find the catalog file in various possible locations"""
    base_dir = Path(__file__).parent.absolute()
    
    # Possible catalog file names and locations
    catalog_names = ["shl_catalogue.json", "catalog.json"]
    possible_dirs = [
        base_dir / "app" / "data",
        base_dir / "data", 
        base_dir,
        base_dir / "app"
    ]
    
    for directory in possible_dirs:
        for name in catalog_names:
            catalog_path = directory / name
            if catalog_path.exists():
                logger.info(f"Found catalog at: {catalog_path}")
                return str(catalog_path)
    
    # Log all attempted paths
    logger.error("Catalog file not found. Attempted paths:")
    for directory in possible_dirs:
        for name in catalog_names:
            path = directory / name
            logger.error(f"  - {path} (exists: {path.exists()})")
    
    return str(base_dir / "app" / "data" / "shl_catalogue.json")

def load_catalog(catalog_path: str) -> List[Dict[str, Any]]:
    """Load the assessment catalog"""
    try:
        with open(catalog_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.info(f"Successfully loaded {len(data)} assessments from catalog")
        return data
    except FileNotFoundError:
        logger.error(f"Catalog file not found at: {catalog_path}")
        return []
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in catalog file: {e}")
        return []
    except Exception as e:
        logger.error(f"Error loading catalog: {e}")
        return []

def evaluate_recommendations(recommender: SHLRecommender, queries: List[str], top_k: int = 5) -> None:
    """
    Evaluate the recommendation engine on sample queries
    
    Args:
        recommender: Initialized SHLRecommender instance
        queries: List of test queries
        top_k: Number of recommendations to return
    """
    logger.info("=" * 50)
    logger.info(f"EVALUATION RESULTS (top-{top_k} recommendations)")
    logger.info("=" * 50)
    
    # Track all similarity scores
    all_scores = []
    successful_queries = 0
    
    for i, query in enumerate(queries):
        logger.info(f"\n\nQUERY {i+1}: {query}")
        logger.info("-" * 50)
        
        try:
            # Get recommendations
            recommendations = recommender.recommend(query, top_k=top_k)
            
            if not recommendations:
                logger.warning("No recommendations returned for this query")
                continue
                
            successful_queries += 1
            
            # Display results
            for j, rec in enumerate(recommendations):
                score = rec.get('similarity_score', 0)
                all_scores.append(score)
                logger.info(f"{j+1}. {rec['name']} (Score: {score:.4f})")
                logger.info(f"   Category: {rec['category']}")
                logger.info(f"   Tags: {', '.join(rec['tags'])}")
                logger.info(f"   Recommended for: {', '.join(rec['recommended_roles'])}")
                
        except Exception as e:
            logger.error(f"Error processing query '{query}': {e}")
    
    # Print overall statistics
    logger.info("\n\nOVERALL STATISTICS")
    logger.info("-" * 50)
    logger.info(f"Total queries processed: {len(queries)}")
    logger.info(f"Successful queries: {successful_queries}")
    logger.info(f"Success rate: {(successful_queries/len(queries)*100):.1f}%")
    
    if all_scores:
        logger.info(f"Total recommendations: {len(all_scores)}")
        logger.info(f"Average similarity score: {np.mean(all_scores):.4f}")
        logger.info(f"Min similarity score: {np.min(all_scores):.4f}")
        logger.info(f"Max similarity score: {np.max(all_scores):.4f}")
        logger.info(f"Median similarity score: {np.median(all_scores):.4f}")
        logger.info(f"Standard deviation: {np.std(all_scores):.4f}")
    else:
        logger.warning("No similarity scores collected")

def test_simple_api():
    """Test the basic functionality without the full recommender"""
    catalog_path = find_catalog_path()
    catalog_data = load_catalog(catalog_path)
    
    if not catalog_data:
        logger.error("Cannot proceed without catalog data")
        return False
    
    logger.info(f"Testing with {len(catalog_data)} assessments")
    
    # Simple text matching test
    query = "software engineer"
    query_words = query.lower().split()
    matches = []
    
    for assessment in catalog_data:
        score = 0
        assessment_text = (
            assessment.get('name', '') + ' ' +
            assessment.get('description', '') + ' ' +
            ' '.join(assessment.get('tags', [])) + ' ' +
            ' '.join(assessment.get('recommended_roles', []))
        ).lower()
        
        for word in query_words:
            if word in assessment_text:
                score += 1
        
        if score > 0:
            matches.append({
                'name': assessment['name'],
                'score': score,
                'category': assessment['category']
            })
    
    matches.sort(key=lambda x: x['score'], reverse=True)
    
    logger.info(f"Simple matching test for '{query}':")
    for i, match in enumerate(matches[:5]):
        logger.info(f"  {i+1}. {match['name']} (Score: {match['score']}) - {match['category']}")
    
    return len(matches) > 0

def main():
    """Run the evaluation"""
    logger.info("Starting SHL Assessment Recommendation Engine Evaluation")
    
    # Find catalog path
    catalog_path = find_catalog_path()
    
    if not Path(catalog_path).exists():
        logger.error(f"Catalog file not found at: {catalog_path}")
        logger.info("Running simple API test instead...")
        success = test_simple_api()
        if success:
            logger.info("Simple test completed successfully")
        else:
            logger.error("Simple test failed")
        return
    
    logger.info(f"Loading catalog from: {catalog_path}")
    
    try:
        # Initialize recommender
        logger.info("Initializing SHLRecommender...")
        recommender = SHLRecommender(catalog_path=catalog_path)
        
        # Run evaluation
        evaluate_recommendations(recommender, TEST_QUERIES)
        
        logger.info("\nEvaluation complete! Results saved to evaluation_results.log")
        
    except Exception as e:
        logger.error(f"Error during evaluation: {e}")
        logger.info("Falling back to simple API test...")
        test_simple_api()

if __name__ == "__main__":
    main()