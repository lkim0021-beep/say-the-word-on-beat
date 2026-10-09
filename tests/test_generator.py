import base64
import subprocess
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageChops
import app
from generate_demo import generate


class GeneratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory()
        cls.root=Path(cls.temp.name)
        cls.old_data=app.DATA
        app.DATA=cls.root/'jobs';app.DATA.mkdir()
        cls.demo=cls.root/'demo';generate(cls.demo)
        cls.payload={
            'audio':base64.b64encode((cls.demo/'120-bpm.wav').read_bytes()).decode(),
            'items':[{'word':str(i+1),'image':base64.b64encode((cls.demo/f'{i+1}.png').read_bytes()).decode()} for i in range(8)],
            'bpm':120,'offset':0,'beats':[1,1,.75,.5,.5],
            'style':'grid','full':False,'theme':'night','decor':True,'transition':'fade',
        }

    @classmethod
    def tearDownClass(cls):
        app.DATA=cls.old_data
        cls.temp.cleanup()

    def test_timeline_and_frames(self):
        job=app.prepare(dict(self.payload,full=True))
        self.assertEqual(job['duration'],36.5)
        self.assertEqual(len(job['frames']),88)
        for a,b in zip(job['frames'],job['frames'][1:]):self.assertEqual(a['end'],b['start'])
        assets=app.read_assets(app.DATA/job['id'],job)
        self.assertIsNotNone(ImageChops.difference(app.animated_frame(job,7.6,assets),app.animated_frame(job,7.7,assets)).getbbox())
        self.assertEqual(app.animated_frame(job,2.5,assets).tobytes(),app.animated_core(job,2.5-1/30,assets).tobytes())

    def test_invalid_input(self):
        for change in [{'bpm':0},{'bpm':'nan'},{'items':[]},{'accent':'bad-color'}]:
            with self.assertRaises(ValueError):app.prepare(dict(self.payload,**change))

    def test_custom_transparent_sticker(self):
        path=self.root/'transparent.png';Image.new('RGBA',(40,40),(255,0,0,100)).save(path)
        raw=base64.b64encode(path.read_bytes()).decode()
        job=app.prepare(dict(self.payload,stickers=[raw,None]))
        with Image.open(app.DATA/job['id']/'sticker0.png') as im:
            self.assertEqual(im.mode,'RGBA')
            self.assertEqual(im.getpixel((90,90))[3],100)

    def test_real_video(self):
        job=app.prepare(dict(self.payload,bpm=300,beats=[.25]*5))
        app.render(job)
        self.assertEqual(job['status'],'done',job.get('error'))
        video=app.DATA/job['id']/'video.mp4'
        result=subprocess.run([app.FFMPEG,'-i',str(video),'-f','null','-'],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        for expected in ['1920x1080','30 fps','Audio: aac']:
            self.assertIn(expected,result.stderr)

if __name__=='__main__':unittest.main()
