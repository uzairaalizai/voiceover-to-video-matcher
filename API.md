# API Documentation

Complete API reference for the Voiceover to Video Matcher.

## Main API: VoiceoverMatcher

### Initialization

```python
from matcher import VoiceoverMatcher

matcher = VoiceoverMatcher(
    model='gpt-4-vision',  # Optional: AI model to use
    validate_config=True   # Optional: validate config on init
)
```

**Parameters:**
- `model` (str, optional): AI model for vision analysis. Default: `gpt-4-vision`
- `validate_config` (bool, optional): Whether to validate configuration. Default: `True`

### Methods

#### match()

Match voiceover to media files.

```python
matches = matcher.match(
    voiceover_path='narration.mp3',
    media_paths=['video.mp4', 'image.jpg'],
    output_json='results.json',
    extract_frames=True
)
```

**Parameters:**
- `voiceover_path` (str, required): Path to audio file
- `media_paths` (List[str], required): Paths to video/image files
- `output_json` (str, optional): Path to save JSON results
- `extract_frames` (bool, optional): Extract frames from videos. Default: `True`

**Returns:** List[Dict] - Matches with timing and scoring information

**Raises:** FileNotFoundError, ValueError

---

## Audio Processing

### AudioExtractor

Extract audio from video files.

```python
from audio.extractor import AudioExtractor

extractor = AudioExtractor()
audio_path = extractor.extract_from_video('video.mp4')
duration = extractor.get_duration(audio_path)
```

#### Methods

**extract_from_video(video_path, output_audio_path=None) -> str**
- Extract audio from video
- Returns: Path to extracted audio file

**get_duration(audio_path) -> float**
- Get audio duration in seconds
- Returns: Duration as float

---

### AudioTranscriber

Transcribe audio to text.

```python
from audio.transcriber import AudioTranscriber

transcriber = AudioTranscriber()
transcription = transcriber.transcribe('audio.mp3')
word_timestamps = transcriber.get_word_timestamps('audio.mp3')
```

#### Methods

**transcribe(audio_path) -> Dict**
- Transcribe audio file
- Returns: Dict with 'text', 'confidence', 'language'

**get_word_timestamps(audio_path) -> List[Dict]**
- Get word-level timing information
- Returns: List of dicts with 'word', 'start', 'end'

---

### AudioSegmenter

Segment audio transcription into sentences.

```python
from audio.segmenter import AudioSegmenter

segmenter = AudioSegmenter(min_length=2.0)
segments = segmenter.segment_by_sentences(
    transcription='Full text here',
    word_timestamps=[...]
)
```

#### Methods

**segment_by_sentences(transcription, word_timestamps) -> List[Dict]**
- Segment into sentences
- Returns: List of segments with 'text', 'start_time', 'end_time', 'duration'

**segment_by_duration(transcription, duration, segment_duration=5.0) -> List[Dict]**
- Segment into fixed-duration chunks
- Returns: List of segments with timing

---

## Vision Processing

### FrameExtractor

Extract frames from video files.

```python
from vision.frame_extractor import FrameExtractor

extractor = FrameExtractor(sample_rate=5)
frames = extractor.extract_frames('video.mp4', output_dir='frames')
frame = extractor.get_frame_at_time('video.mp4', time_seconds=30.5)
```

#### Methods

**extract_frames(video_path, output_dir=None, sample_rate=None) -> List[str]**
- Extract frames from video
- Returns: List of frame file paths

**get_frame_at_time(video_path, time_seconds) -> str**
- Extract single frame at specific time
- Returns: Path to extracted frame

---

### VisualAnalyzer

Analyze visual content using AI.

```python
from vision.analyzer import VisualAnalyzer

analyzer = VisualAnalyzer(model='gpt-4-vision')
analysis = analyzer.analyze_image('photo.jpg')
descriptions = analyzer.analyze_frames(['frame1.jpg', 'frame2.jpg'])
```

#### Methods

**analyze_image(image_path, prompt=None) -> Dict**
- Analyze single image
- Returns: Dict with 'description', 'tags', 'confidence'

**analyze_frames(frame_paths, sample_rate=1) -> List[Dict]**
- Analyze multiple frames
- Returns: List of analysis results

**extract_objects(image_path) -> List[Dict]**
- Extract detected objects
- Returns: List of objects with confidence scores

**extract_scene_description(image_path) -> str**
- Get scene description
- Returns: Scene description string

---

## Matching

### Embedder

Create semantic embeddings.

```python
from matching.embedder import Embedder
import numpy as np

embedder = Embedder(model_name='all-MiniLM-L6-v2')
embedding = embedder.embed_text('Sample text')
similarity = embedder.similarity(embedding1, embedding2)
```

#### Methods

**embed_text(text) -> np.ndarray**
- Create embedding for text
- Returns: Embedding vector

**embed_texts(texts) -> np.ndarray**
- Create embeddings for multiple texts
- Returns: Matrix of embeddings

