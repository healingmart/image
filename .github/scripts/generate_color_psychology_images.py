from PIL import Image, ImageDraw, ImageFont, ImageFilter
from pathlib import Path
import math, glob, os, textwrap

W, H = 1648, 927
OUT = Path(".")

def font_path(bold=False):
    pats = [
        "/usr/share/fonts/opentype/noto/NotoSansCJK-*.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK*.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK*.ttc",
    ]
    files=[]
    for p in pats:
        files.extend(glob.glob(p))
    if bold:
        for f in files:
            if "Bold" in f or "Black" in f:
                return f
    for f in files:
        if "Regular" in f or "Medium" in f:
            return f
    return files[0] if files else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

REG=font_path(False)
BOLD=font_path(True)

def F(size,bold=False):
    return ImageFont.truetype(BOLD if bold else REG, size=size)

def lerp(a,b,t): return int(a+(b-a)*t)
def grad_rect(img, box, c1, c2, vertical=True):
    x0,y0,x1,y1=box
    d=ImageDraw.Draw(img)
    n=(y1-y0) if vertical else (x1-x0)
    for i in range(max(1,n)):
        t=i/max(1,n-1)
        c=tuple(lerp(c1[j],c2[j],t) for j in range(3))
        if vertical: d.line((x0,y0+i,x1,y0+i), fill=c)
        else: d.line((x0+i,y0,x0+i,y1), fill=c)

def save(img,name,q=88):
    img.save(name,"WEBP",quality=q,method=6)

# 1. HERO — four color atmospheres + quiet seated silhouette
img=Image.new("RGB",(W,H),(15,28,48))
d=ImageDraw.Draw(img)
# wall panels
panels=[
    (0,0,430,H,(13,34,60),(20,65,110)),
    (430,0,860,H,(13,72,155),(37,151,244)),
    (860,0,1240,H,(121,62,62),(255,139,102)),
    (1240,0,W,H,(72,109,75),(183,221,131))
]
for x0,y0,x1,y1,c1,c2 in panels:
    grad_rect(img,(x0,y0,x1,y1),c1,c2,False)
# window frames and horizons
for x in [430,860,1240]:
    d.rectangle((x-10,0,x+10,H), fill=(31,34,39))
d.rectangle((0,575,W,H), fill=(54,50,46))
# soft floor reflections
overlay=Image.new("RGBA",(W,H),(0,0,0,0)); od=ImageDraw.Draw(overlay)
od.polygon([(390,575),(885,575),(1160,H),(600,H)], fill=(38,115,223,80))
od.polygon([(880,575),(1230,575),(1460,H),(1050,H)], fill=(255,126,87,74))
od.polygon([(1240,575),(W,575),(W,H),(1370,H)], fill=(116,199,96,70))
overlay=overlay.filter(ImageFilter.GaussianBlur(22))
img=Image.alpha_composite(img.convert("RGBA"),overlay)
d=ImageDraw.Draw(img)
# distant abstract landscape
d.ellipse((930,180,990,240), fill=(255,241,195,220))
for i in range(6):
    y=330+i*24
    pts=[(860,y),(930,y-45),(1010,y-5),(1090,y-60),(1170,y-15),(1240,y+5)]
    d.polygon(pts, fill=(105+8*i,76+8*i,82+7*i,135))
# plant
d.rectangle((1530,535,1575,805), fill=(77,58,39,255))
for a in range(14):
    x=1550+int(math.sin(a*1.9)*70); y=520-a*19
    d.ellipse((x-28,y-15,x+28,y+18), fill=(45,119+3*a,60,255))
# chair + person
d.rounded_rectangle((1035,590,1485,860), radius=35, fill=(112,91,75,255))
d.rectangle((1080,690,1440,888), fill=(77,57,43,255))
d.ellipse((1145,335,1265,455), fill=(42,31,26,255))
d.polygon([(1160,440),(1260,440),(1355,675),(1070,675)], fill=(234,220,197,255))
d.ellipse((1085,465,1180,610), fill=(234,220,197,255))
d.ellipse((1265,465,1360,610), fill=(234,220,197,255))
# side table & mug
d.ellipse((760,720,930,760), fill=(126,104,84,255))
d.rectangle((770,740,920,900), fill=(118,96,78,255))
d.rounded_rectangle((815,672,880,730), 10, fill=(224,215,196,255))
save(img.convert("RGB"),"color-psychology-20261020-hero.webp",90)

