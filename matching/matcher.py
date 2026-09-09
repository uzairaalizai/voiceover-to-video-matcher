"""Matching logic for narration and visual content."""
import numpy as np
from typing import List, Dict, Tuple
from matching.embedder import Embedder
from utils.logger import get_logger
from utils.config import Config

logger = get_logger()

class NarrationMatcher:
    """Match narration segments to visual content."""
    
    def __init__(self, embedder: Embedder = None):
        """
        Initialize matcher.
        
        Args:
            embedder: Embedder instance (creates new if None)
        """
        self.embedder = embedder or Embedder()
    
    def match_segment_to_media(self, narration_text: str, media_descriptions: List[Dict]) -> List[Dict]:
        """
        Match a narration segment to multiple media items.
        
        Args:
            narration_text: Narration segment text
            media_descriptions: List of dicts with 'path' and 'description' keys
        
        Returns:
            Sorted list of matches with scores
        """
        try:
            logger.info(f"Matching narration segment: '{narration_text[:50]}...'")
            
            # Embed narration
            narration_embedding = self.embedder.embed_text(narration_text)
            
            # Embed all descriptions
            descriptions = [m['description'] for m in media_descriptions]
            description_embeddings = self.embedder.embed_texts(descriptions)
            
            # Calculate similarities
            similarities = self.embedder.batch_similarity(narration_embedding, description_embeddings)
            
            # Create matches
            matches = []
            for i, (media, similarity) in enumerate(zip(media_descriptions, similarities)):
                if similarity >= Config.MIN_MATCH_SCORE:
                    matches.append({
                        'media_path': media['path'],
                        'description': media['description'],
                        'score': float(similarity),
                        'media_index': i
                    })
            
            # Sort by score descending
            matches.sort(key=lambda x: x['score'], reverse=True)
            
            # Limit results
            matches = matches[:Config.MAX_MATCHES_PER_SEGMENT]
            
            logger.info(f"Found {len(matches)} matches")
            return matches
        
        except Exception as e:
            logger.error(f"Error matching segment: {e}")
            raise
    
    def match_segments_to_media(self, narration_segments: List[Dict], media_items: List[Dict]) -> List[Dict]:
        """
        Match multiple narration segments to media items.
        
        Args:
            narration_segments: List of segments with 'text', 'start_time', 'end_time'
            media_items: List of media with 'path', 'description', optional 'time'
        
        Returns:
            List of matches with timing information
        """
        try:
            logger.info(f"Matching {len(narration_segments)} segments to {len(media_items)} media items")
            
            all_matches = []
            
            for segment in narration_segments:
                segment_matches = self.match_segment_to_media(
                    segment['text'],
                    media_items
                )
                
                # Attach segment timing
                for match in segment_matches:
                    match['narration_segment'] = segment['text']
                    match['narration_time'] = {
                        'start': segment['start_time'],
                        'end': segment['end_time']
                    }
                
                all_matches.extend(segment_matches)
            
            logger.info(f"Total matches found: {len(all_matches)}")
            return all_matches
        
        except Exception as e:
            logger.error(f"Error matching segments: {e}")
            raise
    
    def score_match(self, narration: str, media_description: str, additional_features: Dict = None) -> float:
        """
        Calculate detailed match score.
        
        Args:
            narration: Narration text
            media_description: Media description
            additional_features: Optional additional scoring factors
        
        Returns:
            Match score (0-1)
        """
        try:
            # Semantic similarity
            narration_emb = self.embedder.embed_text(narration)
            description_emb = self.embedder.embed_text(media_description)
            semantic_score = self.embedder.similarity(narration_emb, description_emb)
            
            # Keyword matching bonus
            keyword_score = self._keyword_match_score(narration, media_description)
            
            # Combined score
            score = 0.7 * semantic_score + 0.3 * keyword_score
            
            return min(1.0, score)
        
        except Exception as e:
            logger.error(f"Error scoring match: {e}")
            return 0.0
    
    def _keyword_match_score(self, text1: str, text2: str) -> float:
        """
        Calculate keyword matching score.
        
        Args:
            text1: First text
            text2: Second text
        
        Returns:
            Keyword match score (0-1)
        """
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union if union > 0 else 0.0
