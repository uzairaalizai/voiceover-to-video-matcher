"""Frame extraction from video files."""
import os
import cv2
from pathlib import Path
from typing import List
from utils.logger import get_logger

logger = get_logger()

class FrameExtractor:
    """Extract frames from video files."""
    
    def __init__(self, sample_rate: int = 1):
        """
        Initialize frame extractor.
        
        Args:
            sample_rate: Extract every nth frame
        """
        self.sample_rate = sample_rate
    
    def extract_frames(self, video_path: str, output_dir: str = None, sample_rate: int = None) -> List[str]:
        """
        Extract frames from video file.
        
        Args:
            video_path: Path to video file
            output_dir: Directory to save frames
            sample_rate: Override default sample rate
        
        Returns:
            List of paths to extracted frame images
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        sample_rate = sample_rate or self.sample_rate
        
        if output_dir is None:
            base_name = os.path.splitext(os.path.basename(video_path))[0]
            output_dir = f"frames_{base_name}"
        
        os.makedirs(output_dir, exist_ok=True)
        
        try:
            logger.info(f"Extracting frames from {video_path}")
            
            cap = cv2.VideoCapture(video_path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            frames = []
            frame_idx = 0
            extracted_count = 0
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                if frame_idx % sample_rate == 0:
                    frame_path = os.path.join(output_dir, f"frame_{extracted_count:06d}.jpg")
                    cv2.imwrite(frame_path, frame)
                    frames.append(frame_path)
                    extracted_count += 1
                
                frame_idx += 1
            
            cap.release()
            
            logger.info(f"Extracted {extracted_count} frames from {frame_count} total frames")
            return frames
        
        except Exception as e:
            logger.error(f"Error extracting frames: {e}")
            raise
    
    def get_frame_at_time(self, video_path: str, time_seconds: float) -> str:
        """
        Extract a single frame at specific time.
        
        Args:
            video_path: Path to video file
            time_seconds: Time in seconds
        
        Returns:
            Path to extracted frame
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        try:
            cap = cv2.VideoCapture(video_path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_number = int(time_seconds * fps)
            
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            ret, frame = cap.read()
            cap.release()
            
            if ret:
                base_name = os.path.splitext(os.path.basename(video_path))[0]
                frame_path = f"frame_{base_name}_{time_seconds:.2f}s.jpg"
                cv2.imwrite(frame_path, frame)
                return frame_path
            else:
                raise ValueError(f"Could not read frame at {time_seconds}s")
        
        except Exception as e:
            logger.error(f"Error extracting frame at {time_seconds}s: {e}")
            raise
