"""Local-model retrieval and real FFmpeg rendering. No paid inference API."""
import gc
import json
import math
import os
import re
import sys
import time
import wave
from pathlib import Path

os.environ.setdefault('OMP_NUM_THREADS', '2')
os.environ.setdefault('TOKENIZERS_PARALLELISM', 'false')
os.environ.setdefault('HF_HOME', str(Path(__file__).parent / 'models'))
sys.path.insert(0, str(Path(__file__).parent))
from common import command, ffmpeg, probe, write


def progress(directory, phase, percent, status='processing'):
    job = json.loads((directory / 'job.json').read_text())
    if job['status'] == 'cancelled':
        raise RuntimeError('Cancelled')
    job.update(status=status, message=phase, progress=percent)
    write(directory / 'job.json', job)
    print(f'{percent}% {phase}', flush=True)


def models():
    import torch
    from transformers import CLIPModel, CLIPProcessor
    from sentence_transformers import SentenceTransformer
    torch.set_num_threads(2)
    name = 'openai/clip-vit-base-patch32'
    return CLIPModel.from_pretrained(name).eval(), CLIPProcessor.from_pretrained(name), SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2', device='cpu')


def transcribe(path, prompt=''):
    from faster_whisper import WhisperModel
    model = WhisperModel('base.en', device='cpu', compute_type='int8', cpu_threads=2)
    segments, _ = model.transcribe(str(path), word_timestamps=True, vad_filter=True,
                                   initial_prompt=prompt[:1600] or None, beam_size=5)
    result = [{'start': s.start, 'end': s.end, 'text': s.text.strip(),
               'words': [{'start': w.start, 'end': w.end, 'word': w.word.strip()} for w in s.words]} for s in segments]
    del model
    gc.collect()
    return result


def beats(transcript, duration):
    words = [w for seg in transcript for w in seg['words'] if w['word']]
    if not words: raise ValueError('No speech was detected in the voiceover.')
    groups, group = [], []
    for word in words:
        group.append(word)
        length = word['end'] - group[0]['start']
        if length >= 4.8 or (length >= 2.8 and re.search(r'[.!?]$', word['word'])):
            groups.append(group)
            group = []
    if group: groups.append(group)
    result = []
    for i, group in enumerate(groups):
        start = 0 if i == 0 else group[0]['start']
        end = groups[i+1][0]['start'] if i+1 < len(groups) else duration
        result.append(dict(start=start, end=end, words=group, text=' '.join(w['word'] for w in group)))
    return result


def align_script(transcript, script):
    """Use supplied wording while keeping recognition-derived speech intervals."""
    import difflib
    words=[w for segment in transcript for w in segment['words']]
    supplied=script.split()
    if not supplied:return transcript
    normalize=lambda s:re.sub(r'[^a-z0-9]', '', s.lower())
    matcher=difflib.SequenceMatcher(None,[normalize(w['word']) for w in words],[normalize(w) for w in supplied],autojunk=False)
    if not words or matcher.ratio()<.55:
        raise ValueError('The supplied script differs too much from the recording. Use the exact spoken script or leave it blank.')
    result=[]
    for operation,a,b,c,d in matcher.get_opcodes():
        if operation=='equal':
            result.extend(dict(words[a+i],word=supplied[c+i]) for i in range(d-c))
        elif operation=='replace':
            start,end=words[a]['start'],words[b-1]['end']
            lengths=[max(1,len(w)) for w in supplied[c:d]]
            cursor=start
            for word,length in zip(supplied[c:d],lengths):
                finish=cursor+(end-start)*length/sum(lengths)
                result.append(dict(word=word,start=cursor,end=finish));cursor=finish
        elif operation=='insert':
            start=words[a-1]['end'] if a else 0
            end=words[a]['start'] if a<len(words) else words[-1]['end']
            step=max(0,end-start)/max(1,d-c)
            result.extend(dict(word=supplied[k],start=start+(k-c)*step,end=start+(k-c+1)*step) for k in range(c,d))
    return [dict(start=result[0]['start'],end=result[-1]['end'],text=script,words=result)]


def index(directory, job):
    from PIL import Image
    video = directory / 'video'
    frames_dir = directory / 'frames'
    frames_dir.mkdir(exist_ok=True)
    command([ffmpeg(), '-nostdin', '-y', '-v', 'error', '-threads', '2', '-i', str(video),
             '-vf', 'fps=1/2,scale=320:-2', '-q:v', '3', str(frames_dir / '%06d.jpg')])
    candidates = [dict(asset='video', time=i*2+1, frame=str(path)) for i, path in enumerate(sorted(frames_dir.glob('*.jpg')))]
    for i in range(job['settings']['images']):
        path = directory / f'image-{i}'
        with Image.open(path) as image:
            image.convert('RGB').thumbnail((640, 640))
        candidates.append(dict(asset=f'image-{i}', time=0, frame=str(path)))
    if not candidates: raise ValueError('The source video has no usable frames.')
    return candidates


