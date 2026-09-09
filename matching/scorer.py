"""Scoring and ranking for matches."""
import numpy as np
from typing import List, Dict
from utils.logger import get_logger
from utils.config import Config

logger = get_logger()

class MatchScorer:
    """Score and rank matches."""
    
    @staticmethod
    def rank_matches(matches: List[Dict], scoring_weights: Dict = None) -> List[Dict]:
        """
        Rank matches by multiple criteria.
        
        Args:
            matches: List of matches with scores
            scoring_weights: Dict of weights for different factors
        
        Returns:
            Sorted matches by combined score
        """
        if not matches:
            return []
        
        if scoring_weights is None:
            scoring_weights = {
                'semantic': 0.6,
                'temporal': 0.2,
                'confidence': 0.2
            }
        
        try:
            for match in matches:
                combined_score = 0.0
                
                # Semantic similarity
                if 'score' in match:
                    combined_score += match['score'] * scoring_weights.get('semantic', 0.6)
                
                # Temporal proximity (if applicable)
                if 'media_time' in match and 'narration_time' in match:
                    temporal_score = MatchScorer._temporal_score(
                        match['narration_time'],
                        match['media_time']
                    )
                    combined_score += temporal_score * scoring_weights.get('temporal', 0.2)
                
                # Confidence
                if 'confidence' in match:
                    combined_score += match['confidence'] * scoring_weights.get('confidence', 0.2)
                
                match['combined_score'] = combined_score
            
            # Sort by combined score
            matches.sort(key=lambda x: x.get('combined_score', 0), reverse=True)
            
            return matches
        
        except Exception as e:
            logger.error(f"Error ranking matches: {e}")
            return matches
    
    @staticmethod
    def _temporal_score(narration_time: Dict, media_time: Dict) -> float:
        """
        Calculate temporal proximity score.
        
        Args:
            narration_time: Dict with 'start' and 'end'
            media_time: Dict with 'start' and 'end'
        
        Returns:
            Temporal score (0-1)
        """
        # Calculate overlap
        narration_start = narration_time.get('start', 0)
        narration_end = narration_time.get('end', 0)
        media_start = media_time.get('start', 0)
        media_end = media_time.get('end', 0)
        
        overlap_start = max(narration_start, media_start)
        overlap_end = min(narration_end, media_end)
        
        if overlap_end <= overlap_start:
            return 0.0  # No overlap
        
        overlap = overlap_end - overlap_start
        narration_duration = narration_end - narration_start
        media_duration = media_end - media_start
        
        max_duration = max(narration_duration, media_duration)
        
        if max_duration == 0:
            return 0.0
        
        return min(1.0, overlap / max_duration)
    
    @staticmethod
    def filter_by_confidence(matches: List[Dict], threshold: float = None) -> List[Dict]:
        """
        Filter matches by confidence threshold.
        
        Args:
            matches: List of matches
            threshold: Confidence threshold (default: Config.CONFIDENCE_THRESHOLD)
        
        Returns:
            Filtered matches
        """
        threshold = threshold or Config.CONFIDENCE_THRESHOLD
        filtered = [m for m in matches if m.get('score', 0) >= threshold]
        logger.info(f"Filtered {len(matches)} matches to {len(filtered)} above threshold {threshold}")
        return filtered
    
    @staticmethod
    def get_top_matches(matches: List[Dict], top_n: int = 5) -> List[Dict]:
        """
        Get top N matches.
        
        Args:
            matches: List of matches
            top_n: Number of top matches to return
        
        Returns:
            Top N matches
        """
        sorted_matches = sorted(matches, key=lambda x: x.get('score', 0), reverse=True)
        return sorted_matches[:top_n]
