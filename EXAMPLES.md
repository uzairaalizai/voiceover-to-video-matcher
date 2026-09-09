# Usage Examples

This document provides practical examples of how to use the Voiceover to Video Matcher.

## Installation

```bash
git clone https://github.com/uzairaalizai/voiceover-to-video-matcher.git
cd voiceover-to-video-matcher
pip install -r requirements.txt
```

## Setup

1. Create a `.env` file:

```env
OPENAI_API_KEY=your_api_key_here
MODEL=gpt-4-vision
CONFIDENCE_THRESHOLD=0.7
```

2. Ensure you have ffmpeg installed (for video processing):

```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt-get install ffmpeg

# Windows
choco install ffmpeg
```

## Python API Examples

### Basic Usage

```python
from matcher import VoiceoverMatcher

# Initialize matcher
matcher = VoiceoverMatcher()

# Match voiceover to media
results = matcher.match(
    voiceover_path='narration.mp3',
    media_paths=['video1.mp4', 'video2.mp4', 'image1.jpg'],
    output_json='results.json'
)

# Print results
for match in results:
    print(f"Narration: {match['narration_segment']}")
    print(f"Matched media: {match['media_path']}")
    print(f"Confidence: {match['score']:.2%}")
    print()
```

### Advanced Usage

```python
from matcher import VoiceoverMatcher
from matching.scorer import MatchScorer

matcher = VoiceoverMatcher()

# Get all matches (including low confidence)
all_matches = matcher.match(
    voiceover_path='narration.mp3',
    media_paths=['video.mp4', 'image.jpg'],
    output_json='all_matches.json',
    extract_frames=True  # Extract frames from videos
)

# Filter by confidence
high_confidence = MatchScorer.filter_by_confidence(
    all_matches,
    threshold=0.8
)

# Get top matches
top_5 = MatchScorer.get_top_matches(all_matches, top_n=5)

for match in top_5:
    print(f"{match['narration_segment'][:50]}... -> {match['media_path']}")
```

### Processing Individual Components

```python
from audio.transcriber import AudioTranscriber
from audio.segmenter import AudioSegmenter
from vision.frame_extractor import FrameExtractor
from vision.analyzer import VisualAnalyzer

# Transcribe audio
transcriber = AudioTranscriber()
transcription = transcriber.transcribe('narration.mp3')
print(f"Full text: {transcription['text']}")

# Segment audio
segmenter = AudioSegmenter(min_length=2.0)
word_timestamps = transcriber.get_word_timestamps('narration.mp3')
segments = segmenter.segment_by_sentences(
    transcription['text'],
    word_timestamps
)

# Extract and analyze frames
extractor = FrameExtractor(sample_rate=5)  # Every 5th frame
frames = extractor.extract_frames('video.mp4', output_dir='frames')

analyzer = VisualAnalyzer()
for frame in frames:
    description = analyzer.extract_scene_description(frame)
    print(f"Frame: {frame}")
    print(f"Description: {description}")
```

## Command Line Examples

### Match voiceover to media

```bash
# Basic matching
python cli.py match --voiceover narration.mp3 --media video.mp4 --media image.jpg --output results.json

# With custom confidence threshold
python cli.py match \
  --voiceover narration.mp3 \
  --media video.mp4 \
  --media image.jpg \
  --output results.json \
  --confidence-threshold 0.8

# Verbose output
python cli.py match --voiceover narration.mp3 --media video.mp4 --verbose

# Skip frame extraction
python cli.py match --voiceover narration.mp3 --media video.mp4 --no-frames
```

### Transcribe audio

```bash
# Basic transcription
python cli.py transcribe --audio narration.mp3 --output transcription.json

# Verbose output
python cli.py transcribe --audio narration.mp3 --output transcription.json --verbose
```

### Extract video frames

```bash
# Extract every frame
python cli.py extract-frames --video video.mp4 --output ./frames

# Extract every 5th frame
python cli.py extract-frames --video video.mp4 --output ./frames --sample-rate 5

# Verbose output
python cli.py extract-frames --video video.mp4 --output ./frames --verbose
```

### Analyze images

```bash
# Analyze single image
python cli.py analyze-image --image photo.jpg

# Verbose output
python cli.py analyze-image --image photo.jpg --verbose
```

### Check configuration

```bash
python cli.py config
```

## Real-World Scenarios

### Scenario 1: Video Tutorial with Narration