def match(directory):
    import numpy as np
    from PIL import Image
    job = json.loads((directory / 'job.json').read_text())
    progress(directory, 'Transcribing your voiceover', 5)
    narration = transcribe(directory / 'voice', job['settings']['script'])
    narration = align_script(narration, job['settings']['script'])
    write(directory / 'narration.json', narration)
    timeline = beats(narration, job['voice']['duration'])
    progress(directory, 'Finding visual moments', 15)
    candidates = index(directory, job)
    progress(directory, 'Transcribing source dialogue for context', 25)
    source = transcribe(directory / 'video') if job['source']['audio'] else []
    write(directory / 'source-transcript.json', source)
    progress(directory, 'Comparing images and narration meaning', 35)
    import torch
    clip, processor, semantic = models()
    image_vectors = []
    with torch.inference_mode():
        for start in range(0, len(candidates), 12):
            images = []
            for candidate in candidates[start:start+12]:
                with Image.open(candidate['frame']) as im: images.append(im.convert('RGB'))
            vector = clip.get_image_features(**processor(images=images, return_tensors='pt'))
            vector = vector / vector.norm(dim=-1, keepdim=True)
            image_vectors.append(vector.cpu().numpy())
            if start % 120 == 0:
                progress(directory, 'Comparing images and narration meaning', 35 + int(10*start/len(candidates)))
        query = [t['text'] for t in timeline]
        text = clip.get_text_features(**processor(text=query, padding=True, truncation=True, return_tensors='pt'))
        text = text / text.norm(dim=-1, keepdim=True)
        visual = text.cpu().numpy() @ np.concatenate(image_vectors).T
    nearby = [' '.join(seg['text'] for seg in source if seg['start']-6 <= c['time'] <= seg['end']+6)
              if c['asset'] == 'video' else '' for c in candidates]
    sem_query = semantic.encode(query, normalize_embeddings=True)
    sem_source = semantic.encode(nearby, normalize_embeddings=True, batch_size=32)
    linguistic = sem_query @ sem_source.T
    linguistic[:, [i for i, s in enumerate(nearby) if not s]] = 0
    combined = .6 * visual + .4 * linguistic
    selected = []
    for i, shot in enumerate(timeline):
        duration = shot['end'] - shot['start']
        order = np.argsort(combined[i])[::-1]
        alternatives = []
        for k in order:
            candidate = candidates[int(k)]
            if candidate['asset'] == 'video' and duration > job['source']['duration']: continue
            start = max(0, min(candidate['time']-duration/2, job['source']['duration']-duration)) if candidate['asset'] == 'video' else 0
            if any(a['asset'] == candidate['asset'] and abs(a['source_time']-start)<5 for a in alternatives): continue
            alternatives.append(dict(asset=candidate['asset'], source_time=round(start, 3),
                                     similarity=round(float(combined[i,k]), 3),
                                     visual=round(float(visual[i,k]), 3), dialogue=round(float(linguistic[i,k]), 3)))
            if len(alternatives) >= 5: break
        if not alternatives: raise ValueError('Source video is too short for this narration segment.')
        best = next((a for a in alternatives if not any(a['asset']==old['asset'] and abs(a['source_time']-old['source_time'])<4 for old in selected[-3:])), alternatives[0])
        shot.update(best, alternatives=alternatives, approved=False,
                    review_reason='AI selection — check identity and context. Similarity is not an accuracy percentage.')
        selected.append(best)
    write(directory / 'timeline.json', timeline)
    progress(directory, 'Scene matching complete', 52)


def ass_escape(text):
    return str(text).replace('\\', '').replace('{', '').replace('}', '').replace('\n', ' ')


