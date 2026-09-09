"""Main API for voiceover to video matcher."""
import os
from typing import List, Dict, Union, Optional
from pathlib import Path

from audio.extractor import AudioExtractor
from audio.transcriber import AudioTranscriber
from audio.segmenter import AudioSegmenter
from vision.frame_extractor import FrameExtractor
from vision.analyzer import VisualAnalyzer
from matching.embedder import Embedder
from matching.matcher import NarrationMatcher
from matching.scorer import MatchScorer
from utils.logger import get_logger
from utils.config import Config

logger = get_logger()

class VoiceoverMatcher:
    """Main API for matching voiceover to video/image content."""
    
    def __init__(self, model: str = None, validate_config: bool = True):
        """
        Initialize VoiceoverMatcher.
        
        Args:
            model: Model name (default: gpt-4-vision)
            validate_config: Whether to validate configuration
        """
        if validate_config:
            Config.validate()
        
        self.model = model or Config.MODEL
        
        # Initialize components
        logger.info("Initializing VoiceoverMatcher components")
        self.audio_extractor = AudioExtractor()
        self.audio_transcriber = AudioTranscriber()
        self.audio_segmenter = AudioSegmenter(min_length=Config.AUDIO_SEGMENT_MIN_LENGTH)
        self.frame_extractor = FrameExtractor(sample_rate=Config.FRAME_SAMPLE_RATE)
        self.visual_analyzer = VisualAnalyzer(model=self.model)
        self.embedder = Embedder()
        self.matcher = NarrationMatcher(embedder=self.embedder)
        
        os.makedirs(Config.OUTPUT_DIR, exist_ok=True)
        logger.info("VoiceoverMatcher initialized successfully")
    
    def match(
        self,
        voiceover_path: str,
        media_paths: List[str],
        output_json: Optional[str] = None,
        extract_frames: bool = True
    ) -> List[Dict]:
        """
        Match voiceover to media files.
        
        Args:
            voiceover_path: Path to audio file
            media_paths: List of video/image file paths
            output_json: Optional output JSON file path
            extract_frames: Whether to extract frames from videos
        
        Returns:
            List of matches with timing and scoring information
        """
        try:
            logger.info("Starting voiceover to media matching")
            
            # Step 1: Process audio
            logger.info("Step 1: Processing audio")
            narration_segments = self._process_audio(voiceover_path)
            
            # Step 2: Process media
            logger.info("Step 2: Processing media files")
            media_items = self._process_media(media_paths, extract_frames=extract_frames)
            
            # Step 3: Match segments to media
            logger.info("Step 3: Matching narration to media")
            matches = self.matcher.match_segments_to_media(narration_segments, media_items)
            
            # Step 4: Score and rank matches
            logger.info("Step 4: Scoring and ranking matches")
            matches = MatchScorer.rank_matches(matches)
            matches = MatchScorer.filter_by_confidence(matches)
            
            # Step 5: Save results
            if output_json:
                self._save_results(matches, output_json)
            
            logger.info(f"Matching complete. Found {len(matches)} matches")
            return matches
        
        except Exception as e:
            logger.error(f"Error in match: {e}")
            raise
    
    def _process_audio(self, audio_path: str) -> List[Dict]:
        """
        Process audio file and return narration segments.
        
        Args:
            audio_path: Path to audio file
        
        Returns:
            List of narration segments with timing
        """
        try:
            # Transcribe audio
            logger.info(f"Transcribing audio: {audio_path}")
            transcription = self.audio_transcriber.transcribe(audio_path)
            
            if not transcription['text']:
                logger.warning("No speech detected in audio")
                return []
            
            # Get word timestamps
            word_timestamps = self.audio_transcriber.get_word_timestamps(audio_path)
            
            # Segment audio
            logger.info("Segmenting audio into narration segments")
            segments = self.audio_segmenter.segment_by_sentences(
                transcription['text'],
                word_timestamps
            )
            
            logger.info(f"Created {len(segments)} narration segments")
            return segments
        
        except Exception as e:
            logger.error(f"Error processing audio: {e}")
            raise
    
    def _process_media(self, media_paths: List[str], extract_frames: bool = True) -> List[Dict]:
        """
        Process media files and return analyzed items.
        
        Args:
            media_paths: List of media file paths
            extract_frames: Whether to extract frames from videos
        
        Returns:
            List of media items with descriptions and analysis
        """
        media_items = []
        
        for media_path in media_paths:
            try:
                if not os.path.exists(media_path):
                    logger.warning(f"Media file not found: {media_path}")
                    continue
                
                _, ext = os.path.splitext(media_path)
                ext = ext.lower()
                
                if ext in Config.VIDEO_FORMATS:
                    logger.info(f"Processing video: {media_path}")
                    
                    if extract_frames:
                        # Extract frames from video
                        frames = self.frame_extractor.extract_frames(media_path)
                        
                        # Analyze frames
                        for frame_path in frames:
                            description = self.visual_analyzer.extract_scene_description(frame_path)
                            media_items.append({
                                'path': media_path,
                                'frame_path': frame_path,
                                'description': description,
                                'type': 'video_frame'
                            })
                    else:
                        # Get video description without frame extraction
                        description = f"Video file: {os.path.basename(media_path)}"
                        media_items.append({
                            'path': media_path,
                            'description': description,
                            'type': 'video'
                        })
                
                elif ext in Config.IMAGE_FORMATS:
                    logger.info(f"Processing image: {media_path}")
                    description = self.visual_analyzer.extract_scene_description(media_path)
                    media_items.append({
                        'path': media_path,
                        'description': description,
                        'type': 'image'
                    })
            
            except Exception as e:
                logger.error(f"Error processing media {media_path}: {e}")
                continue
        
        logger.info(f"Processed {len(media_items)} media items")
        return media_items
    
    def _save_results(self, matches: List[Dict], output_path: str) -> None:
        """
        Save matching results to JSON file.
        
        Args:
            matches: List of matches
            output_path: Path to save JSON results
        """
        import json
        
        try:
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
            
            with open(output_path, 'w') as f:
                json.dump(matches, f, indent=2)
            
            logger.info(f"Results saved to {output_path}")
        
        except Exception as e:
            logger.error(f"Error saving results: {e}")
            raise
