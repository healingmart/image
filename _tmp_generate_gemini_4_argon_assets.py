from PIL import Image, ImageDraw, ImageFont, ImageFilter
from pathlib import Path
import math, random

ROOT = Path(".")
BOLD = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
REG = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"

def F(path, size):
    return ImageFont.truetype(path, size, index=1)

def rr(d, box, r, fill, outline=None, width=1):
    d.rounded_rectangle(box, radius=r, fill=fill, outline=outline, width=width)

def save(img, name):
    img.convert("RGB").save(ROOT / name, "WEBP", quality=82, method=6)

# --- HERO 16:9 ---
W,H=1600,900
img=Image.new("RGB",(W,H))
px=img.load()
for y in range(H):
    for x in range(W):
        t=y/H
        r=int(4+7*(1-t)); g=int(12+20*(1-t)); b=int(36+42*(1-t))
        px[x,y]=(r,g,b)
d=ImageDraw.Draw(img,"RGBA")
# futuristic arcs and grid
for i in range(9):
    inset=120+i*52
    d.ellipse((inset,120+i*18,W-inset,H-110-i*12), outline=(52,133,255,55), width=2)
for x in range(0,W,100):
    d.line((x,0,x,H),fill=(63,120,220,25),width=1)
for y in range(0,H,80):
    d.line((0,y,W,y),fill=(63,120,220,20),width=1)