def make_captions(directory, timeline, settings, width, height):
    def timestamp(t):
        cs = round(t*100)
        return f'{cs//360000}:{cs//6000%60:02}:{cs//100%60:02}.{cs%100:02}'
    head = f'''[Script Info]
ScriptType: v4.00+
PlayResX: {width}
PlayResY: {height}
WrapStyle: 0
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Caption,DejaVu Sans,{width*.057:.0f},&H00FFFFFF,&H0034E8FF,&H00120F0B,&H80000000,-1,0,0,0,100,100,0,0,1,{width*.003:.0f},1,5,50,50,0,1
Style: Title,DejaVu Sans,{width*.045:.0f},&H0034E8FF,&H0034E8FF,&H00120F0B,&H80000000,-1,0,0,0,100,100,0,0,1,0,0,5,80,80,0,1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
'''
    events, srt = [], []
    def event(a,b,style,text):
        events.append(f'Dialogue: 0,{timestamp(a)},{timestamp(b)},{style},,0,0,0,,{text}')
    for shot in timeline:
        words = shot['words']
        for start in range(0,len(words),5):
            group=words[start:start+5]
            a,b=group[0]['start'],group[-1]['end']
            srt.append(f"{len(srt)+1}\n0{timestamp(a).replace('.', ',')}0 --> 0{timestamp(b).replace('.', ',')}0\n"+' '.join(w['word'] for w in group)+'\n')
            if settings['captions']:
                for j,w in enumerate(group):
                    next_chunk_start=words[start+len(group)]['start'] if start+len(group)<len(words) else shot['end']
                    end=group[j+1]['start'] if j+1<len(group) else min(shot['end'],next_chunk_start,w['end']+.15)
                    if end <= w['start']: continue
                    text=' '.join((r'{\c&H0034E8FF&}'+ass_escape(x['word'])+r'{\c&H00FFFFFF&}') if j==k else ass_escape(x['word']) for k,x in enumerate(group))
                    event(w['start'],end,'Caption',f'{{\\pos({width//2},{int(height*.75)})}}'+text)
        if settings['graphics']:
            title=ass_escape(settings['title'])
            event(shot['start'],shot['end'],'Title',f'{{\\pos({width//2},{int(height*.16)})\\fad(120,100)}}'+title)
            # Every fourth shot gets a short, animated quote from the actual narration.
            if timeline.index(shot)%4==0:
                label=ass_escape(' '.join(w['word'] for w in words[:5])).upper()
                event(shot['start'],min(shot['end'],shot['start']+2),'Title',f'{{\\pos({width//2},{int(height*.22)})\\fs{int(width*.028)}\\fscx94\\fscy94\\t(0,250,\\fscx100\\fscy100)\\fad(120,150)}}'+label)
    (directory/'captions.ass').write_text(head+'\n'.join(events))
    (directory/'captions.srt').write_text('\n'.join(srt))


def face_center(path):
    import cv2
    image=cv2.imread(str(path))
    if image is None:return .5,.5
    detector=cv2.CascadeClassifier(cv2.data.haarcascades+'haarcascade_frontalface_default.xml')
    faces=detector.detectMultiScale(cv2.cvtColor(image,cv2.COLOR_BGR2GRAY),1.1,5,minSize=(30,30))
    if len(faces)!=1:return .5,.5
    x,y,w,h=faces[0]
    return (x+w/2)/image.shape[1],(y+h/2)/image.shape[0]


