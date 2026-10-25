#!/usr/bin/env python3
"""Render a config-driven silent product demo. See references/config.md."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import argparse, json, math, subprocess, concurrent.futures
HERE=Path('.')
W,H,FPS,DURATION=1920,1080,60,3.8
PRODUCT='Product Demo'
OUTRO='보안에서 업무까지'
SCENES=[]
FONT=MEDIUM=ENGLISH=''
CROP_TOP=0
OUTPUT=None

def find_font(explicit, candidates, patterns=()):
 if explicit:
  p=Path(explicit).expanduser()
  if p.is_file():return str(p)
  raise ValueError(f'Font does not exist: {p}')
 for p in candidates:
  if Path(p).is_file():return p
 for base,pattern in patterns:
  for p in Path(base).glob(pattern):
   if p.is_file():return str(p)
 raise ValueError('A serif font was not found; set font_ko / font_en in the config.')

def run(args): subprocess.run(['ffmpeg','-y',*args,'-loglevel','error'],check=True)
def font(size,bold=True): return ImageFont.truetype(FONT if bold else MEDIUM,size)
def assets(scenes):
 bg=Image.new('RGB',(W,H),(249,249,247))
 # A neutral paper-white canvas and a soft contact shadow; no grid or glow.
 shadow=Image.new('RGBA',(W,H));sd=ImageDraw.Draw(shadow)
 sd.ellipse((240,878,1690,1010),fill=(40,42,44,25))
 shadow=shadow.filter(ImageFilter.GaussianBlur(45))
 bg=Image.alpha_composite(bg.convert('RGBA'),shadow)
 bg.convert('RGB').save(HERE/'background.png')
 mask=Image.new('L',(1600,750));ImageDraw.Draw(mask).rounded_rectangle((0,0,1599,749),24,fill=255);mask.save(HERE/'mask.png')
 tags=[scene.get('keywords',[]) for scene in scenes]
 for i,s in enumerate(scenes):
  im=Image.new('RGBA',(W,H));d=ImageDraw.Draw(im)
  d.text((112,49),s.get('section','FEATURES'),font=ImageFont.truetype(ENGLISH,24),fill=(123,124,122))
  im.save(HERE/f'meta-{i}.png')
  im=Image.new('RGBA',(W,H));d=ImageDraw.Draw(im)
  titlefont=font(72)
  while d.textlength(s['title'],font=titlefont)>850 and titlefont.size>30:
   titlefont=font(titlefont.size-2)
  d.text((108,93),s['title'],font=titlefont,fill=(43,44,42))
  im.save(HERE/f'title-{i}.png')
  for j,tag in enumerate(tags[i]):
   chip=Image.new('RGBA',(360,70));cd=ImageDraw.Draw(chip)
   cd.line((0,13,0,54),fill=(181,182,178,255),width=2)
   cd.text((25,17),tag,font=font(29,False),fill=(91,93,89,255))
   chip.save(HERE/f'chip-{i}-{j}.png')
 for name,title,sub in [('intro',PRODUCT,'  ×  '.join(dict.fromkeys(scene.get('section','FEATURES') for scene in scenes))),('outro',OUTRO,PRODUCT)]:
  im=bg.copy();d=ImageDraw.Draw(im)
  textfont=ImageFont.truetype(ENGLISH,116) if name=='intro' else font(100)
  while d.textlength(title,font=textfont)>1660:
   textfont=ImageFont.truetype(ENGLISH if name=='intro' else FONT,textfont.size-2)
  tw=d.textlength(title,font=textfont)
  d.text(((W-tw)/2,385),title,font=textfont,fill=(43,44,42))
  sf=font(28,False);tw=d.textlength(sub,font=sf);d.text(((W-tw)/2,570),sub,font=sf,fill=(121,122,117))
  d.line((895,674,1025,674),fill=(171,173,167),width=1)
  im.convert('RGB').save(HERE/f'{name}.png')

def camera(mode):
 p=f'(1-cos(PI*on/{round(DURATION*FPS)-1}))/2';wave=f'sin(PI*({p}))';sweep=f'1-2*({p})'
 if mode=='orbit': a=f'65*({sweep})'; b=f'25*({wave})';roll='0.012*cos(PI*t/3.8)'
 elif mode=='push': a=f'75*(1-({p}))';b=f'35*(1-({p}))';roll='-0.016*(1-cos(PI*t/3.8))/2'
 elif mode=='sweep':a=f'-70*({sweep})';b=f'18*({wave})';roll='0.012*cos(PI*t/3.8)'
 elif mode=='crane':a=f'18*({wave})';b=f'55*({sweep})';roll='0.008*sin(PI*t/3.8)'
 elif mode=='reveal':a=f'-85*(1-({p}))';b=f'20*({wave})';roll='0.02*cos(PI*t/3.8)'
 else:a=f'45*({sweep})';b=f'-20*({wave})';roll='-0.012*cos(PI*t/3.8)'
 roll=roll.replace('/3.8',f'/{DURATION}')
 return f"perspective=x0='{a}':y0='{b}':x1='W-({a})':y1='-({b})':x2='-({a})':y2='H-({b})':x3='W+({a})':y3='H+({b})':sense=destination:eval=frame:interpolation=cubic,rotate='{roll}':c=none"

def render_scene(i,s,source_dir):
 z=s['zoom'];p=f'(1-cos(PI*on/{round(DURATION*FPS)-1}))/2'
 zoom=f'{z}-({z}-1.02)*({p})' if s['motion']=='pull' else f'1.02+({z}-1.02)*({p})'
 fx,fy=s['focus'];x=f'(iw-iw/zoom)*{fx}';y=f'(ih-ih/zoom)*{fy}'
 # All inputs run at 60 fps. Upsampling before zoompan reduces integer crop jitter.
 # Each caption layer has its own entrance, hold and exit timing.
 entry='pow(max(0,1-t/0.58),3)';exit=f'pow(max(0,(t-{DURATION-0.68})/0.68),2)'
 title_x=f'{-150 if i%2==0 else 150}*({entry})+100*({exit})'
 filters=f"[0:v]scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=white,crop=1920:{1080-CROP_TOP}:0:{CROP_TOP},scale=3840:1800:force_original_aspect_ratio=decrease:flags=lanczos,pad=3840:1800:(ow-iw)/2:(oh-ih)/2:color=white,fps=60,zoompan=z='{zoom}':x='{x}':y='{y}':d=1:s=1600x750:fps=60,format=rgba[vid];[vid][3:v]alphamerge,pad=1920:1080:160:220:color=black@0,{camera(s['motion'])}[card];[1:v][card]overlay=x=0:y=0:shortest=1:format=auto[scene];[2:v]format=rgba,fade=t=in:st=0.08:d=0.34:alpha=1,fade=t=out:st={DURATION-0.68}:d=0.52:alpha=1[title];[scene][title]overlay=x='{title_x}':y=0:shortest=1:format=auto[titled];[titled][4:v]overlay=0:0:shortest=1:format=auto[meta];[5:v]format=rgba,fade=t=in:st=0.5:d=0.3:alpha=1,fade=t=out:st={DURATION-0.9}:d=0.4:alpha=1[c0];[meta][c0]overlay=x='1060+70*pow(max(0,1-(t-0.5)/0.5),3)':y=109:shortest=1:format=auto[chip0];[6:v]format=rgba,fade=t=in:st=0.8:d=0.3:alpha=1,fade=t=out:st={DURATION-0.75}:d=0.4:alpha=1[c1];[chip0][c1]overlay=x='1450+70*pow(max(0,1-(t-0.8)/0.5),3)':y=109:shortest=1:format=auto,fps=60,setsar=1,format=yuv420p[out]"
 args=['-ss',str(s['start']),'-t',str(DURATION),'-i',str((source_dir/s['file']).resolve())]
 for asset in ['background.png',f'title-{i}.png','mask.png',f'meta-{i}.png',f'chip-{i}-0.png',f'chip-{i}-1.png']:
  args+=['-loop','1','-framerate','60','-i',str(HERE/asset)]
 run([*args,'-filter_complex_threads','2','-filter_complex',filters,'-map','[out]','-an','-t',str(DURATION),'-r','60','-c:v','libx264','-preset','fast','-crf','18',str(HERE/f'scene-{i}.mp4')])
 print(f"Rendered {i+1}: {s['title']}",flush=True)

def assemble():
 for n in ['intro','outro']:
  run(['-loop','1','-framerate','60','-i',str(HERE/f'{n}.png'),'-vf',"scale=3840:2160:flags=lanczos,zoompan=z='1+0.025*(1-cos(PI*on/89))/2':d=1:s=1920x1080:fps=60,format=yuv420p",'-t','1.5','-an','-c:v','libx264','-preset','fast','-crf','18',str(HERE/f'{n}.mp4')])
 files=[HERE/'intro.mp4']+[HERE/f'scene-{i}.mp4' for i in range(len(SCENES))]+[HERE/'outro.mp4']
 lengths=[1.5]+[DURATION]*len(SCENES)+[1.5];trans=['zoomin','smoothleft','fadewhite','diagtl','slideup','hblur','smoothright','circleopen','fade']
 args=[]
 for f in files:args+=['-i',str(f)]
 filters=[f'[{i}:v]fps=60,settb=AVTB,setpts=PTS-STARTPTS[v{i}]' for i in range(len(files))]
 prev='v0';elapsed=lengths[0]
 for i in range(1,len(files)):
  elapsed-=0.28;filters.append(f'[{prev}][v{i}]xfade=transition={trans[(i-1)%len(trans)]}:duration=0.28:offset={elapsed:.3f}[x{i}]');prev=f'x{i}';elapsed+=lengths[i]
 run([*args,'-filter_complex_threads','2','-filter_complex',';'.join(filters),'-map',f'[{prev}]','-an','-c:v','libx264','-preset','fast','-crf','18','-movflags','+faststart',str(OUTPUT)])

if __name__=='__main__':
 parser=argparse.ArgumentParser(description='Render a silent serif/light product reel at 60 fps.')
 parser.add_argument('--config',type=Path,required=True)
 parser.add_argument('--output-dir',type=Path,required=True)
 parser.add_argument('--jobs',type=int,default=2)
 parser.add_argument('--scene',type=int,help='Render only one zero-based scene for visual QA.')
 a=parser.parse_args()
 config=json.loads(a.config.read_text(encoding='utf-8'))
 HERE=a.output_dir.resolve();HERE.mkdir(parents=True,exist_ok=True)
 OUTPUT=HERE/'showcase.mp4';PRODUCT=config['product_name'];OUTRO=config.get('outro_title',PRODUCT)
 DURATION=float(config.get('scene_duration',3.8))
 if not 2.5<=DURATION<=8:raise ValueError('scene_duration must be 2.5–8 seconds')
 CROP_TOP=int(config.get('crop_top_px',0))
 if not 0<=CROP_TOP<=300:raise ValueError('crop_top_px must be 0–300 after 1920x1080 normalization')
 FONT=find_font(config.get('font_ko'),[
  '/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc',
  '/usr/share/fonts/truetype/nanum/NanumMyeongjo.ttf'],[
  ('/System/Library/AssetsV2/com_apple_MobileAsset_Font8','*/AssetData/NanumMyeongjo.ttc'),
  (str(Path.home()/'Library/Fonts'),'*Serif*KR*')])
 MEDIUM=FONT
 ENGLISH=find_font(config.get('font_en'),[
  '/System/Library/Fonts/Supplemental/Baskerville.ttc',
  '/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf',FONT])
 SCENES=config['scenes']
 if not SCENES:raise ValueError('At least one scene is required')
 base=a.config.resolve().parent
 for scene in SCENES:
  scene['start']=float(scene['start']);scene['zoom']=float(scene.get('zoom',1.14))
  scene['focus']=[float(v) for v in scene.get('focus',[0.5,0.5])]
  if len(scene['focus'])!=2 or not all(0<=v<=1 for v in scene['focus']):raise ValueError('focus must contain two fractions in [0,1]')
  if not 1<=scene['zoom']<=2:raise ValueError('zoom must be 1–2')
  if scene.get('motion','orbit') not in ['orbit','push','pull','sweep','crane','reveal']:raise ValueError('Unknown motion preset')
  scene.setdefault('motion','orbit')
  scene['file']=str((base/scene['file']).resolve())
  if not Path(scene['file']).is_file():raise FileNotFoundError(scene['file'])
  # Avoid silently freezing a missing tail of a source recording.
  probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','json',scene['file']]))
  if scene['start']<0 or scene['start']+DURATION>float(probe['format']['duration']):raise ValueError('Scene extends beyond the source video')
  if len(scene.get('keywords',[]))!=2:raise ValueError('Each scene needs exactly two short noun keywords')
  for key in ['title','section','keywords']:
   if key=='title' and not scene.get(key):raise ValueError('Each scene needs a title')
 assets(SCENES)
 if a.scene is not None:
  render_scene(a.scene,SCENES[a.scene],base)
 else:
  with concurrent.futures.ThreadPoolExecutor(max_workers=max(1,min(a.jobs,4))) as pool:
   list(pool.map(lambda i:render_scene(i,SCENES[i],base),range(len(SCENES))))
  assemble()
  probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(OUTPUT)]))
  if any(stream['codec_type']=='audio' for stream in probe['streams']):raise RuntimeError('Unexpected audio stream')
  duration=float(probe['format']['duration'])
  run(['-ss',str(min(2.5,duration/2)),'-i',str(OUTPUT),'-frames:v','1','-vf','scale=1280:-1',str(HERE/'preview.jpg')])
  print(json.dumps({'video':str(OUTPUT),'preview':str(HERE/'preview.jpg'),'duration':duration,'fps':60,'audio':False},ensure_ascii=False))
