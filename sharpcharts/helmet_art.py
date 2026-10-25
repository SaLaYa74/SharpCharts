"""Team helmets drawn from the free-for-commercial-use helmet template (assets/helmet_template.png).
assets/make_helmet_parts.py splits it into shell / facemask / shine / outline masks; here each team gets
its own shell + facemask colors and its abbreviation where a logo would go (no team logos)."""
import base64
import io
import os
from html import escape

from PIL import Image

from .helmets import H
A = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets") + "/"
PARTS = {n: Image.open(f"{A}helmet_{n}.png").convert("L") for n in ("shell", "mask", "shine", "outline")}
W, Hh = PARTS["shell"].size
hexrgb = lambda c: tuple(int(c[i:i + 2], 16) for i in (1, 3, 5)) + (255,)
_cache = {}

def helmet_uri(abbr):
    if abbr not in _cache:
        shell, stripe, edge, mask, decal = H[abbr]
        out = Image.new("RGBA", (W, Hh), (0, 0, 0, 0))
        for part, col in (("outline", "#111827"), ("shell", shell), ("shine", "#FFFFFF"), ("mask", mask if mask.upper() not in (shell.upper(),) else "#9CA3AF")):
            out.paste(Image.new("RGBA", (W, Hh), hexrgb(col)), (0, 0), PARTS[part])
        buf = io.BytesIO(); out.save(buf, "PNG", optimize=True)
        _cache[abbr] = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()
    return _cache[abbr]

def helmet_img(abbr, size=200, facing="right"):
    shell, stripe, edge, mask, decal = H[abbr]
    flip = f' transform="translate({W} 0) scale(-1 1)"' if facing == "left" else ""
    tx = 150 if facing == "right" else W - 150
    fs = 112 if len(abbr) <= 2 else 94
    return f'''<svg width="{size}" height="{int(size * Hh / W)}" viewBox="0 0 {W} {Hh}" xmlns="http://www.w3.org/2000/svg">
 <g{flip}><image href="{helmet_uri(abbr)}" width="{W}" height="{Hh}"/></g>
 <text x="{tx}" y="205" text-anchor="middle" font-family="Barlow Condensed, Arial Narrow, sans-serif" font-weight="800"
  font-style="italic" font-size="{fs}" fill="{decal if decal.upper() != shell.upper() else '#FFFFFF'}" stroke="#111827" stroke-width="6" paint-order="stroke">{escape(abbr)}</text></svg>'''

