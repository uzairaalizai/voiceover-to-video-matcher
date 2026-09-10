import asyncio
import hashlib
import hmac
import json
import os
import secrets
import signal
import shutil
import subprocess
import sys
import threading
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from hosted.common import ROOT, DATA, write, probe

PASSWORD = os.environ.get('STUDIO_PASSWORD', '')
SESSIONS = {}
ATTEMPTS = {}
LOCK = threading.Lock()
ACTIVE = {}
MAX_BYTES = 2 * 1024**3
COOKIE = 'scenevault_session'


def job_dir(identifier):
    if len(identifier) != 32 or any(c not in '0123456789abcdef' for c in identifier):
        raise HTTPException(404)
    directory = DATA / identifier
    if not (directory / 'job.json').exists():
        raise HTTPException(404)
    return directory


def read_job(identifier):
    return json.loads((job_dir(identifier) / 'job.json').read_text())


@asynccontextmanager
async def lifespan(app):
    for path in DATA.glob('*/job.json'):
        job = json.loads(path.read_text())
        if job['status'] in {'queued', 'processing', 'rendering'}:
            job.update(status='interrupted', message='Server restarted. Re-run the saved job.')
            write(path, job)
    yield
    for process in list(ACTIVE.values()):
        try: os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError: pass


app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None)


@app.middleware('http')
async def private_api(request: Request, call_next):
    if request.url.path.startswith('/api/') and request.url.path not in {'/api/login', '/api/session'}:
        token = request.cookies.get(COOKIE, '')
        if SESSIONS.get(token, 0) < time.time():
            return JSONResponse({'detail': 'Please sign in.'}, status_code=401)
        origin = request.headers.get('origin')
        if request.method not in {'GET', 'HEAD'} and origin:
            from urllib.parse import urlparse
            if urlparse(origin).netloc != request.headers.get('host'):
                return JSONResponse({'detail': 'Origin rejected'}, status_code=403)
    response = await call_next(request)
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Referrer-Policy'] = 'same-origin'
    response.headers['X-Frame-Options'] = 'DENY'
    if request.url.path.startswith('/api/'):
        response.headers['Cache-Control'] = 'no-store'
    return response


class Login(BaseModel):
    password: str = Field(max_length=200)


@app.post('/api/login')
def login(body: Login, request: Request):
    if not PASSWORD:
        raise HTTPException(503, 'Private studio password has not been configured.')
    client = request.client.host
    recent = [t for t in ATTEMPTS.get(client, []) if t > time.time() - 300]
    if len(recent) >= 10:
        raise HTTPException(429, 'Please wait five minutes before trying again.')
    ATTEMPTS[client] = recent + [time.time()]
    if not hmac.compare_digest(body.password.encode(), PASSWORD.encode()):
        raise HTTPException(401, 'Password incorrect.')
    token = secrets.token_urlsafe(32)
    SESSIONS[token] = time.time() + 86400
    response = JSONResponse({'ok': True})
    response.set_cookie(COOKIE, token, httponly=True, samesite='strict',
                        secure=request.url.scheme == 'https' or bool(os.environ.get('RENDER')), max_age=86400)
    return response


@app.get('/api/session')
def session(request: Request):
    return {'authenticated': SESSIONS.get(request.cookies.get(COOKIE, ''), 0) > time.time()}


class NewJob(BaseModel):
    title: str = Field(default='TV story', max_length=70)
    script: str = Field(default='', max_length=24000)
    quality: str = Field(default='4k', pattern='^(4k|1080p|preview)$')
    grade: str = Field(default='documentary', pattern='^(documentary|neutral|warm)$')
    motion: bool = True
    masking: bool = True
    graphics: bool = True
    captions: bool = True
    sfx: bool = True
    transitions: bool = True
    images: int = Field(default=0, ge=0, le=12)


@app.post('/api/jobs')
def new_job(body: NewJob):
    if shutil.disk_usage(DATA).free < 4 * 1024**3:
        raise HTTPException(507, 'Storage is full. Delete an older project first.')
    identifier = secrets.token_hex(16)
    directory = DATA / identifier
    directory.mkdir()
    job = dict(id=identifier, status='uploading', progress=0, message='Uploading media',
               created=time.time(), settings=body.model_dump())
    write(directory / 'job.json', job)
    return job


@app.put('/api/jobs/{identifier}/upload/{kind}')
async def upload(identifier: str, kind: str, request: Request, offset: int = 0):
    directory = job_dir(identifier)
    job = read_job(identifier)
    if job['status'] != 'uploading':
        raise HTTPException(409, 'Upload already completed.')
    allowed = ['voice', 'video'] + [f'image-{i}' for i in range(job['settings']['images'])]
    if kind not in allowed:
        raise HTTPException(400, 'Unsupported media slot.')
    target = directory / kind
    if offset != (target.stat().st_size if target.exists() else 0):
        raise HTTPException(409, 'Upload offset does not match; start a new project.')
    limit = 100 * 1024**2 if kind != 'video' else MAX_BYTES
    count = 0
    with target.open('ab') as output:
        async for chunk in request.stream():
            count += len(chunk)
            if count > 8 * 1024**2 or offset + count > limit:
                output.truncate(offset)
                raise HTTPException(413, 'Upload exceeds the media size limit.')
            output.write(chunk)
    return {'offset': offset + count}


