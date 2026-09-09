# Voiceover to Video Matcher

A tool that automatically matches audio narration to relevant video clips and images using AI-powered content analysis.

## Features

- **Audio Extraction & Analysis**: Extract voiceover from video files and transcribe narration
- **Visual Content Recognition**: Analyze video frames and images to extract semantic content
- **Smart Matching**: Match narration segments to visual content using AI embeddings
- **Automatic Synchronization**: Align video clips with corresponding voiceover narration
- **Multiple Formats**: Support for MP4, WebM, MOV, JPG, PNG, and more
- **Batch Processing**: Process multiple files efficiently

## Installation

```bash
git clone https://github.com/uzairaalizai/voiceover-to-video-matcher.git
cd voiceover-to-video-matcher
pip install -r requirements.txt
```

## Quick Start

```python
from matcher import VoiceoverMatcher

# Initialize matcher
matcher = VoiceoverMatcher()

# Match voiceover to video clips
results = matcher.match(
    voiceover_path='narration.mp3',
    media_paths=['clip1.mp4', 'clip2.mp4', 'image1.jpg'],
    output_json='results.json'
)

# View matches
for match in results:
    print(f"Narration: {match['text']}")
    print(f"Best match: {match['matched_media']}")
    print(f"Confidence: {match['confidence']}")
```

## Architecture

```
voiceover-to-video-matcher/
├── audio/
│   ├── extractor.py          # Extract audio from video
│   ├── transcriber.py        # Transcribe audio to text
│   └── segmenter.py          # Segment audio into sentences
├── vision/
│   ├── analyzer.py           # Extract visual content features
│   ├── frame_extractor.py    # Extract frames from video
│   └── captioner.py          # Generate descriptions for images
├── matching/
│   ├── embedder.py           # Create semantic embeddings
│   ├── matcher.py            # Match narration to content
│   └── scorer.py             # Score and rank matches
├── utils/
│   ├── config.py             # Configuration management
│   └── logger.py             # Logging utilities
├── matcher.py                # Main API
├── cli.py                    # Command-line interface
└── tests/                    # Unit tests
```

## Usage

### Python API

```python
from matcher import VoiceoverMatcher

matcher = VoiceoverMatcher(model='gpt-4-vision')
matches = matcher.match(voiceover='audio.mp3', media=['video.mp4', 'image.jpg'])
```

### Command Line

```bash
python cli.py match --voiceover narration.mp3 --media video.mp4 image.jpg --output results.json
```

## Configuration

Create a `.env` file:

```env
OPENAI_API_KEY=your_api_key_here
MODEL=gpt-4-vision
CONFIDENCE_THRESHOLD=0.7
```

## Output Format

```json
[
  {
    "narration_segment": "The sun rises over the mountains",
    "narration_time": {"start": 0.0, "end": 3.5},
    "matched_media": "video.mp4",
    "media_time": {"start": 120, "end": 125},
    "confidence": 0.95,
    "reasoning": "Visual shows sunrise with mountain scenery"
  }
]
```

## License

MIT
