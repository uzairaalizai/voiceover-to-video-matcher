"""Integration tests for voiceover matcher."""
import pytest
import os
import json
import tempfile
from pathlib import Path

class TestIntegration:
    """Integration tests."""
    
    @pytest.mark.skip(reason="Requires media files")
    def test_end_to_end_matching(self):
        """Test end-to-end matching workflow."""
        from matcher import VoiceoverMatcher
        
        # This would require actual media files
        matcher = VoiceoverMatcher()
        
        voiceover = 'test_audio.mp3'
        media = ['test_video.mp4', 'test_image.jpg']
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = os.path.join(tmpdir, 'matches.json')
            matches = matcher.match(
                voiceover_path=voiceover,
                media_paths=media,
                output_json=output_file
            )
            
            assert len(matches) > 0
            assert os.path.exists(output_file)
            
            with open(output_file, 'r') as f:
                saved_matches = json.load(f)
            
            assert len(saved_matches) == len(matches)

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
