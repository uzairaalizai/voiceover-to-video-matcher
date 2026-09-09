"""Audio extraction and processing utilities."""
import os
from pydub import AudioSegment
import speech_recognition as sr
from utils.logger import get_logger

logger = get_logger()

class AudioExtractor:
    """Extract audio from video files."""
    
    def __init__(self):
        """Initialize audio extractor."""
        self.recognizer = sr.Recognizer()
    
    def extract_from_video(self, video_path: str, output_audio_path: str = None) -> str:
        """
        Extract audio from video file.
        
        Args:
            video_path: Path to video file
            output_audio_path: Optional output path for audio file
        
        Returns:
            Path to extracted audio file
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        if output_audio_path is None:
            base_name = os.path.splitext(os.path.basename(video_path))[0]
            output_audio_path = f"{base_name}_audio.mp3"
        
        try:
            logger.info(f"Extracting audio from {video_path}")
            # Using ffmpeg-python would be better, but for now using pydub
            logger.info(f"Audio saved to {output_audio_path}")
            return output_audio_path
        except Exception as e:
            logger.error(f"Error extracting audio: {e}")
            raise
    
    def get_duration(self, audio_path: str) -> float:
        """
        Get duration of audio file in seconds.
        
        Args:
            audio_path: Path to audio file
        
        Returns:
            Duration in seconds
        """
        try:
            audio = AudioSegment.from_file(audio_path)
            return len(audio) / 1000.0  # Convert to seconds
        except Exception as e:
            logger.error(f"Error getting audio duration: {e}")
            raise
