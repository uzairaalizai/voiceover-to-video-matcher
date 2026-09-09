"""Command-line interface for voiceover matcher."""
import click
import json
import os
from pathlib import Path
from matcher import VoiceoverMatcher
from utils.logger import get_logger
from utils.config import Config

logger = get_logger()

@click.group()
def cli():
    """Voiceover to Video Matcher - Match audio narration to visual content."""
    pass

@cli.command()
@click.option('--voiceover', '-v', required=True, help='Path to voiceover audio file')
@click.option('--media', '-m', multiple=True, required=True, help='Paths to video/image files')
@click.option('--output', '-o', default='matches.json', help='Output JSON file path')
@click.option('--no-frames', is_flag=True, help='Skip frame extraction from videos')
@click.option('--confidence-threshold', type=float, default=None, help='Confidence threshold for matches')
@click.option('--verbose', is_flag=True, help='Verbose output')
def match(voiceover, media, output, no_frames, confidence_threshold, verbose):
    """
    Match voiceover to media files.
    
    Example:
        python cli.py match -v narration.mp3 -m video.mp4 -m image.jpg -o results.json
    """
    try:
        if verbose:
            click.echo("Starting voiceover matching...")
        
        # Validate input files
        if not os.path.exists(voiceover):
            click.echo(f"Error: Voiceover file not found: {voiceover}", err=True)
            return
        
        for media_file in media:
            if not os.path.exists(media_file):
                click.echo(f"Error: Media file not found: {media_file}", err=True)
                return
        
        # Initialize matcher
        matcher = VoiceoverMatcher()
        
        # Run matching
        click.echo(f"Processing voiceover: {voiceover}")
        click.echo(f"Processing {len(media)} media files...")
        
        matches = matcher.match(
            voiceover_path=voiceover,
            media_paths=list(media),
            output_json=output,
            extract_frames=not no_frames
        )
        
        # Display results
        click.echo(f"\n✓ Matching complete!")
        click.echo(f"Found {len(matches)} matches")
        
        if matches:
            click.echo("\nTop matches:")
            for i, match in enumerate(matches[:5], 1):
                click.echo(f"\n{i}. Narration: {match.get('narration_segment', 'N/A')[:60]}...")
                click.echo(f"   Media: {os.path.basename(match.get('media_path', 'N/A'))}")
                click.echo(f"   Confidence: {match.get('score', 0):.2%}")
        
        click.echo(f"\nFull results saved to: {output}")
    
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        if verbose:
            import traceback
            traceback.print_exc()

@cli.command()
@click.option('--audio', '-a', required=True, help='Path to audio file')
@click.option('--output', '-o', default='transcription.json', help='Output JSON file')
@click.option('--verbose', is_flag=True, help='Verbose output')
def transcribe(audio, output, verbose):
    """
    Transcribe audio file to text.
    
    Example:
        python cli.py transcribe -a narration.mp3 -o transcription.json
    """
    try:
        if verbose:
            click.echo("Transcribing audio...")
        
        if not os.path.exists(audio):
            click.echo(f"Error: Audio file not found: {audio}", err=True)
            return
        
        from audio.transcriber import AudioTranscriber
        from audio.segmenter import AudioSegmenter
        
        transcriber = AudioTranscriber()
        segmenter = AudioSegmenter()
        
        # Transcribe
        click.echo(f"Transcribing: {audio}")
        transcription = transcriber.transcribe(audio)
        
        # Get word timestamps
        word_timestamps = transcriber.get_word_timestamps(audio)
        
        # Segment
        segments = segmenter.segment_by_sentences(
            transcription['text'],
            word_timestamps
        )
        
        # Save results
        results = {
            'full_text': transcription['text'],
            'segments': segments,
            'word_timestamps': word_timestamps
        }
        
        os.makedirs(os.path.dirname(output) or '.', exist_ok=True)
        with open(output, 'w') as f:
            json.dump(results, f, indent=2)
        
        click.echo(f"✓ Transcription complete!")
        click.echo(f"Segments: {len(segments)}")
        click.echo(f"Results saved to: {output}")
    
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        if verbose:
            import traceback
            traceback.print_exc()

@cli.command()
@click.option('--video', '-v', required=True, help='Path to video file')
@click.option('--output', '-o', default='frames', help='Output directory for frames')
@click.option('--sample-rate', type=int, default=1, help='Extract every nth frame')
@click.option('--verbose', is_flag=True, help='Verbose output')
def extract_frames(video, output, sample_rate, verbose):
    """
    Extract frames from video file.
    
    Example:
        python cli.py extract-frames -v video.mp4 -o ./frames --sample-rate 5
    """
    try:
        if verbose:
            click.echo("Extracting frames...")
        
        if not os.path.exists(video):
            click.echo(f"Error: Video file not found: {video}", err=True)
            return
        
        from vision.frame_extractor import FrameExtractor
        
        extractor = FrameExtractor(sample_rate=sample_rate)
        
        click.echo(f"Extracting frames from: {video}")
        frames = extractor.extract_frames(video, output_dir=output)
        
        click.echo(f"✓ Extraction complete!")
        click.echo(f"Extracted {len(frames)} frames to: {output}")
    
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        if verbose:
            import traceback
            traceback.print_exc()

@cli.command()
@click.option('--image', '-i', required=True, help='Path to image file')
@click.option('--verbose', is_flag=True, help='Verbose output')
def analyze_image(image, verbose):
    """
    Analyze image using vision AI.
    
    Example:
        python cli.py analyze-image -i photo.jpg
    """
    try:
        if verbose:
            click.echo("Analyzing image...")
        
        if not os.path.exists(image):
            click.echo(f"Error: Image file not found: {image}", err=True)
            return
        
        from vision.analyzer import VisualAnalyzer
        
        analyzer = VisualAnalyzer()
        
        click.echo(f"Analyzing: {image}")
        analysis = analyzer.analyze_image(image)
        
        click.echo(f"\n✓ Analysis complete!")
        click.echo(f"Description: {analysis.get('description', 'N/A')}")
        click.echo(f"Tags: {', '.join(analysis.get('tags', []))}")
        click.echo(f"Confidence: {analysis.get('confidence', 0):.2%}")
    
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        if verbose:
            import traceback
            traceback.print_exc()

@cli.command()
def config():
    """Display current configuration."""
    click.echo("\n" + "="*50)
    click.echo("VOICEOVER MATCHER CONFIGURATION")
    click.echo("="*50)
    
    config_items = [
        ('API Key', '***' if Config.OPENAI_API_KEY else 'NOT SET'),
        ('Model', Config.MODEL),
        ('Confidence Threshold', f"{Config.CONFIDENCE_THRESHOLD:.2%}"),
        ('Min Match Score', f"{Config.MIN_MATCH_SCORE:.2%}"),
        ('Frame Sample Rate', f"1/{Config.FRAME_SAMPLE_RATE}"),
        ('Audio Segment Min Length', f"{Config.AUDIO_SEGMENT_MIN_LENGTH}s"),
        ('Debug Mode', 'ON' if Config.DEBUG else 'OFF'),
        ('Verbose', 'ON' if Config.VERBOSE else 'OFF'),
    ]
    
    for key, value in config_items:
        click.echo(f"{key:<30} {value}")
    
    click.echo("\n" + "="*50)
    click.echo("Configure via .env file")
    click.echo("="*50)

if __name__ == '__main__':
    cli()
