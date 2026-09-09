"""Unit tests for voiceover matcher."""
import pytest
import os
import json
import tempfile
from pathlib import Path

from matcher import VoiceoverMatcher
from audio.extractor import AudioExtractor
from audio.transcriber import AudioTranscriber
from audio.segmenter import AudioSegmenter
from vision.frame_extractor import FrameExtractor
from vision.analyzer import VisualAnalyzer
from matching.embedder import Embedder
from matching.matcher import NarrationMatcher
from matching.scorer import MatchScorer
from utils.config import Config

class TestEmbedder:
    """Test embedding functionality."""
    
    def test_embedder_initialization(self):
        """Test embedder initialization."""
        embedder = Embedder()
        assert embedder.model is not None
    
    def test_embed_text(self):
        """Test text embedding."""
        embedder = Embedder()
        embedding = embedder.embed_text("This is a test sentence")
        assert embedding is not None
        assert len(embedding) > 0
    
    def test_embed_multiple_texts(self):
        """Test multiple text embedding."""
        embedder = Embedder()
        texts = ["First text", "Second text", "Third text"]
        embeddings = embedder.embed_texts(texts)
        assert embeddings.shape[0] == len(texts)
    
    def test_similarity(self):
        """Test similarity calculation."""
        embedder = Embedder()
        text1 = "The cat sat on the mat"
        text2 = "The cat is sitting on the mat"
        
        emb1 = embedder.embed_text(text1)
        emb2 = embedder.embed_text(text2)
        
        similarity = embedder.similarity(emb1, emb2)
        assert 0 <= similarity <= 1
        assert similarity > 0.5  # Should be quite similar

class TestAudioSegmenter:
    """Test audio segmentation."""
    
    def test_segmenter_initialization(self):
        """Test segmenter initialization."""
        segmenter = AudioSegmenter(min_length=2.0)
        assert segmenter.min_length == 2.0
    
    def test_segment_by_sentences(self):
        """Test sentence segmentation."""
        segmenter = AudioSegmenter()
        
        text = "This is the first sentence. This is the second sentence. And here is the third."
        word_timestamps = [
            {'word': word, 'start': i * 0.5, 'end': (i + 1) * 0.5}
            for i, word in enumerate(text.split())
        ]
        
        segments = segmenter.segment_by_sentences(text, word_timestamps)
        assert len(segments) > 0
        assert all('text' in s and 'start_time' in s and 'end_time' in s for s in segments)

class TestMatchScorer:
    """Test match scoring."""
    
    def test_rank_matches(self):
        """Test match ranking."""
        matches = [
            {'score': 0.9, 'media_path': 'video1.mp4'},
            {'score': 0.7, 'media_path': 'video2.mp4'},
            {'score': 0.8, 'media_path': 'video3.mp4'},
        ]
        
        ranked = MatchScorer.rank_matches(matches)
        assert ranked[0]['score'] >= ranked[1]['score']
    
    def test_filter_by_confidence(self):
        """Test confidence filtering."""
        matches = [
            {'score': 0.9},
            {'score': 0.5},
            {'score': 0.3},
        ]
        
        filtered = MatchScorer.filter_by_confidence(matches, threshold=0.6)
        assert len(filtered) == 1
        assert filtered[0]['score'] == 0.9
    
    def test_get_top_matches(self):
        """Test getting top matches."""
        matches = [
            {'score': 0.9},
            {'score': 0.8},
            {'score': 0.7},
            {'score': 0.6},
            {'score': 0.5},
        ]
        
        top = MatchScorer.get_top_matches(matches, top_n=3)
        assert len(top) == 3
        assert top[0]['score'] == 0.9

class TestNarrationMatcher:
    """Test narration matching."""
    
    def test_matcher_initialization(self):
        """Test matcher initialization."""
        matcher = NarrationMatcher()
        assert matcher.embedder is not None
    
    def test_match_segment_to_media(self):
        """Test matching a segment to media."""
        matcher = NarrationMatcher()
        
        narration = "A dog is running in the park"
        media_descriptions = [
            {'path': 'video1.mp4', 'description': 'A dog running in a grass field'},
            {'path': 'video2.mp4', 'description': 'People eating at a restaurant'},
            {'path': 'image1.jpg', 'description': 'A sunset over the ocean'},
        ]
        
        matches = matcher.match_segment_to_media(narration, media_descriptions)
        assert len(matches) > 0
        assert matches[0]['score'] > Config.MIN_MATCH_SCORE

class TestConfig:
    """Test configuration."""
    
    def test_config_validation(self):
        """Test configuration validation."""
        # This will raise if API key is not set
        try:
            Config.validate()
        except ValueError:
            pytest.skip("API key not configured")
    
    def test_config_values(self):
        """Test configuration values."""
        assert Config.CONFIDENCE_THRESHOLD > 0
        assert Config.CONFIDENCE_THRESHOLD <= 1
        assert Config.FRAME_SAMPLE_RATE >= 1
        assert Config.AUDIO_SEGMENT_MIN_LENGTH > 0

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
