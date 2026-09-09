"""Configuration management for voiceover matcher."""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Application configuration."""
    
    # API Configuration
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
    MODEL = os.getenv('MODEL', 'gpt-4-vision')
    
    # Matching Configuration
    CONFIDENCE_THRESHOLD = float(os.getenv('CONFIDENCE_THRESHOLD', 0.7))
    MIN_MATCH_SCORE = float(os.getenv('MIN_MATCH_SCORE', 0.5))
    MAX_MATCHES_PER_SEGMENT = int(os.getenv('MAX_MATCHES_PER_SEGMENT', 3))
    
    # Processing Configuration
    FRAME_SAMPLE_RATE = int(os.getenv('FRAME_SAMPLE_RATE', 1))
    AUDIO_SEGMENT_MIN_LENGTH = float(os.getenv('AUDIO_SEGMENT_MIN_LENGTH', 2))
    VIDEO_CHUNK_DURATION = int(os.getenv('VIDEO_CHUNK_DURATION', 10))
    
    # Output Configuration
    DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'
    VERBOSE = os.getenv('VERBOSE', 'true').lower() == 'true'
    SAVE_INTERMEDIATE_RESULTS = os.getenv('SAVE_INTERMEDIATE_RESULTS', 'true').lower() == 'true'
    
    # Paths
    CACHE_DIR = 'cache'
    OUTPUT_DIR = 'output'
    LOGS_DIR = 'logs'
    
    # Supported formats
    VIDEO_FORMATS = {'.mp4', '.mov', '.webm', '.avi', '.mkv', '.flv'}
    IMAGE_FORMATS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
    AUDIO_FORMATS = {'.mp3', '.wav', '.aac', '.flac', '.m4a'}
    
    @classmethod
    def validate(cls):
        """Validate configuration."""
        if not cls.OPENAI_API_KEY:
            raise ValueError('OPENAI_API_KEY not set in environment')
        return True