def execute(identifier, mode):
    directory = job_dir(identifier)
    with LOCK:
        job = read_job(identifier)
        if job['status'] == 'cancelled':
            return
        with (directory / 'worker.log').open('a') as log:
            process = subprocess.Popen([sys.executable, str(ROOT / 'engine.py'), mode, str(directory)],
                                       stdout=log, stderr=log, start_new_session=True)
            ACTIVE[identifier] = process
            result = process.wait()
            ACTIVE.pop(identifier, None)
        job = read_job(identifier)
        if result and job['status'] != 'cancelled':
            job.update(status='failed', message='Processing stopped. Open the job log for details.')
            write(directory / 'job.json', job)


@app.post('/api/jobs/{identifier}/start')
def start(identifier: str):
    directory = job_dir(identifier)
    job = read_job(identifier)
    if job['status'] not in {'uploading', 'failed', 'interrupted'}:
        raise HTTPException(409, 'Job is already started.')
    try:
        voice = probe(directory / 'voice')
        video = probe(directory / 'video')
        if not voice['audio'] or not video['width']:
            raise ValueError('Upload a valid voiceover and video.')
        if not 1 <= voice['duration'] <= 600 or not 1 <= video['duration'] <= 3600:
            raise ValueError('Use a voiceover of up to 10 minutes and video of up to one hour.')
        from PIL import Image
        for i in range(job['settings']['images']):
            with Image.open(directory / f'image-{i}') as img:
                img.verify()
    except Exception as error:
        raise HTTPException(400, str(error))
    job.update(status='queued', message='Waiting for the processor', source=video, voice=voice)
    write(directory / 'job.json', job)
    threading.Thread(target=execute, args=(identifier, 'all'), daemon=True).start()
    return {'ok': True}


@app.get('/api/jobs')
def jobs():
    return sorted([json.loads(p.read_text()) for p in DATA.glob('*/job.json')], key=lambda j: j['created'], reverse=True)


@app.get('/api/jobs/{identifier}')
def job(identifier: str):
    value = read_job(identifier)
    timeline = job_dir(identifier) / 'timeline.json'
    if timeline.exists():
        value['timeline'] = json.loads(timeline.read_text())
    return value


class Edit(BaseModel):
    index: int = Field(ge=0)
    asset: str = 'video'
    source_time: float = Field(ge=0)
    text: str = Field(max_length=1000)
    approved: bool = False


@app.put('/api/jobs/{identifier}/shot')
def edit(identifier: str, body: Edit):
    directory = job_dir(identifier)
    job = read_job(identifier)
    if job['status'] not in {'ready', 'review'}:
        raise HTTPException(409, 'Wait for the current render to finish.')
    timeline = json.loads((directory / 'timeline.json').read_text())
    if body.index >= len(timeline): raise HTTPException(400)
    allowed = ['video'] + [f'image-{i}' for i in range(job['settings']['images'])]
    if body.asset not in allowed: raise HTTPException(400)
    shot = timeline[body.index]
    if body.asset == 'video' and body.source_time + shot['end'] - shot['start'] > job['source']['duration']:
        raise HTTPException(400, 'The selected clip extends past the source video.')
    if not body.text.strip(): raise HTTPException(400, 'Caption text cannot be empty.')
    if body.text != shot['text']:
        words = body.text.split()
        step = (shot['end'] - shot['start']) / len(words)
        shot['words'] = [dict(word=w, start=shot['start']+i*step, end=shot['start']+(i+1)*step) for i,w in enumerate(words)]
    shot.update(asset=body.asset, source_time=body.source_time, text=body.text, approved=body.approved)
    write(directory / 'timeline.json', timeline)
    job.update(dirty=True)
    write(directory / 'job.json', job)
    return {'ok': True}


@app.post('/api/jobs/{identifier}/render')
def rerender(identifier: str):
    job = read_job(identifier)
    if job['status'] not in {'ready', 'review'}: raise HTTPException(409)
    job.update(status='queued', message='Rendering your changes', dirty=False)
    write(job_dir(identifier) / 'job.json', job)
    threading.Thread(target=execute, args=(identifier, 'render'), daemon=True).start()
    return {'ok': True}


@app.post('/api/jobs/{identifier}/cancel')
def cancel(identifier: str):
    job = read_job(identifier)
    job.update(status='cancelled', message='Cancelled')
    write(job_dir(identifier) / 'job.json', job)
    if identifier in ACTIVE:
        try: os.killpg(ACTIVE[identifier].pid, signal.SIGTERM)
        except ProcessLookupError: pass
    return {'ok': True}


@app.delete('/api/jobs/{identifier}')
def delete(identifier: str):
    directory = job_dir(identifier)
    if read_job(identifier)['status'] in {'queued', 'processing', 'rendering'}:
        raise HTTPException(409, 'Cancel processing first.')
    if identifier in ACTIVE: raise HTTPException(409, 'Cancellation is finishing.')
    shutil.rmtree(directory)
    return {'ok': True}


@app.get('/api/jobs/{identifier}/file/{kind}')
def file(identifier: str, kind: str):
    names = {'output': 'final.mp4', 'source': 'video', 'captions': 'captions.srt',
             'timeline': 'timeline.json', 'log': 'worker.log'}
    if kind not in names: raise HTTPException(404)
    path = job_dir(identifier) / names[kind]
    if not path.exists(): raise HTTPException(404)
    if kind == 'output' and read_job(identifier)['status'] not in {'ready', 'review'}:
        raise HTTPException(409, 'Video is still rendering.')
    return FileResponse(path, media_type='video/mp4' if kind in {'output', 'source'} else None,
                        filename='SceneVault.mp4' if kind == 'output' else None)


@app.get('/health')
def health():
    return {'ok': True, 'configured': bool(PASSWORD)}


app.mount('/', StaticFiles(directory=ROOT / 'web', html=True), name='web')
