#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Regenera avatar.svg (Scan Matrix) desde la foto de perfil ACTUAL de GitHub.
Ejecutado por GitHub Actions: baja github.com/<user>.png, incrusta la foto y
reconstruye el SVG animado. Asi el avatar del README sigue "la que uno cargue".
"""
import base64, io, os, ssl, urllib.request

from fontTools.ttLib import TTFont
from fontTools.subset import Subsetter, Options

USER = os.environ.get("AVATAR_USER", "fevar54")
FONT = "cuneiform.otf"
OUT = "avatar.svg"

# deterministico (mismo layout entre corridas; solo cambia la foto)
import random
random.seed(7)

S, R = 300, 132
CX = CY = S // 2

# 1) descargar avatar actual (sigue redireccion a la imagen real)
url = f"https://github.com/{USER}.png?size=460"
ctx = ssl.create_default_context()
req = urllib.request.Request(url, headers={"User-Agent": "avatar-bot"})
raw = urllib.request.urlopen(req, timeout=30, context=ctx).read()
mime = "image/jpeg" if raw[:2] == b"\xff\xd8" else ("image/gif" if raw[:3] == b"GIF" else "image/png")
img_b64 = base64.b64encode(raw).decode()

# 2) subset fuente cuneiforme
font = TTFont(FONT)
cune = sorted(cp for cp in font.getBestCmap().keys() if 0x12000 <= cp <= 0x123FF)
pick = cune[:: max(1, len(cune) // 18)][:18]
glyphs = [chr(cp) for cp in pick]
opts = Options(); opts.flavor = "woff2"; opts.desubroutinize = True
ss = Subsetter(options=opts); ss.populate(unicodes=pick); ss.subset(font)
b = io.BytesIO(); font.save(b)
font_b64 = base64.b64encode(b.getvalue()).decode()

digits = list("0123456789")
pool = glyphs + digits

FS = 15
cols = []
for x in range(CX - R + 8, CX + R - 6, 20):
    half = int((R ** 2 - (x - CX) ** 2) ** 0.5) if abs(x - CX) < R else 0
    if half < 20:
        continue
    dur = round(random.uniform(2.6, 5.5), 2)
    delay = round(-random.uniform(0, dur), 2)
    n = random.randint(4, 8)
    tsp = []
    for i in range(n):
        ch = random.choice(pool)
        fam = "monospace" if ch in digits else "Cune"
        head = (i == n - 1)
        op = 0.9 if head else (0.25 + 0.4 * i / max(1, n - 1))
        col = "#ff6b6b" if head else "#d81f1f"
        tsp.append(f'<tspan x="{x}" y="{i*FS}" font-family="{fam}" fill="{col}" fill-opacity="{op:.2f}">{ch}</tspan>')
    cols.append(
        f'<g style="animation:av_fall {dur}s linear {delay}s infinite" transform="translate(0,{CY-half})">'
        f'<text font-size="{FS}">{"".join(tsp)}</text></g>'
    )
rain = "\n".join(cols)

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {S} {S}" width="100%" role="img" aria-label="avatar scan matrix">
<defs>
<style>
@font-face {{ font-family:"Cune"; src:url(data:font/woff2;base64,{font_b64}) format("woff2"); }}
@keyframes av_fall {{ from {{ transform: translateY(-30px);}} to {{ transform: translateY({2*R+30}px);}} }}
@keyframes scan {{ 0% {{ transform: translateY({CY-R}px);}} 100% {{ transform: translateY({CY+R}px);}} }}
@keyframes ring {{ 0%,100% {{ opacity:.55; stroke-width:3;}} 50% {{ opacity:1; stroke-width:5;}} }}
@keyframes flick {{ 0%,100%{{opacity:.18}} 50%{{opacity:.30}} }}
</style>
<clipPath id="cir"><circle cx="{CX}" cy="{CY}" r="{R}"/></clipPath>
<filter id="gl" x="-40%" y="-40%" width="180%" height="180%">
  <feGaussianBlur stdDeviation="3.2" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
</filter>
<linearGradient id="red" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="#ff2b2b" stop-opacity="0.10"/>
  <stop offset="1" stop-color="#7a0000" stop-opacity="0.45"/>
</linearGradient>
<pattern id="scanlines" width="4" height="4" patternUnits="userSpaceOnUse">
  <rect width="4" height="1.2" y="0" fill="#000000" opacity="0.35"/>
</pattern>
</defs>

<g clip-path="url(#cir)">
  <image href="data:{mime};base64,{img_b64}" x="{CX-R}" y="{CY-R}" width="{2*R}" height="{2*R}" preserveAspectRatio="xMidYMid slice"/>
  <rect x="{CX-R}" y="{CY-R}" width="{2*R}" height="{2*R}" fill="url(#red)"/>
  <rect x="{CX-R}" y="{CY-R}" width="{2*R}" height="{2*R}" fill="url(#scanlines)" style="animation:flick 2.4s steps(2) infinite"/>
  <g>{rain}</g>
  <rect x="{CX-R}" y="-6" width="{2*R}" height="12" fill="#ff4d4d" opacity="0.55" filter="url(#gl)" style="animation:scan 3.2s linear infinite"/>
</g>

<circle cx="{CX}" cy="{CY}" r="{R}" fill="none" stroke="#e01e1e" stroke-width="3"
        filter="url(#gl)" style="animation:ring 2.8s ease-in-out infinite"/>
<circle cx="{CX}" cy="{CY}" r="{R-6}" fill="none" stroke="#5a0000" stroke-width="1" opacity="0.7"/>
</svg>'''

with open(OUT, "w", encoding="utf-8") as f:
    f.write(svg)
print(f"avatar.svg regenerado desde github.com/{USER}.png ({len(raw)} bytes de foto)")