# 2. SUMMARY infographic
img=Image.new("RGB",(W,H),(251,250,247))
d=ImageDraw.Draw(img)
segments=[(80,78,430,(45,83,170)),(430,78,780,(232,84,63)),(780,78,1130,(247,184,54)),(1130,78,1510,(54,139,110))]
for x0,y,x1,c in segments:
    d.rounded_rectangle((x0,y,x1,y+14),radius=7,fill=c)
d.text((84,126),"COLOR PSYCHOLOGY · 3 STEPS",font=F(27,True),fill=(45,83,170))
d.text((84,175),"색은 ‘처방’보다",font=F(61,True),fill=(24,42,70))
d.text((84,248),"환경을 읽는 단서에 가깝습니다",font=F(61,True),fill=(24,42,70))
d.text((84,347),"같은 색이라도 장면과 사람에 따라 다르게 느껴집니다. 내 공간에서 작은 변화로 반응을 살펴보세요.",font=F(28),fill=(72,87,105))
cards=[
    (84,468,528,767,(45,83,170),"1","장면을 먼저 고르기","집중할 책상인지, 쉴 침실인지부터 정합니다."),
    (554,468,998,767,(232,84,63),"2","색 단서 하나만 바꾸기","노트 탭·머그컵·쿠션처럼 되돌리기 쉬운 것부터 시작합니다."),
    (1024,468,1510,767,(54,139,110),"3","내 반응을 기록하기","예쁜지와 편한지, 눈이 피로한지를 나눠 봅니다.")
]
for x0,y0,x1,y1,c,n,t,body in cards:
    d.rounded_rectangle((x0,y0,x1,y1),radius=24,fill="white",outline=(222,226,232),width=2)
    d.ellipse((x0+34,y0+35,x0+92,y0+93),fill=c)
    bb=d.textbbox((0,0),n,font=F(26,True)); tw=bb[2]-bb[0]; th=bb[3]-bb[1]
    d.text((x0+63-tw/2,y0+64-th/2-4),n,font=F(26,True),fill="white")
    d.text((x0+34,y0+126),t,font=F(32,True),fill=(24,42,70))
    # manual wrap
    words=body.split(" ")
    lines=[]; cur=""
    for w in words:
        test=(cur+" "+w).strip()
        if d.textlength(test,font=F(24)) > x1-x0-68 and cur:
            lines.append(cur); cur=w
        else: cur=test
    if cur: lines.append(cur)
    for j,line in enumerate(lines):
        d.text((x0+34,y0+190+j*41),line,font=F(24),fill=(75,88,104))
d.rounded_rectangle((84,807,1510,895),radius=18,fill=(24,42,70))
d.ellipse((116,842,132,858),fill=(247,184,54))
d.text((151,830),"색은 기분을 조금 다르게 느끼게 할 수 있지만, 건강 문제를 해결하는 치료를 대신하지는 않습니다.",font=F(25),fill="white")
save(img,"color-psychology-20261020-summary.webp",92)

