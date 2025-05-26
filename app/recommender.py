import json
import os
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any, Tuple, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SHLRecommender:
    """
    SHL Assessment Recommender Engine
    
    This class loads SHL assessment catalog data, converts assessments to vector embeddings,
    and provides methods to find the most similar assessments based on user queries.
    """
    
    def __init__(self, catalog_path: str = None, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the SHL Recommender Engine
        
        Args:
            catalog_path: Path to the catalog JSON file
            model_name: Name of the sentence-transformer model to use
        """
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()
        
        # Initialize FAISS index
        self.index = faiss.IndexFlatIP(self.dimension)  # Inner product for cosine similarity with normalized vectors
        
        # Storage for assessment data and IDs
        self.assessments = []
        self.assessment_ids = []
        
        # Load catalog if provided
        if catalog_path and os.path.exists(catalog_path):
            self.load_catalog(catalog_path)
    
    def load_catalog(self, catalog_path: str) -> None:
        """
        Load assessment catalog from JSON file
        
        Args:
            catalog_path: Path to the catalog JSON file
        """
        try:
            with open(catalog_path, 'r') as f:
                catalog_data = json.load(f)
            
            logger.info(f"Loaded catalog with {len(catalog_data)} assessments")
            self.index_catalog(catalog_data)
        except Exception as e:
            logger.error(f"Error loading catalog: {e}")
            raise
    
    def index_catalog(self, catalog_data: List[Dict[str, Any]]) -> None:
        """
        Index the catalog data by creating and storing embeddings
        
        Args:
            catalog_data: List of assessment dictionaries
        """
        # Clear existing data
        self.assessments = catalog_data
        self.assessment_ids = [assessment['id'] for assessment in catalog_data]
        
        # Create embeddings for each assessment
        texts_to_embed = []
        for assessment in catalog_data:
            # Create a rich text representation for embedding
            text = f"{assessment['name']}. {assessment['description']} Categories: {assessment['category']}. Tags: {', '.join(assessment['tags'])}. Recommended for: {', '.join(assessment['recommended_roles'])}."
            texts_to_embed.append(text)
        
        # Generate embeddings
        embeddings = self.model.encode(texts_to_embed, normalize_embeddings=True)
        
        # Reset the index and add embeddings
        self.index = faiss.IndexFlatIP(self.dimension)
        self.index.add(np.array(embeddings).astype('float32'))
        
        logger.info(f"Indexed {len(catalog_data)} assessments")
    
    def recommend(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Recommend assessments based on user query
        
        Args:
            query: User input (job role, skills, or description)
            top_k: Number of recommendations to return
            
        Returns:
            List of recommended assessments with similarity scores
        """
        # Ensure index is not empty
        if self.index.ntotal == 0:
            logger.warning("No assessments indexed")
            return []
        
        # Encode the query
        query_embedding = self.model.encode([query], normalize_embeddings=True)
        
        # Search the index
        top_k = min(top_k, self.index.ntotal)
        scores, indices = self.index.search(query_embedding.astype('float32'), top_k)
        
        # Prepare results
        results = []
        for i, idx in enumerate(indices[0]):
            assessment = self.assessments[idx]
            score = float(scores[0][i])  # Convert numpy float to native Python float
            
            # Add assessment info with score
            result = assessment.copy()
            result['similarity_score'] = score
            results.append(result)
        
        return results
    
    def update_catalog(self, new_catalog_data: List[Dict[str, Any]]) -> None:
        """
        Update the catalog with new data
        
        Args:
            new_catalog_data: New catalog data to index
        """
        self.index_catalog(new_catalog_data)
        logger.info("Catalog updated successfully")


# Example function to find the default catalog path
from pathlib import Path

def get_default_catalog_path():
    """
    Get the default catalog path, trying multiple possible locations
    """
    import os
    from pathlib import Path
    
    # Get the current file's directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Try multiple possible paths
    possible_paths = [
        # Standard path from app/recommender.py
        os.path.join(current_dir, "data", "shl_catalogue.json"),
        # Path from project root
        os.path.join(os.path.dirname(current_dir), "app", "data", "shl_catalogue.json"),
        # Alternative path structure
        os.path.join(current_dir, "..", "data", "shl_catalogue.json"),
        # Direct path if running from project root
        os.path.join("app", "data", "shl_catalogue.json"),
    ]
    
    for path in possible_paths:
        full_path = os.path.abspath(path)
        if os.path.exists(full_path):
            return full_path
    
    # If none found, return the first (standard) path
    return os.path.abspath(possible_paths[0])