# center energy cube
cx,cy=1020,420
for s,a in [(340,40),(270,70),(210,110)]:
    d.rectangle((cx-s//2,cy-s//2,cx+s//2,cy+s//2),outline=(90,170,255,a),width=3)
for r,a in [(155,60),(110,90),(72,180)]:
    d.ellipse((cx-r,cy-r,cx+r,cy+r),fill=(255,127,28,a//5),outline=(255,160,55,a),width=3)
# dark glass panel
rr(d,(110,95,1490,800),40,(2,14,44,190),(98,160,255,110),2)
rr(d,(145,135,670,207),34,(7,58,135,235))
d.ellipse((175,160,195,180),fill=(255,139,26,255))
d.text((218,148),"GOOGLE GEMINI 4 ARGON",font=F(BOLD,30),fill="white")
d.text((150,270),"제미나이 4 아르곤",font=F(BOLD,84),fill="white")
d.text((150,382),"정식 출시",font=F(BOLD,122),fill="white")
d.rounded_rectangle((150,525,580,538),6,fill=(255,139,26,255))
d.text((150,575),"GPT-6 · Claude와",font=F(BOLD,50),fill=(224,238,255))
d.text((150,642),"성능 · 가격 · 사용 경로 비교",font=F(BOLD,52),fill=(255,181,81))
d.text((150,742),"출시일 · 1M 컨텍스트 · API 요금 · 코딩 벤치마크",font=F(REG,29),fill=(214,228,246))
save(img,"gemini-4-argon-launch-20261014-hero.webp")

# --- SUMMARY ---
W,H=1600,1000
img=Image.new("RGB",(W,H),(248,250,253)); d=ImageDraw.Draw(img)
rr(d,(70,55,1530,200),30,(17,39,91))
d.ellipse((102,92,120,110),fill=(255,126,28))
d.text((140,78),"GEMINI 4 ARGON · ARTICLE SUMMARY",font=F(BOLD,28),fill=(183,214,255))
d.text((100,122),"Gemini 4 Argon 한눈에 보기",font=F(BOLD,56),fill="white")
cards=[
("공개일","2026. 10. 13","Google 글로벌 공개"),
("이용 경로","Gemini 앱 · 검색 AI Mode","개발자는 API · 기업용 플랫폼"),
("통합 컨텍스트","1,048,576 tokens","입력·thinking·출력이 함께 사용"),
("API 출시 가격","$2 입력 / $10 출력","100만 토큰 · 11월 30일까지"),
("12월 1일부터","$4 입력 / $20 출력","출시 프로모션 종료 후"),
("Terminal-Bench 4.0","57.58%","같은 Mini-SWE-agent 기준 Argon")
]
xs=[70,810]; ys=[240,440,640]
for i,(k,v,s) in enumerate(cards):
    x=xs[i%2]; y=ys[i//2]
    rr(d,(x,y,x+720,y+165),24,(255,255,255),(214,224,238),2)
    d.text((x+30,y+22),k,font=F(BOLD,24),fill=(54,88,150))
    d.text((x+30,y+62),v,font=F(BOLD,38 if len(v)<24 else 32),fill=(19,39,84))
    d.text((x+30,y+120),s,font=F(REG,20),fill=(81,99,124))
rr(d,(70,840,1530,950),24,(255,244,230),(255,184,91),2)
d.text((100,862),"읽는 기준",font=F(BOLD,25),fill=(172,77,8))
d.text((245,860),"모델 성능 · 실제 이용 경로 · API 가격 · 벤치마크를 서로 다른 기준으로 분리해서 비교하세요.",font=F(BOLD,25),fill=(88,48,18))
d.text((100,915),"기준일 2026-10-15 · Google / OpenAI / Anthropic 공식 자료와 Vals 공개 리더보드 기준",font=F(REG,18),fill=(100,104,112))
save(img,"gemini-4-argon-launch-20261014-summary.webp")

# --- TERMINAL BENCH COMPARISON ---
W,H=1600,1100
img=Image.new("RGB",(W,H),(248,250,253)); d=ImageDraw.Draw(img)
rr(d,(80,70,650,128),28,(225,238,255))
d.ellipse((105,91,121,107),fill=(255,126,28))
d.text((140,79),"INDEPENDENT CODING EVALUATION",font=F(BOLD,24),fill=(40,93,184))
d.text((80,155),"같은 터미널 평가도 점수 차이가 납니다",font=F(BOLD,54),fill=(18,39,86))
d.text((80,226),"Vals Terminal-Bench 4.0 · Mini-SWE-agent · 2026년 10월 13일 갱신",font=F(REG,28),fill=(72,88,112))
d.rounded_rectangle((80,294,210,302),4,fill=(61,111,235))
# table
x0,y0=80,340
cols=[100,530,265,445]
headers=["순위","모델","점수","평가 범위"]
rows=[
("01","Claude Opus 5.5","65.15%","터미널 과제 · 원점수"),
("02","Claude Sonnet 5.5","64.14%","터미널 과제"),
("03","GPT-6 Astra","59.60%","터미널 과제"),
("04","Claude Fable 5.1","58.08%","터미널 과제 · 원점수"),
("05","Gemini 4 Argon","57.58%","터미널 과제"),
("06","GPT-6.1 Sol","55.05%","터미널 과제"),
]
rowh=76
# header
cx=x0
for w,hdr in zip(cols,headers):
    d.rectangle((cx,y0,cx+w,y0+62),fill=(25,48,105))
    d.text((cx+18,y0+14),hdr,font=F(BOLD,22),fill="white")
    cx+=w
for ri,row in enumerate(rows):
    yy=y0+62+ri*rowh
    fill=(236,245,255) if ri==4 else (255,255,255)
    cx=x0
    for ci,(w,val) in enumerate(zip(cols,row)):
        d.rectangle((cx,yy,cx+w,yy+rowh),fill=fill,outline=(214,224,238))
        col=(28,56,120) if ri==4 else (28,37,51)
        ff=F(BOLD,24) if (ri==4 or ci==2) else F(REG,23)
        d.text((cx+18,yy+22),val,font=ff,fill=col)
        cx+=w
# note
yy=y0+62+len(rows)*rowh+28
rr(d,(80,yy,1520,yy+105),22,(255,247,232),(255,191,104),2)
d.text((110,yy+18),"평가 조건",font=F(BOLD,22),fill=(143,69,12))
d.text((250,yy+18),"Terminal-Bench는 어려운 코딩·운영 태스크 평가이며 모든 업무의 종합 순위가 아닙니다.",font=F(REG,22),fill=(100,59,25))
d.text((110,yy+58),"Opus·Fable 점수에는 구형 모델 fallback 실행이 포함되어 있어 처리 방식에 따라 보정 점수가 달라질 수 있습니다.",font=F(REG,19),fill=(100,59,25))
d.text((80,H-65),"출처: Vals Terminal-Bench 4.0 공개 리더보드 · 기준일 2026-10-15",font=F(REG,18),fill=(96,111,130))
save(img,"gemini-4-argon-launch-20261014-compare.webp")

# --- API PRICE ---
W,H=1600,1120
img=Image.new("RGB",(W,H),(248,250,253)); d=ImageDraw.Draw(img)
rr(d,(80,70,500,128),28,(225,238,255))
d.ellipse((105,91,121,107),fill=(255,126,28))
d.text((140,79),"API PRICE SNAPSHOT · USD",font=F(BOLD,24),fill=(40,93,184))
d.text((80,155),"모델마다 API 가격대가 다릅니다",font=F(BOLD,54),fill=(18,39,86))
d.text((80,226),"표준 입력·출력 · 100만 토큰당 · 구독료·캐시·도구 비용 제외",font=F(REG,28),fill=(72,88,112))
d.rounded_rectangle((80,294,210,302),4,fill=(61,111,235))
x0,y0=80,340
cols=[440,220,220,560]
headers=["모델","입력 / 1M","출력 / 1M","조건·메모"]
rows=[
("Gemini 4 Argon","$2","$10","11/30까지 · 12/1부터 $4 / $20"),
("Claude Sonnet 5.5","$2","$10","일상 코딩·빠른 작업"),
("GPT-6.1 Sol","$2","$10","API short-context"),
("Claude Opus 5.5","$4","$20","복잡한 코딩·에이전트"),
("Claude Fable 5.1","$10","$50","장시간 코딩·지식 업무"),
("GPT-6 Astra","$10","$50","최고 난도 추론"),
("GPT-6 Luna","$0.10","$0.50","반복·일상 API 업무"),
]
rowh=72
cx=x0
for w,hdr in zip(cols,headers):
    d.rectangle((cx,y0,cx+w,y0+62),fill=(25,48,105))
    d.text((cx+18,y0+14),hdr,font=F(BOLD,22),fill="white"); cx+=w
for ri,row in enumerate(rows):
    yy=y0+62+ri*rowh; fill=(236,245,255) if ri==0 else (255,255,255)
    cx=x0
    for ci,(w,val) in enumerate(zip(cols,row)):
        d.rectangle((cx,yy,cx+w,yy+rowh),fill=fill,outline=(214,224,238))
        ff=F(BOLD,22) if (ri==0 or ci in (1,2)) else F(REG,21)
        d.text((cx+18,yy+20),val,font=ff,fill=(25,48,105) if ri==0 else (28,37,51)); cx+=w
yy=y0+62+len(rows)*rowh+28
rr(d,(80,yy,1520,yy+105),22,(25,48,105))
d.text((110,yy+18),"예시",font=F(BOLD,21),fill=(119,205,255))
d.text((190,yy+18),"입력 100k + 출력 20k tokens → Argon 프로모션 $0.40, 12/1 이후 $0.80",font=F(REG,21),fill="white")
d.text((110,yy+58),"* OpenAI short-context 입력 구간은 272K tokens 이하. 장문·캐시·도구 사용 요금은 별도입니다.",font=F(REG,18),fill=(215,227,246))
d.text((80,H-62),"출처: Google AI for Developers · Anthropic · OpenAI API pricing · 기준일 2026-10-15",font=F(REG,18),fill=(96,111,130))
save(img,"gemini-4-argon-launch-20261014-data.webp")