# 3. CONTEXT split scene
img=Image.new("RGB",(W,H),(231,223,206))
d=ImageDraw.Draw(img)
d.rectangle((824,0,W,H),fill=(16,55,95))
# left desk paper
d.polygon([(0,100),(824,0),(824,927),(0,927)],fill=(221,211,191))
d.polygon([(120,230),(720,180),(815,780),(185,840)],fill=(250,245,232))
# book + cup
d.rounded_rectangle((560,20,790,160),20,fill=(28,60,101))
d.ellipse((660,48,790,188),fill=(211,197,174))
# red X + pencil
d.line((390,430,610,625),fill=(209,53,41),width=28)
d.line((590,410,410,650),fill=(209,53,41),width=28)
d.polygon([(600,690),(760,810),(725,842),(565,722)],fill=(219,64,48))
# hands simple
d.ellipse((90,500,300,760),fill=(216,161,126))
# right gift
d.rounded_rectangle((955,315,1335,675),28,fill=(242,235,214))
d.rectangle((1125,315,1175,675),fill=(194,28,33))
d.rectangle((955,475,1335,525),fill=(194,28,33))
d.ellipse((1050,390,1160,500),outline=(194,28,33),width=24)
d.ellipse((1140,390,1265,500),outline=(194,28,33),width=24)
# red ribbon curving toward hand
pts=[]
for i in range(120):
    t=i/119
    x=1170+360*t
    y=410-115*math.sin(t*math.pi)
    pts.append((x,y))
d.line(pts,fill=(211,35,39),width=30)
# hand on right
d.ellipse((1450,180,1648,455),fill=(226,177,143))
# decorative flower
for a in range(8):
    d.line((880,260,890+80*math.cos(a),180+80*math.sin(a)),fill=(225,214,189),width=4)
    d.ellipse((880+70*math.cos(a)-8,170+70*math.sin(a)-8,880+70*math.cos(a)+8,170+70*math.sin(a)+8),fill=(244,237,217))
save(img,"color-psychology-20261020-context.webp",90)

# 4. PRACTICAL warm desk
img=Image.new("RGB",(W,H),(236,220,190))
d=ImageDraw.Draw(img)
grad_rect(img,(0,0,W,420),(239,247,250),(253,233,190),True)
# window
d.rectangle((0,0,540,410),fill=(224,241,247))
d.rectangle((500,0,540,410),fill=(242,232,214))
# desk
d.polygon([(0,470),(1500,430),(1648,927),(0,927)],fill=(161,101,54))
# plant left
d.ellipse((20,410,260,650),fill=(221,207,177))
for i in range(20):
    x=110+int(math.sin(i*1.3)*120); y=345-int(i*7)
    d.ellipse((x-28,y-16,x+34,y+18),fill=(55,126+3*(i%6),57))
# lamp
d.rectangle((760,245,790,550),fill=(184,115,30))
d.ellipse((640,110,910,280),fill=(225,143,29))
d.ellipse((710,525,850,570),fill=(184,115,30))
# books
colors=[(38,63,95),(210,92,66),(228,165,61)]
for i,c in enumerate(colors):
    d.rounded_rectangle((440+i*18,365-i*7,620+i*18,520-i*7),10,fill=c)
# mug
d.rounded_rectangle((820,450,940,575),20,fill=(236,226,204))
d.arc((920,475,995,555),270,90,fill=(37,57,82),width=12)
d.rectangle((820,535,940,575),fill=(37,57,82))
# notebook
d.polygon([(340,600),(970,555),(1080,745),(420,790)],fill=(248,245,235))
# color blocks on notebook
d.polygon([(560,620),(720,610),(760,695),(595,708)],fill=(233,111,85))
d.polygon([(730,600),(850,590),(875,655),(748,668)],fill=(45,83,128))
d.ellipse((880,585,950,655),fill=(242,182,53))
# tabs
for i,c in enumerate([(247,184,54),(45,83,170),(232,84,63)]):
    d.rectangle((820+i*55,735,865+i*55,770),fill=c)
# right chair
d.ellipse((1180,560,1710,1050),fill=(34,55,82))
# blanket
d.polygon([(1450,520),(1648,620),(1648,927),(1510,860)],fill=(218,176,93))
# framed abstract art
d.rectangle((1275,55,1590,355),fill=(230,223,207),outline=(112,80,55),width=12)
d.pieslice((1325,100,1470,245),90,270,fill=(27,53,82))
d.pieslice((1430,175,1555,300),270,90,fill=(220,97,63))
d.ellipse((1450,100,1550,200),fill=(225,164,56))
save(img,"color-psychology-20261020-practical.webp",90)

print("generated", [p for p in os.listdir(".") if p.startswith("color-psychology-20261020-") and p.endswith(".webp")])
