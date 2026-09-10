"""Real-media smoke run. No fabricated matching scores or mocked model outputs."""
import json
import os
import subprocess
import sys
from pathlib import Path

repo=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(repo.parent))
from hosted.common import command,ffmpeg,probe,write

upload=Path(sys.argv[1])
out=Path(sys.argv[2]);out.mkdir(parents=True,exist_ok=True)
source=next(upload.glob('The Rise*.mp4'))
voice=next(upload.glob('ElevenLabs*.wav'))
command([ffmpeg(),'-nostdin','-y','-v','error','-ss','150','-i',str(source),'-t','50','-c','copy',str(out/'video')+'.mp4'])
(out/'video.mp4').replace(out/'video')
command([ffmpeg(),'-nostdin','-y','-v','error','-i',str(voice),'-t','10','-c:a','pcm_s16le',str(out/'voice.wav')])
(out/'voice.wav').replace(out/'voice')
write(out/'job.json',dict(id=out.name,status='queued',created=0,settings=dict(title='NYPD BLUE',script='',quality='preview',grade='documentary',motion=True,masking=True,graphics=True,captions=True,sfx=True,transitions=True,images=0),voice=probe(out/'voice'),source=probe(out/'video')))
subprocess.run([sys.executable,str(repo/'engine.py'),'all',str(out)],check=True)
print(json.dumps(probe(out/'final.mp4')))