def render(directory):
    import numpy as np
    from PIL import Image,ImageDraw
    job=json.loads((directory/'job.json').read_text())
    timeline=json.loads((directory/'timeline.json').read_text())
    settings=job['settings']
    width,height={'4k':(2160,3840),'1080p':(1080,1920),'preview':(360,640)}[settings['quality']]
    make_captions(directory,timeline,settings,width,height)
    clips=[]
    for i,shot in enumerate(timeline):
        progress(directory,f'Rendering shot {i+1} of {len(timeline)}',55+int(30*i/len(timeline)),'rendering')
        source=directory/shot['asset']
        frames=max(1,round(shot['end']*24)-round(shot['start']*24))
        length=frames/24
        is_image=shot['asset']!='video'
        if is_image:
            with Image.open(source) as image: sw,sh=image.size
        else: sw,sh=job['source']['width'],job['source']['height']
        fw=width
        fh=round(width*sh/sw/2)*2
        if fh>height*.48:
            fh=int(height*.48)//2*2
            fw=round(fh*sw/sh/2)*2
        x=(width-fw)//2
        y=int(height*.34)
        # A real rounded alpha mask separates the footage panel from the dark backdrop.
        mask=Image.new('L',(fw,fh),0)
        ImageDraw.Draw(mask).rounded_rectangle((0,0,fw-1,fh-1),radius=int(width*.015) if settings['masking'] else 0,fill=255)
        mask_path=directory/'mask.png';mask.save(mask_path)
        thumb=directory/'shot.jpg'
        inputs=['-loop','1','-i',str(source)] if is_image else ['-ss',str(shot['source_time']),'-i',str(source)]
        command([ffmpeg(),'-nostdin','-y','-v','error',*inputs,'-frames:v','1','-vf','scale=480:-2',str(thumb)])
        cx,cy=face_center(thumb)
        if settings['motion']:
            zoom=f"zoompan=z='1+0.035*on/{frames}':x='max(0,min(iw-iw/zoom,iw*{cx}-iw/zoom/2))':y='max(0,min(ih-ih/zoom,ih*{cy}-ih/zoom/2))':d=1:s={fw}x{fh}:fps=24"
        else:zoom=f'scale={fw}:{fh},fps=24'
        grade={'neutral':'null','documentary':'eq=contrast=1.035:saturation=1.015:gamma=0.99','warm':'colorbalance=rs=.025:bs=-.02,eq=saturation=1.025'}[settings['grade']]
        filters=(f'[0:v]fps=24,split[bg][fg];[bg]scale=90:160:force_original_aspect_ratio=increase,crop=90:160,boxblur=5:2,scale={width}:{height},eq=brightness=-.17:saturation=.45,drawbox=color=0x080d15@.65:t=fill[base];'
                 f'[fg]{zoom},{grade},setsar=1,format=rgba[panel];[1:v]format=gray[mask];[panel][mask]alphamerge[rounded];[base][rounded]overlay={x}:{y}:shortest=1,setsar=1')
        if settings['transitions'] and i>0:filters+=',fade=t=in:st=0:d=0.10'
        clip=directory/f'part-{i:04}.mp4'
        command([ffmpeg(),'-nostdin','-y','-v','error','-threads','2',*inputs,'-loop','1','-i',str(mask_path),
                 '-filter_complex_threads','1','-filter_complex',filters,'-frames:v',str(frames),'-an',
                 '-c:v','libx264','-preset','veryfast','-crf','19','-threads','2','-pix_fmt','yuv420p',str(clip)])
        if abs(probe(clip)['duration']-length)>.1:raise RuntimeError(f'Shot {i+1} did not render completely.')
        clips.append(clip)
    listing=directory/'concat.txt'
    listing.write_text(''.join(f"file '{path.name}'\n" for path in clips))
    command([ffmpeg(),'-nostdin','-y','-v','error','-f','concat','-safe','0','-i',str(listing),'-c','copy',str(directory/'sequence.mp4')])
    duration=job['voice']['duration']
    sample_rate=44100
    audio=np.zeros(math.ceil(duration*sample_rate),dtype=np.float32)
    if settings['sfx']:
        rng=np.random.default_rng(42)
        for shot in timeline[4::4]:
            n=int(.22*sample_rate);t=np.arange(n)/sample_rate
            noise=np.convolve(rng.normal(0,1,n),np.ones(16)/16,mode='same')
            sound=(.022*noise+.012*np.sin(2*np.pi*(100*t-80*t*t)))*np.sin(np.pi*np.arange(n)/n)**2
            start=int(shot['start']*sample_rate);available=min(n,len(audio)-start)
            audio[start:start+available]+=sound[:available]
    with wave.open(str(directory/'sfx.wav'),'wb') as file:
        file.setnchannels(1);file.setsampwidth(2);file.setframerate(sample_rate)
        file.writeframes((audio*32767).astype('<i2').tobytes())
    progress(directory,'Adding timed captions, graphics and sound',90,'rendering')
    ass=str(directory/'captions.ass')
    fontdir=str(Path(__file__).parent/'fonts')
    command([ffmpeg(),'-nostdin','-y','-v','error','-threads','2','-i',str(directory/'sequence.mp4'),'-i',str(directory/'voice'),
             '-i',str(directory/'sfx.wav'),'-filter_complex_threads','1','-filter_complex',
             f'[0:v]ass={ass}:fontsdir={fontdir}[v];[1:a][2:a]amix=inputs=2:duration=first:normalize=0,alimiter=limit=.95:level=0[a]',
             '-map','[v]','-map','[a]','-t',str(duration),'-c:v','libx264','-preset','veryfast','-crf','18','-threads','2',
             '-c:a','aac','-b:a','192k','-pix_fmt','yuv420p','-movflags','+faststart',str(directory/'final.mp4')])
    if abs(probe(directory/'final.mp4')['duration']-duration)>.12:raise RuntimeError('Output duration does not match the voiceover.')
    for path in clips:path.unlink(missing_ok=True)
    (directory/'sequence.mp4').unlink(missing_ok=True)
    progress(directory,'Video ready. Review the selected scenes before publishing.',100,'review')


if __name__=='__main__':
    mode=sys.argv[1]
    if mode=='warmup':
        models()
        from faster_whisper import WhisperModel
        WhisperModel('base.en',device='cpu',compute_type='int8')
        print('Models cached.')
    else:
        directory=Path(sys.argv[2]).resolve()
        try:
            if mode == 'all':
                import subprocess
                for stage in ['match', 'render']:
                    subprocess.run([sys.executable, __file__, stage, str(directory)], check=True)
            elif mode == 'match':match(directory)
            elif mode == 'render':render(directory)
        except Exception:
            import traceback
            traceback.print_exc()
            raise
