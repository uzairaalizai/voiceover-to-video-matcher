"""Audio segmentation utilities."""
import re
from typing import List, Dict
from utils.logger import get_logger

logger = get_logger()

class AudioSegmenter:
    """Segment audio transcription into sentences."""
    
    def __init__(self, min_length: float = 2.0):
        """
        Initialize audio segmenter.
        
        Args:
            min_length: Minimum segment length in seconds
        """
        self.min_length = min_length
    
    def segment_by_sentences(self, transcription: str, word_timestamps: List[Dict]) -> List[Dict]:
        """
        Segment transcription into sentences.
        
        Args:
            transcription: Full transcription text
            word_timestamps: List of words with timestamps
        
        Returns:
            List of segments with text and timestamps
        """
        # Split by sentence-ending punctuation
        sentences = re.split(r'[.!?]+', transcription)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        segments = []
        word_idx = 0
        
        for sentence in sentences:
            words_in_sentence = sentence.split()
            num_words = len(words_in_sentence)
            
            if word_idx + num_words <= len(word_timestamps):
                start_time = word_timestamps[word_idx]['start']
                end_time = word_timestamps[word_idx + num_words - 1]['end']
                
                if end_time - start_time >= self.min_length:
                    segments.append({
                        'text': sentence,
                        'start_time': start_time,
                        'end_time': end_time,
                        'duration': end_time - start_time
                    })
                
                word_idx += num_words
        
        logger.info(f"Segmented audio into {len(segments)} segments")
        return segments
    
    def segment_by_duration(self, transcription: str, duration: float, segment_duration: float = 5.0) -> List[Dict]:
        """
        Segment transcription by fixed duration.
        
        Args:
            transcription: Full transcription text
            duration: Total audio duration in seconds
            segment_duration: Duration of each segment in seconds
        
        Returns:
            List of segments with text and timestamps
        """
        words = transcription.split()
        words_per_segment = max(1, int(len(words) * segment_duration / duration))
        
        segments = []
        for i in range(0, len(words), words_per_segment):
            segment_words = words[i:i + words_per_segment]
            segments.append({
                'text': ' '.join(segment_words),
                'start_time': i * (duration / len(words)),
                'end_time': min((i + words_per_segment) * (duration / len(words)), duration)
            })
        
        logger.info(f"Segmented audio into {len(segments)} segments by duration")
        return segments
