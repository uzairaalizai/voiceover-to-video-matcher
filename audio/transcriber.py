"""Audio transcription utilities."""
import os
from pydub import AudioSegment
from pydub.utils import mediainfo
import speech_recognition as sr
from utils.logger import get_logger

logger = get_logger()

class AudioTranscriber:
    """Transcribe audio to text."""
    
    def __init__(self):
        """Initialize audio transcriber."""
        self.recognizer = sr.Recognizer()
    
    def transcribe(self, audio_path: str) -> dict:
        """
        Transcribe audio file to text.
        
        Args:
            audio_path: Path to audio file
        
        Returns:
            Dictionary with transcription and metadata
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        try:
            logger.info(f"Transcribing audio from {audio_path}")
            
            with sr.AudioFile(audio_path) as source:
                audio_data = self.recognizer.record(source)
            
            text = self.recognizer.recognize_google(audio_data)
            
            logger.info(f"Transcription complete. Length: {len(text)} characters")
            
            return {
                'text': text,
                'confidence': 1.0,
                'language': 'en-US'
            }
        except sr.UnknownValueError:
            logger.warning("Could not understand audio")
            return {'text': '', 'confidence': 0.0}
        except sr.RequestError as e:
            logger.error(f"Transcription error: {e}")
            raise
    
    def get_word_timestamps(self, audio_path: str) -> list:
        """
        Get word-level timestamps from audio.
        
        Args:
            audio_path: Path to audio file
        
        Returns:
            List of words with timestamps
        """
        # Placeholder for more advanced timing
        transcription = self.transcribe(audio_path)
        words = transcription['text'].split()
        
        # Basic timing distribution
        duration = len(AudioSegment.from_file(audio_path)) / 1000.0
        word_duration = duration / len(words) if words else 0
        
        return [
            {'word': word, 'start': i * word_duration, 'end': (i + 1) * word_duration}
            for i, word in enumerate(words)
        ]
