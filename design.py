"""Shared artwork and motion settings for preview and video export."""
import math, random
from PIL import Image, ImageDraw, ImageFilter

PALETTES={
 'paper':{'background':'#f3eee5','ink':'#252531','muted':'#666474','accent':'#32dc74'},
 'night':{'background':'#14172d','ink':'#f9f5ff','muted':'#bdc4dc','accent':'#ab83ff'},
 'candy':{'background':'#fff0f5','ink':'#443048','muted':'#896879','accent':'#f06aac'},
}

def background(theme):
    colors=PALETTES[theme]; im=Image.new('RGB',(1920,1080),colors['background']); d=ImageDraw.Draw(im)
    rng=random.Random(42)
    if theme=='paper':
        for _ in range(65):
            x=rng.randrange(1920);y=rng.randrange(1080);w=rng.randrange(60,450)
            d.line((x,y,x+w,y+rng.randrange(-180,180)),fill=rng.choice(['#e5dfd5','#faf7f0','#ece6dc']),width=rng.randrange(1,4))
        for x,y,r in [(65,80,190),(1780,930,240),(1900,180,130)]:d.ellipse((x-r,y-r,x+r,y+r),outline='#ded7ca',width=3)
    elif theme=='night':
        glow=Image.new('RGB',im.size,colors['background']);g=ImageDraw.Draw(glow)
        g.ellipse((-250,-350,1050,600),fill='#403266');g.ellipse((1250,600,2200,1500),fill='#164e59')
        im=glow.filter(ImageFilter.GaussianBlur(180));d=ImageDraw.Draw(im)
        for _ in range(130):
            x=rng.randrange(1920);y=rng.randrange(1080);r=rng.choice([1,1,2]);d.ellipse((x-r,y-r,x+r,y+r),fill='#8686ac')
    else:
        for box,color in [((-200,-250,600,480),'#e2d4fb'),((1370,650,2100,1320),'#ffd8a9'),((1550,-80,2070,460),'#c9f0e3')]:d.ellipse(box,fill=color)
        for x in range(35,1920,45):
            for y in range(30,1080,45):d.ellipse((x,y,x+3,y+3),fill='#e8cdd9')
    # A quiet backing keeps the headings legible over all presets.
    d=ImageDraw.Draw(im);d.rounded_rectangle((475,32,1445,225),radius=70,fill=colors['background'])
    return im

def sticker(index,theme):
    im=Image.new('RGBA',(180,180));d=ImageDraw.Draw(im);accent=PALETTES[theme]['accent']
    if index==0:
        points=[]
        for i in range(10):
            a=-math.pi/2+i*math.pi/5;r=76 if i%2==0 else 36
            points.append((90+math.cos(a)*r,90+math.sin(a)*r))
        d.polygon(points,fill='#ffe181',outline='#252531',width=4)
        d.ellipse((60,65,71,83),fill='#252531');d.ellipse((105,65,116,83),fill='#252531');d.arc((67,78,112,109),0,180,fill='#252531',width=4)
    else:
        d.ellipse((14,14,166,166),fill=accent,outline='#252531',width=4)
        d.line((52,99,75,120,129,59),fill='white',width=14)
    return im

def decorate(im,stickers,t):
    for n,(x,y) in enumerate([(30,65),(1740,70),(28,445),(1742,450),(30,835),(1740,840)]):
        pic=stickers[n%2]
        angle=4*math.sin(t*2.4+n)
        tile=pic.rotate(angle,resample=Image.Resampling.BICUBIC,expand=False)
        im.paste(tile,(x,y+round(7*math.sin(t*2+n))),tile)
    return im
