import base64, io, json, math, os, shutil, subprocess, sys, threading, uuid, webbrowser
import re
from pathlib import Path
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parent
import imageio_ffmpeg
import design
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
DATA = ROOT / 'data'
DATA.mkdir(exist_ok=True)
JOBS = {}
LOCK = threading.Lock()
LEVELS = ['Easy', 'Normal', 'Hard', 'Expert', 'Insane']

def font(size):
    return ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf', size)

def card(image_path, word, level, section):
    im = Image.new('RGB', (1920,1080), '#101529')
    d = ImageDraw.Draw(im)
    d.text((100,65), 'SAY THE WORD ON BEAT', font=font(42), fill='#a4b3d3')
    d.text((100,140), level.upper(), font=font(72), fill='#77f2c5')
    d.text((1670,155), f'{section+1} / 8', font=font(48), fill='white')
    picture = ImageOps.contain(Image.open(image_path).convert('RGB'), (1100,570))
    im.paste(picture, ((1920-picture.width)//2, 270+(570-picture.height)//2))
    size = 110
    while size > 20 and d.textbbox((0,0),word,font=font(size))[2] > 1720:
        size -= 2
    d.text((960,925), word, font=font(size), fill='white', anchor='mm')
    for n in range(8):
        x = 100+n*217
        d.rounded_rectangle((x,1020,x+195,1033),radius=6,fill='#77f2c5' if n<=section else '#303951')
    return im

def number(value, lo, hi):
    value=float(value)
    if not math.isfinite(value) or not lo<=value<=hi:
        raise ValueError(f'Число должно быть от {lo} до {hi}')
    return value

def make_tile(path, word):
    im=Image.new('RGB',(330,350),'white')
    pic=ImageOps.contain(Image.open(path).convert('RGBA'),(302,270))
    im.paste(pic,((330-pic.width)//2,12+(270-pic.height)//2),pic)
    d=ImageDraw.Draw(im); size=42
    while size>12 and d.textbbox((0,0),word,font=font(size))[2]>304: size-=1
    d.text((165,312),word,font=font(size),fill='#161616',anchor='mm')
    d.rectangle((3,3,326,346),outline='#171717',width=7)
    return im

def scene(job,t):
    return next((f for f in job['frames'] if f['start']<=t<f['end']),job['frames'][-1])

def animated_core(job,t,assets):
    f=scene(job,t); im=assets['background'].copy()
    if job.get('decor',False):design.decorate(im,assets['stickers'],t)
    d=ImageDraw.Draw(im);colors=job.get('colors',design.PALETTES['paper']);ink=colors['ink'];accent=colors['accent']
    elapsed=max(0,t-f['start']); pulse=math.exp(-elapsed*12)
    if f['kind'] in ('countdown','title'):
        d.rounded_rectangle((300,170,1620,900),radius=65,fill=colors['background'])
        d.text((960,280),'SAY THE WORD ON BEAT',font=font(64),fill=ink,anchor='mm')
        text=str(f['number']) if f['kind']=='countdown' else f['level'].upper()
        size=round((240 if f['kind']=='countdown' else 140)*(1+.1*pulse))
        d.text((960,550),text,font=font(size),fill=accent,anchor='mm')
        d.text((960,800),'GET READY' if f['kind']=='countdown' else 'SAY IT ON THE BEAT',font=font(45),fill=ink,anchor='mm')
        return im
    d.text((960,105),f['level'].upper(),font=font(68),fill=ink,anchor='mm')
    d.text((960,185),'WATCH' if f['kind']=='reveal' else 'YOUR TURN',font=font(34),fill=colors['muted'],anchor='mm')
    for i,tile in enumerate(assets['tiles']):
        if f['kind']=='reveal' and i>f['index']:continue
        active=i==f['index']; scale=1+0.055*pulse if active else 1
        if f['kind']=='reveal' and active:scale*=1-.16*pulse
        w,h=round(330*scale),round(350*scale)
        x=270+(i%4)*350+(330-w)//2; y=270+(i//4)*380+(350-h)//2
        im.paste(tile.resize((w,h),Image.Resampling.BILINEAR),(x,y))
        if f['kind']=='play' and i<=f['index']:
            ImageDraw.Draw(im).rectangle((x,y,x+w-1,y+h-1),outline=accent,width=10)
    return im

def animated_frame(job,t,assets):
    current=animated_core(job,t,assets);f=scene(job,t)
    if job.get('transition')=='fade' and f['start']>0:
        previous=scene(job,max(0,f['start']-1/30))
        length=min(.25,(f['end']-f['start'])/2)
        if f['kind']!=previous['kind'] and t-f['start']<length:
            amount=max(0,(t-f['start'])/length);amount=amount*amount*(3-2*amount)
            return Image.blend(animated_core(job,f['start']-1/30,assets),current,amount)
    return current

def read_assets(folder,job):
    assets={'background':Image.open(folder/'background.png').convert('RGB'),'tiles':[Image.open(folder/f'tile{i}.png').convert('RGB') for i in range(8)]}
    if job.get('decor'):assets['stickers']=[Image.open(folder/f'sticker{i}.png').convert('RGBA') for i in range(2)]
    return assets

def prepare(payload):
    bpm=number(payload['bpm'],30,300)
    offset=number(payload.get('offset',0),0,36000)
    items=payload['items']
    if len(items)!=8: raise ValueError('Нужно ровно 8 карточек')
    beats=[number(x,0.25,32) for x in payload['beats']]
    if len(beats)!=5: raise ValueError('Нужно 5 значений длительности')
    ident=uuid.uuid4().hex
    folder=DATA/ident
    folder.mkdir()
    audio=base64.b64decode(payload['audio'],validate=True)
    if not audio: raise ValueError('Выберите аудио')
    (folder/'audio').write_bytes(audio)
    frames=[]
    time=0
    count=5 if payload.get('full') else 1
    for i,item in enumerate(items):
        raw=base64.b64decode(item['image'],validate=True)
        with Image.open(io.BytesIO(raw)) as picture:
            picture=ImageOps.exif_transpose(picture)
            picture.thumbnail((1920,1080))
            picture.convert('RGBA').save(folder/f'input{i}.png')
    style=payload.get('style','grid')
    if style=='grid':
        theme=payload.get('theme','paper')
        if theme not in design.PALETTES:raise ValueError('Неизвестное оформление')
        colors=dict(design.PALETTES[theme]);accent=payload.get('accent',colors['accent'])
        if not re.fullmatch(r'#[0-9a-fA-F]{6}',accent):raise ValueError('Некорректный цвет подсветки')
        colors['accent']=accent
        bg=design.background(theme)
        if payload.get('background'):
            bg=ImageOps.fit(Image.open(io.BytesIO(base64.b64decode(payload['background'],validate=True))).convert('RGB'),(1920,1080))
        bg.save(folder/'background.png')
        stickers=payload.get('stickers',[None,None])
        if len(stickers)!=2:raise ValueError('Нужно два поля стикеров')
        for i,raw in enumerate(stickers):
            pic=design.sticker(i,theme)
            if raw:
                pic=ImageOps.exif_transpose(Image.open(io.BytesIO(base64.b64decode(raw,validate=True)))).convert('RGBA')
                pic=ImageOps.contain(pic,(180,180));canvas=Image.new('RGBA',(180,180));canvas.alpha_composite(pic,((180-pic.width)//2,(180-pic.height)//2));pic=canvas
            pic.save(folder/f'sticker{i}.png')
        for i,item in enumerate(items):
            word=str(item['word']).strip()[:80]
            if not word:raise ValueError('Заполните все слова')
            make_tile(folder/f'input{i}.png',word).save(folder/f'tile{i}.png')
        def event(duration,**kwargs):
            nonlocal time
            end=time+duration
            frames.append(dict(start=round(time*30)/30,end=round(end*30)/30,**kwargs))
            time=end
        for n in [3,2,1]:event(60/bpm,kind='countdown',number=n)
        for level in range(count):
            event(2*60/bpm,kind='title',level=LEVELS[level])
            for kind in ['reveal','play']:
                for i in range(8):event(beats[level]*60/bpm,kind=kind,index=i,level=LEVELS[level])
        job={'id':ident,'style':'grid','frames':frames,'duration':frames[-1]['end'],'offset':offset,'status':'ready','progress':0}
        job.update(colors=colors,decor=bool(payload.get('decor',True)),transition=payload.get('transition','fade'))
        JOBS[ident]=job
        (folder/'job.json').write_text(json.dumps(job),encoding='utf-8')
        return job
    for level in range(count):
        for section,item in enumerate(items):
            word=str(item['word']).strip()[:80]
            if not word: raise ValueError('Заполните все слова')
            name=f'frame{len(frames):02}.png'
            card(folder/f'input{section}.png',word,LEVELS[level],section).save(folder/name)
            # Round cumulative boundaries to frames to prevent timing drift.
            end=time+beats[level]*60/bpm
            frames.append({'file':name,'start':round(time*30)/30,'end':round(end*30)/30,'level':LEVELS[level]})
            time=end
    job={'id':ident,'frames':frames,'duration':frames[-1]['end'],'offset':offset,'status':'ready','progress':0}
    JOBS[ident]=job
    (folder/'settings.json').write_text(json.dumps({k:v for k,v in payload.items() if k not in ('audio','items')},ensure_ascii=False),encoding='utf-8')
    return job

def render(job):
    folder=DATA/job['id']
    try:
        if job.get('style')=='grid':
            assets=read_assets(folder,job)
            command=[FFMPEG,'-y','-f','rawvideo','-pix_fmt','rgb24','-s','1920x1080','-r','30','-i','pipe:0','-ss',str(job['offset']),'-i',str(folder/'audio'),'-map','0:v:0','-map','1:a:0','-af','apad','-t',str(job['duration']),'-c:v','libx264','-preset','veryfast','-crf','20','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-movflags','+faststart',str(folder/'video.mp4')]
            with (folder/'render.log').open('w',encoding='utf-8') as log:
                p=subprocess.Popen(command,stdin=subprocess.PIPE,stderr=log,stdout=subprocess.DEVNULL,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
                try:
                    total=round(job['duration']*30)
                    for n in range(total):
                        p.stdin.write(animated_frame(job,n/30,assets).tobytes())
                        job['progress']=min(99,round(n/total*100))
                    p.stdin.close()
                    if p.wait()!=0:raise RuntimeError('Ошибка FFmpeg. См. render.log')
                finally:
                    if p.poll() is None:p.kill();p.wait()
            job.update(status='done',progress=100)
            return
        lines=[]
        for f in job['frames']:
            lines.extend([f"file '{f['file']}'",'option framerate 30',f"duration {f['end']-f['start']:.9f}"])
        lines.append(f"file '{job['frames'][-1]['file']}'")
        lines.append('option framerate 30')
        (folder/'frames.txt').write_text('\n'.join(lines),encoding='utf-8')
        command=[FFMPEG,'-y','-f','concat','-safe','0','-i',str(folder/'frames.txt'),'-ss',str(job['offset']),'-i',str(folder/'audio'),'-map','0:v:0','-map','1:a:0','-af','apad','-t',str(job['duration']),'-r','30','-c:v','libx264','-preset','veryfast','-crf','20','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-movflags','+faststart','-progress','pipe:1',str(folder/'video.mp4')]
        with (folder/'render.log').open('w',encoding='utf-8') as log:
            p=subprocess.Popen(command,stdout=subprocess.PIPE,stderr=log,text=True,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            for line in p.stdout:
                if line.startswith('out_time_us='):
                    try: job['progress']=min(99,round(int(line.split('=')[1])/1e6/job['duration']*100))
                    except ValueError: pass
            if p.wait()!=0: raise RuntimeError('FFmpeg не смог прочитать медиа. Подробности: data/'+job['id']+'/render.log')
        job.update(status='done',progress=100)
    except Exception as e: job.update(status='error',error=str(e))

class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args): pass
    def reply(self,obj,status=200):
        data=json.dumps(obj,ensure_ascii=False).encode()
        self.send_response(status); self.send_header('Content-Type','application/json; charset=utf-8'); self.send_header('Content-Length',str(len(data))); self.end_headers(); self.wfile.write(data)
    def do_POST(self):
        try:
            if self.headers.get('Origin') not in (None,'http://127.0.0.1:8766','http://localhost:8766'): raise ValueError('Недопустимый источник запроса')
            length=int(self.headers.get('Content-Length',0))
            if not 0<length<150*1024*1024: raise ValueError('Общий размер загрузки должен быть меньше 110 МБ')
            payload=json.loads(self.rfile.read(length))
            if self.path=='/api/prepare': self.reply(prepare(payload))
            elif self.path=='/api/render':
                job=JOBS[payload['id']]
                with LOCK:
                    if any(j['status']=='rendering' for j in JOBS.values()): raise ValueError('Дождитесь текущего экспорта')
                    job['status']='rendering'
                threading.Thread(target=render,args=(job,),daemon=True).start()
                self.reply(job)
            else: self.reply({'error':'Not found'},404)
        except Exception as e: self.reply({'error':str(e)},400)
    def do_GET(self):
        if self.path=='/api/version':return self.reply({'version':'design-3'})
        if self.path.startswith('/api/job/'):
            return self.reply(JOBS.get(self.path.split('/')[-1],{'error':'Проект не найден'}))
        path=self.path.split('?')[0]
        target=(ROOT/('web/index.html' if path=='/' else path.lstrip('/'))).resolve()
        allowed=(ROOT/'web').resolve() in target.parents or DATA.resolve() in target.parents or (ROOT/'demo').resolve() in target.parents
        if not allowed or not target.is_file(): self.send_error(404); return
        mime={'.html':'text/html; charset=utf-8','.png':'image/png','.mp4':'video/mp4','.wav':'audio/wav'}.get(target.suffix,'application/octet-stream')
        self.send_response(200); self.send_header('Content-Type',mime); self.send_header('Content-Length',str(target.stat().st_size))
        if target.suffix=='.mp4': self.send_header('Content-Disposition','attachment; filename="say-the-word.mp4"')
        self.end_headers()
        with target.open('rb') as f: shutil.copyfileobj(f,self.wfile)

if __name__=='__main__':
    from generate_demo import generate
    generate(ROOT / 'demo')
    try:
        server=ThreadingHTTPServer(('127.0.0.1',8766),Handler)
    except OSError:
        print('Port 8766 is in use. Close the other generator window, or open http://127.0.0.1:8766 if it is already running.')
        sys.exit(1)
    print('Say the Word: http://127.0.0.1:8766',flush=True)
    if '--no-browser' not in sys.argv: webbrowser.open('http://127.0.0.1:8766')
    server.serve_forever()
