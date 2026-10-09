"""Generate original numbered cards and a synthetic metronome; no third-party media."""
from pathlib import Path
import math, struct, wave
from PIL import Image, ImageDraw, ImageFont

def generate(folder):
    folder=Path(folder);folder.mkdir(exist_ok=True)
    font=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',100)
    for i in range(8):
        path=folder/f'{i+1}.png'
        if path.exists():continue
        im=Image.new('RGB',(640,400),['#ef798a','#67b7dc','#a492ea','#83c59c'][i%4]);d=ImageDraw.Draw(im)
        d.ellipse((150,30,490,370),fill='white');d.text((320,200),str(i+1),font=font,fill='black',anchor='mm');im.save(path)
    audio=folder/'120-bpm.wav'
    if not audio.exists():
        with wave.open(str(audio),'wb') as w:
            w.setparams((1,2,44100,0,'NONE','not compressed'))
            second=b''.join(struct.pack('<h',int(10000*math.sin(2*math.pi*880*n/44100)*max(0,1-(n%22050)/1800))) for n in range(44100))
            for _ in range(44):w.writeframesraw(second)

if __name__=='__main__':generate(Path(__file__).resolve().parent/'demo')