**similarity(embedding1, embedding2) -> float**
- Calculate cosine similarity (0-1)
- Returns: Similarity score

**batch_similarity(embedding, embeddings) -> np.ndarray**
- Calculate similarities in batch
- Returns: Array of similarity scores

---

### NarrationMatcher

Match narration to visual content.

```python
from matching.matcher import NarrationMatcher

matcher = NarrationMatcher()
matches = matcher.match_segment_to_media(
    'The dog is running',
    [{'path': 'video.mp4', 'description': 'A dog running in field'}]
)
```

#### Methods

**match_segment_to_media(narration_text, media_descriptions) -> List[Dict]**
- Match single narration segment to media
- Returns: Sorted list of matches with scores

**match_segments_to_media(narration_segments, media_items) -> List[Dict]**
- Match multiple segments to media
- Returns: List of matches with timing

**score_match(narration, media_description, additional_features=None) -> float**
- Calculate detailed match score
- Returns: Score (0-1)

---

### MatchScorer

Score and rank matches.

```python
from matching.scorer import MatchScorer

ranked = MatchScorer.rank_matches(matches)
filtered = MatchScorer.filter_by_confidence(matches, threshold=0.7)
top = MatchScorer.get_top_matches(matches, top_n=5)
```

#### Methods

**rank_matches(matches, scoring_weights=None) -> List[Dict]**
- Rank matches by multiple criteria
- Returns: Sorted matches

**filter_by_confidence(matches, threshold=None) -> List[Dict]**
- Filter matches by confidence
- Returns: Filtered matches

**get_top_matches(matches, top_n=5) -> List[Dict]**
- Get top N matches
- Returns: Top N matches

---

## Configuration

### Config Class

```python
from utils.config import Config

# Read configuration
print(Config.OPENAI_API_KEY)
print(Config.CONFIDENCE_THRESHOLD)
print(Config.MODEL)

# Validate configuration
Config.validate()
```

**Available Properties:**
- `OPENAI_API_KEY` (str): OpenAI API key
- `MODEL` (str): AI model name
- `CONFIDENCE_THRESHOLD` (float): Confidence threshold for matches
- `MIN_MATCH_SCORE` (float): Minimum match score
- `MAX_MATCHES_PER_SEGMENT` (int): Max matches per segment
- `FRAME_SAMPLE_RATE` (int): Extract every nth frame
- `AUDIO_SEGMENT_MIN_LENGTH` (float): Min segment length in seconds
- `VIDEO_CHUNK_DURATION` (int): Video processing chunk size
- `DEBUG` (bool): Debug mode
- `VERBOSE` (bool): Verbose logging
- `VIDEO_FORMATS` (set): Supported video formats
- `IMAGE_FORMATS` (set): Supported image formats
- `AUDIO_FORMATS` (set): Supported audio formats

---

## Logging

```python
from utils.logger import get_logger

logger = get_logger()
logger.info('Processing started')
logger.warning('Low confidence match')
logger.error('Error occurred')
```

**Log Levels:**
- DEBUG: Detailed diagnostic info
- INFO: Informational messages
- WARNING: Warning messages
- ERROR: Error messages

Logs are saved to `logs/` directory and console.

---

## Return Types

### Match Object

```python
{
    'narration_segment': str,        # Narration text
    'narration_time': {
        'start': float,              # Start time in seconds
        'end': float                 # End time in seconds
    },
    'media_path': str,               # Path to matched media
    'description': str,              # Media description
    'score': float,                  # Semantic similarity (0-1)
    'combined_score': float,         # Combined score (0-1)
    'confidence': float,             # Confidence score (0-1)
    'type': str                      # 'video_frame', 'video', or 'image'
}
```

### Transcription Object

```python
{
    'text': str,                     # Transcribed text
    'confidence': float,             # Confidence (0-1)
    'language': str                  # Language code (e.g., 'en-US')
}
```

### Segment Object

```python
{
    'text': str,                     # Segment text
    'start_time': float,             # Start time in seconds
    'end_time': float,               # End time in seconds
    'duration': float                # Duration in seconds
}
```

---

## Error Handling

```python
try:
    matches = matcher.match(
        voiceover_path='narration.mp3',
        media_paths=['video.mp4']
    )
except FileNotFoundError as e:
    print(f"File not found: {e}")
except ValueError as e:
    print(f"Invalid value: {e}")
except Exception as e:
    print(f"Error: {e}")
```

**Common Exceptions:**
- `FileNotFoundError`: Input file not found
- `ValueError`: Invalid configuration or parameters
- `Exception`: General processing errors

---

## Performance Considerations

1. **Frame Extraction**: Slower for large videos. Use `extract_frames=False` or increase `FRAME_SAMPLE_RATE`
2. **Embedding Creation**: Uses pre-trained models, typically fast
3. **API Calls**: Vision analysis uses OpenAI API, subject to rate limits
4. **Memory**: Store results incrementally for large batches

---

## Version Info

Currently at version 1.0.0
