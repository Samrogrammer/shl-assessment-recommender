"""
SHL Assessment Recommendation Engine - Evaluation Script

This script tests the recommendation engine with sample queries and
evaluates the quality of recommendations.
"""

import os
import json
from app.recommender import SHLRecommender, get_default_catalog_path

import logging
from typing import List, Dict, Any
import numpy as np
from sentence_transformers import util

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
    "Executive Leadership position requiring strategic decision making"
]

def load_catalog(catalog_path: str) -> List[Dict[str, Any]]:
    """Load the assessment catalog"""
    with open(catalog_path, 'r') as f:
        return json.load(f)

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
    
    for i, query in enumerate(queries):
        logger.info(f"\n\nQUERY {i+1}: {query}")
        logger.info("-" * 50)
        
        # Get recommendations
        recommendations = recommender.recommend(query, top_k=top_k)
        
        # Display results
        for j, rec in enumerate(recommendations):
            score = rec['similarity_score']
            all_scores.append(score)
            logger.info(f"{j+1}. {rec['name']} (Score: {score:.4f})")
            logger.info(f"   Category: {rec['category']}")
            logger.info(f"   Tags: {', '.join(rec['tags'])}")
            logger.info(f"   Recommended for: {', '.join(rec['recommended_roles'])}")
    
    # Print overall statistics
    if all_scores:
        logger.info("\n\nOVERALL STATISTICS")
        logger.info("-" * 50)
        logger.info(f"Average similarity score: {np.mean(all_scores):.4f}")
        logger.info(f"Min similarity score: {np.min(all_scores):.4f}")
        logger.info(f"Max similarity score: {np.max(all_scores):.4f}")
        logger.info(f"Median similarity score: {np.median(all_scores):.4f}")

def main():
    """Run the evaluation"""
    # Determine catalog path
    base_dir = os.path.dirname(os.path.abspath(__file__))
    catalog_path = os.path.join(base_dir, "app", "data", "catalog.json")
    
    if not os.path.exists(catalog_path):
        logger.error(f"Catalog file not found at: {catalog_path}")
        return
    
    logger.info(f"Loading catalog from: {catalog_path}")
    
    # Initialize recommender
    recommender = SHLRecommender(catalog_path=catalog_path)
    
    # Run evaluation
    evaluate_recommendations(recommender, TEST_QUERIES)
    
    logger.info("\nEvaluation complete! Results saved to evaluation_results.log")

if __name__ == "__main__":
    main()