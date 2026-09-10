import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = Path(os.environ.get('STUDIO_DATA', '/tmp/scenevault-data')).resolve()
DATA.mkdir(parents=True, exist_ok=True)


def write(path, value):
    path = Path(path)
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2))
    temporary.replace(path)


def ffmpeg():
    import imageio_ffmpeg
    return os.environ.get('FFMPEG_BINARY') or imageio_ffmpeg.get_ffmpeg_exe()


def command(args):
    result = subprocess.run(args, capture_output=True, text=True, timeout=7200)
    if result.returncode:
        raise RuntimeError(result.stderr[-1800:])
    return result.stdout


def probe(path):
    import av
    with av.open(str(path)) as container:
        duration = (container.duration or 0) / av.time_base
        streams = list(container.streams.video)
        return {'duration': duration, 'width': streams[0].width if streams else 0,
                'height': streams[0].height if streams else 0,
                'audio': bool(container.streams.audio)}