You have:
- `tutorial_narration.mp3` - Audio narration explaining steps
- `tutorial_videos/` - Directory with multiple video clips

```python
from matcher import VoiceoverMatcher
import os

matcher = VoiceoverMatcher()

# Get all video files
media_files = [
    os.path.join('tutorial_videos', f)
    for f in os.listdir('tutorial_videos')
    if f.endswith('.mp4')
]

# Match
results = matcher.match(
    voiceover_path='tutorial_narration.mp3',
    media_paths=media_files,
    output_json='tutorial_matches.json'
)

# Create a synchronized playlist
for match in results:
    print(f"Time: {match['narration_time']['start']:.1f}s - {match['narration_time']['end']:.1f}s")
    print(f"Text: {match['narration_segment']}")
    print(f"Video: {match['media_path']} (Confidence: {match['score']:.2%})")
    print()
```

### Scenario 2: Documentary with Stock Footage

You have:
- `documentary_narration.mp3` - Documentary narration
- `stock_footage/` - Directory with stock photos and videos

```bash
# Get all media files
python cli.py match \
  --voiceover documentary_narration.mp3 \
  --media stock_footage/video1.mp4 \
  --media stock_footage/video2.mp4 \
  --media stock_footage/photo1.jpg \
  --media stock_footage/photo2.jpg \
  --output documentary_matches.json \
  --confidence-threshold 0.75 \
  --verbose
```

### Scenario 3: Social Media Content Generation

You have:
- `script.mp3` - Voice script
- `clips/` - Multiple short video clips
- `images/` - Background images

```python
from matcher import VoiceoverMatcher
from matching.scorer import MatchScorer
import json
import os

matcher = VoiceoverMatcher()

# Collect all media
media_files = []
for folder in ['clips', 'images']:
    for file in os.listdir(folder):
        media_files.append(os.path.join(folder, file))

# Match
results = matcher.match(
    voiceover_path='script.mp3',
    media_paths=media_files,
    output_json='social_media_matches.json'
)

# Filter for high confidence matches
high_confidence = MatchScorer.filter_by_confidence(results, threshold=0.8)

# Group by narration segment
by_segment = {}
for match in high_confidence:
    segment = match['narration_segment']
    if segment not in by_segment:
        by_segment[segment] = []
    by_segment[segment].append(match)

# Print organized results
for segment, matches in by_segment.items():
    print(f"Segment: {segment}")
    for match in matches:
        print(f"  - {os.path.basename(match['media_path'])} ({match['score']:.2%})")
```

## Output Format

The matcher outputs results in JSON format:

```json
[
  {
    "narration_segment": "The sun rises over the mountains",
    "narration_time": {
      "start": 0.0,
      "end": 3.5
    },
    "matched_media": "video.mp4",
    "media_time": {
      "start": 120,
      "end": 125
    },
    "score": 0.95,
    "combined_score": 0.92,
    "confidence": 0.95
  },
  {
    "narration_segment": "Birds fly across the sky",
    "narration_time": {
      "start": 3.5,
      "end": 7.2
    },
    "matched_media": "image.jpg",
    "score": 0.87,
    "combined_score": 0.85,
    "confidence": 0.87
  }
]
```

## Troubleshooting

### Issue: "OPENAI_API_KEY not set"

**Solution:** Create a `.env` file with your API key:

```env
OPENAI_API_KEY=sk-...
```

### Issue: No matches found

**Solution:** Lower the confidence threshold:

```python
# In code
from utils.config import Config
Config.CONFIDENCE_THRESHOLD = 0.5

# Or via CLI
python cli.py match ... --confidence-threshold 0.5
```

### Issue: Slow processing

**Solution:** Skip frame extraction or reduce sample rate:

```python
# Extract fewer frames
matcher.match(
    voiceover_path='audio.mp3',
    media_paths=['video.mp4'],
    extract_frames=False  # Skip extraction
)

# Or
from vision.frame_extractor import FrameExtractor
from utils.config import Config
Config.FRAME_SAMPLE_RATE = 10  # Every 10th frame
```

## Performance Tips

1. **For large videos:** Use `--no-frames` or reduce `FRAME_SAMPLE_RATE`
2. **For batch processing:** Process multiple files in one call
3. **For accuracy:** Use videos/images with clear, distinct content
4. **For speed:** Lower `CONFIDENCE_THRESHOLD` to reduce processing time

## Next Steps

- See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines
- Check [API.md](API.md) for detailed API documentation
- Review [tests/](tests/) for more usage examples
