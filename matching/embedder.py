"""Semantic embeddings for text and visual content."""
import numpy as np
from typing import List, Union
from sentence_transformers import SentenceTransformer
from utils.logger import get_logger

logger = get_logger()

class Embedder:
    """Create semantic embeddings for matching."""
    
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """
        Initialize embedder with sentence transformer.
        
        Args:
            model_name: Sentence transformer model name
        """
        try:
            logger.info(f"Loading embedding model: {model_name}")
            self.model = SentenceTransformer(model_name)
            logger.info("Embedder loaded successfully")
        except Exception as e:
            logger.error(f"Error loading embedder: {e}")
            raise
    
    def embed_text(self, text: str) -> np.ndarray:
        """
        Create embedding for text.
        
        Args:
            text: Text to embed
        
        Returns:
            Embedding vector
        """
        try:
            embedding = self.model.encode(text, convert_to_tensor=False)
            return embedding
        except Exception as e:
            logger.error(f"Error embedding text: {e}")
            raise
    
    def embed_texts(self, texts: List[str]) -> np.ndarray:
        """
        Create embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed
        
        Returns:
            Matrix of embeddings
        """
        try:
            embeddings = self.model.encode(texts, convert_to_tensor=False)
            return embeddings
        except Exception as e:
            logger.error(f"Error embedding texts: {e}")
            raise
    
    def similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
        
        Returns:
            Similarity score (0-1)
        """
        try:
            # Cosine similarity
            dot_product = np.dot(embedding1, embedding2)
            norm1 = np.linalg.norm(embedding1)
            norm2 = np.linalg.norm(embedding2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            return float((similarity + 1) / 2)  # Normalize to 0-1
        except Exception as e:
            logger.error(f"Error calculating similarity: {e}")
            return 0.0
    
    def batch_similarity(self, embedding: np.ndarray, embeddings: np.ndarray) -> np.ndarray:
        """
        Calculate similarity between one embedding and multiple embeddings.
        
        Args:
            embedding: Single embedding vector
            embeddings: Matrix of embeddings
        
        Returns:
            Array of similarity scores
        """
        try:
            # Normalize vectors
            embedding_norm = embedding / np.linalg.norm(embedding)
            embeddings_norm = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
            
            # Calculate cosine similarities
            similarities = np.dot(embeddings_norm, embedding_norm)
            return (similarities + 1) / 2  # Normalize to 0-1
        except Exception as e:
            logger.error(f"Error calculating batch similarity: {e}")
            return np.array([])
