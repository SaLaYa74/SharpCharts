"""SharpCharts 'light' look (v2): warm white, big friendly type, chunky bright bars, an icon above each bar.
One idea per graphic. All artwork (icons, Penny) is original."""
from html import escape

from .templates import mascot_svg
from .helmets import badge, H as TEAM_COLORS

HANDLE = "@sharp_charts"
PALETTE = ["#EF4444", "#F97316", "#22C55E", "#3B82F6", "#A855F7", "#EAB308", "#14B8A6"]
FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
         '<link href="https://fonts.googleapis.com/css2?family=Baloo+2:wght@600;700;800&family=Nunito:wght@600;700;800&display=block" rel="stylesheet">')

CSS = """
*{box-sizing:border-box;margin:0;padding:0}
html,body{width:100%;height:100%}
body{background:#FBFCFF;color:#1F2937;font-family:Nunito,Arial,sans-serif;overflow:hidden;-webkit-font-smoothing:antialiased}
.f{width:100%;height:100%;display:flex;flex-direction:column;padding:70px 64px 60px;
   background:radial-gradient(1100px 700px at 50% 0%,#E8F1FF 0%,#FBFCFF 60%)}
.f.tall{padding:190px 60px 250px}
.t{font-family:"Baloo 2",Arial,sans-serif;font-weight:800;font-size:104px;line-height:.95;text-align:center;letter-spacing:-1px}
.t em{font-style:normal;color:var(--hl)}
.s{font-size:32px;font-weight:700;color:#6B7280;text-align:center;margin-top:16px}
.chart{flex:1;display:flex;align-items:flex-end;gap:22px;padding:0 6px;margin-top:20px;min-height:0;border-bottom:5px solid #1F2937}
.col{flex:1;display:flex;flex-direction:column;align-items:center;justify-content:flex-end;height:100%;min-width:0}
.bar{width:100%;border-radius:22px 22px 6px 6px;position:relative;display:flex;justify-content:center;
     box-shadow:inset 0 -14px 0 rgba(0,0,0,.08)}
.val{font-family:"Baloo 2";font-weight:800;color:#fff;font-size:54px;margin-top:10px;text-shadow:0 2px 0 rgba(0,0,0,.15);white-space:nowrap}
.val[data-n="6"],.val[data-n="7"]{font-size:38px}
.val.out{position:absolute;bottom:100%;margin:0 0 6px;color:#1F2937;text-shadow:none}
.icon{width:126px;height:126px;border-radius:50%;display:flex;align-items:center;justify-content:center;margin-bottom:12px;
      filter:drop-shadow(0 6px 0 rgba(0,0,0,.10))}
.labels{display:flex;gap:22px;padding:14px 6px 0}
.lab{flex:1;text-align:center;font-weight:800;font-size:30px;line-height:1.1;min-width:0}
.lab small{display:block;font-size:22px;color:#6B7280;font-weight:700;margin-top:4px}
.foot{display:flex;justify-content:space-between;align-items:center;margin-top:26px;font-size:24px;color:#6B7280;font-weight:700}
.qm{width:126px;height:126px;border-radius:50%;background:#F3F4F6;border:5px dashed #9CA3AF;display:flex;align-items:center;
    justify-content:center;font-family:"Baloo 2";font-weight:800;font-size:80px;color:#9CA3AF}
.tease{align-self:center;background:#1F2937;color:#fff;font-family:"Baloo 2";font-weight:800;font-size:40px;
       padding:6px 30px;border-radius:999px;margin:-60px 0 22px}
.brand{display:flex;align-items:center;gap:12px;font-family:"Baloo 2";font-weight:800;color:#1F2937;font-size:30px;letter-spacing:1px}
"""

# Simple original icons (viewBox 0 0 64 64)
ICONS = {
    "dog": '<path d="M14 26l6-12 8 8h8l8-8 6 12v14a14 14 0 0 1-14 14h-8A14 14 0 0 1 14 40z" fill="#FDBA74" stroke="#1F2937" stroke-width="3.5" stroke-linejoin="round"/><circle cx="25" cy="34" r="3" fill="#1F2937"/><circle cx="39" cy="34" r="3" fill="#1F2937"/><ellipse cx="32" cy="43" rx="5" ry="3.5" fill="#1F2937"/>',
    "crown": '<path d="M10 44l4-24 12 12 6-16 6 16 12-12 4 24z" fill="#FDE047" stroke="#1F2937" stroke-width="3.5" stroke-linejoin="round"/><rect x="10" y="44" width="44" height="8" rx="2" fill="#FBBF24" stroke="#1F2937" stroke-width="3.5"/>',
    "home": '<path d="M10 32L32 12l22 20" fill="none" stroke="#1F2937" stroke-width="3.5" stroke-linejoin="round" stroke-linecap="round"/><path d="M16 30v22h32V30" fill="#93C5FD" stroke="#1F2937" stroke-width="3.5"/><rect x="27" y="38" width="10" height="14" fill="#1F2937"/>',
    "plane": '<path d="M8 36l20-4 10-20 6 2-4 18 16 4v6l-18-2-6 14-6-2 2-12-20-2z" fill="#C4B5FD" stroke="#1F2937" stroke-width="3" stroke-linejoin="round"/>',
    "up": '<path d="M32 10l18 20H38v24H26V30H14z" fill="#86EFAC" stroke="#1F2937" stroke-width="3.5" stroke-linejoin="round"/>',
    "down": '<path d="M32 54L14 34h12V10h12v24h12z" fill="#FCA5A5" stroke="#1F2937" stroke-width="3.5" stroke-linejoin="round"/>',
    "egg": '<ellipse cx="32" cy="35" rx="17" ry="22" fill="#FFF7E6" stroke="#1F2937" stroke-width="3.5"/><ellipse cx="26" cy="27" rx="4" ry="6" fill="#fff"/>',
    "milk": '<path d="M22 14h20v8l6 8v24H16V30l6-8z" fill="#fff" stroke="#1F2937" stroke-width="3.5" stroke-linejoin="round"/><path d="M16 38h32v10H16z" fill="#60A5FA"/>',
    "beef": '<path d="M14 34c0-12 12-20 24-18s14 12 12 20-12 14-22 12-14-6-14-14z" fill="#F87171" stroke="#1F2937" stroke-width="3.5"/><ellipse cx="38" cy="30" rx="5" ry="4" fill="#fff"/>',
    "bread": '<path d="M12 30c0-10 10-14 20-14s20 4 20 14c0 4-3 5-5 5v15H17V35c-2 0-5-1-5-5z" fill="#F4B860" stroke="#1F2937" stroke-width="3.5" stroke-linejoin="round"/>',
    "coffee": '<path d="M14 24h30v16a12 12 0 0 1-12 12h-6a12 12 0 0 1-12-12z" fill="#fff" stroke="#1F2937" stroke-width="3.5"/><path d="M44 28h4a6 6 0 0 1 0 12h-4" fill="none" stroke="#1F2937" stroke-width="3.5"/><path d="M24 10c-3 4 3 6 0 10M32 10c-3 4 3 6 0 10" stroke="#9CA3AF" stroke-width="3" fill="none" stroke-linecap="round"/>',
    "bulb": '<path d="M32 10a16 16 0 0 0-9 29v7h18v-7a16 16 0 0 0-9-29z" fill="#FDE047" stroke="#1F2937" stroke-width="3.5"/><path d="M24 52h16" stroke="#1F2937" stroke-width="3.5" stroke-linecap="round"/>',
    "gas": '<rect x="14" y="12" width="24" height="40" rx="4" fill="#F87171" stroke="#1F2937" stroke-width="3.5"/><rect x="19" y="18" width="14" height="10" fill="#fff"/><path d="M38 24l8 6v16a4 4 0 0 1-8 0V36" fill="none" stroke="#1F2937" stroke-width="3.5" stroke-linecap="round"/>',
    "house": '<path d="M10 32L32 12l22 20" fill="none" stroke="#1F2937" stroke-width="3.5" stroke-linejoin="round" stroke-linecap="round"/><path d="M16 30v22h32V30" fill="#FDBA74" stroke="#1F2937" stroke-width="3.5"/><rect x="27" y="38" width="10" height="14" fill="#1F2937"/>',
    "pay": '<rect x="8" y="18" width="48" height="28" rx="5" fill="#86EFAC" stroke="#1F2937" stroke-width="3.5"/><circle cx="32" cy="32" r="7" fill="#fff" stroke="#1F2937" stroke-width="3"/><text x="32" y="36" text-anchor="middle" font-family="Arial" font-weight="900" font-size="11" fill="#1F2937">$</text>',
    "prices": '<path d="M12 14h22l18 18-20 20-20-18z" fill="#C4B5FD" stroke="#1F2937" stroke-width="3.5" stroke-linejoin="round"/><circle cx="22" cy="24" r="4" fill="#fff" stroke="#1F2937" stroke-width="3"/>',
    "rent": '<rect x="14" y="10" width="36" height="44" rx="3" fill="#93C5FD" stroke="#1F2937" stroke-width="3.5"/><g fill="#fff"><rect x="20" y="16" width="8" height="8"/><rect x="36" y="16" width="8" height="8"/><rect x="20" y="30" width="8" height="8"/><rect x="36" y="30" width="8" height="8"/></g><rect x="28" y="42" width="8" height="12" fill="#1F2937"/>',
    "cart": '<path d="M8 14h8l6 26h26l6-18H20" fill="none" stroke="#1F2937" stroke-width="3.5" stroke-linejoin="round" stroke-linecap="round"/><circle cx="26" cy="48" r="4" fill="#1F2937"/><circle cx="44" cy="48" r="4" fill="#1F2937"/><path d="M22 22h28l-4 12H25z" fill="#FCD34D"/>',
    "clock": '<circle cx="32" cy="32" r="22" fill="#fff" stroke="#1F2937" stroke-width="3.5"/><path d="M32 18v14l10 6" fill="none" stroke="#1F2937" stroke-width="3.5" stroke-linecap="round"/>',
}


def icon(name, px=126):
    """Team badge for an NFL abbreviation, otherwise one of the simple icons."""
    if name in TEAM_COLORS:
        from .helmet_art import helmet_img
        return f'<div style="width:{int(px * 1.38)}px;margin:0 -16px;display:flex;justify-content:center">{helmet_img(name, int(px * 1.38))}</div>'
    return f'<div style="width:{px}px;height:{px}px;border-radius:50%;background:#fff;border:5px solid #1F2937;display:flex;align-items:center;justify-content:center">' \
           f'<svg width="{int(px * .62)}" height="{int(px * .62)}" viewBox="0 0 64 64">{ICONS.get(name, ICONS["prices"])}</svg></div>'


def _page(body, tall, source):
    return f'''<!doctype html><html><head><meta charset="utf-8">{FONTS}<style>{CSS}</style></head>
<body><div class="f{' tall' if tall else ''}">{body}
<div class="foot"><div class="brand">{mascot_svg(54)}SHARP CHARTS</div><div style="text-align:right">Source: {escape(source)}<br>21+ · Gamble responsibly · 1-800-GAMBLER</div></div></div></body></html>'''


def bars(title, highlight, subtitle, items, source, tall=True, p=1.0, hl_color="#F97316", fmt=None,
         reveal=None, tease=None):
    """Big vertical bar chart. title may contain {hl} where the highlighted word goes.
    items: [dict(label, sub, value, icon, value_label?, color?)] — values must be >= 0.
    reveal: optional per-item progress (0 = still hidden behind a '?', 1 = fully grown) for countdown Reels.
    tease: optional pill above the title (e.g. 'Guess #1 before it shows')."""
    n = len(items)
    hi = max(i["value"] for i in items) or 1
    cols, labs = [], []
    for k, it in enumerate(items):
        color = it.get("color") or PALETTE[k % len(PALETTE)]
        if reveal is not None:
            p = reveal[k]
            if p <= 0:
                cols.append(f'''<div class="col"><div class="icon"><div class="qm">?</div></div>
  <div class="bar" style="height:7%;background:#E5E7EB;box-shadow:none"></div></div>''')
                labs.append(f'<div class="lab" style="color:#9CA3AF">#{k + 1}<small>&nbsp;</small></div>')
                continue
        h = max(3.0, it["value"] / hi * 100 * p)
        short = h < 16
        vl = it.get("value_label") or (fmt(it["value"]) if fmt else f'{it["value"]:g}')
        op = f"opacity:{min(1, p * 1.3):.2f}"
        above = f'<div class="val" style="color:#1F2937;text-shadow:none;margin:0 0 8px;{op}">{escape(vl)}</div>' if short else ""
        inside = "" if short else f'<div class="val" style="{op}">{escape(vl)}</div>'
        cols.append(f'''<div class="col"><div class="icon" style="opacity:{min(1, p * 1.6):.2f}">{icon(it.get("icon"))}</div>
  {above}<div class="bar" style="height:{h:.1f}%;background:{color}">{inside}</div></div>'''.replace('class="val"', f'class="val" data-n="{n}"'))
        sub = f'<small>{escape(it["sub"])}</small>' if it.get("sub") else ""
        labs.append(f'<div class="lab">{escape(it["label"])}{sub}</div>')
    t = escape(title).replace("{hl}", f"<em>{escape(highlight)}</em>")
    pill = (f'<div class="tease">{escape(tease)}</div>' if tease else
            '<div class="tease" style="visibility:hidden">&nbsp;</div>' if reveal is not None else "")   # no layout jump
    body = f'''{pill}<div class="t" style="--hl:{hl_color}">{t}</div><div class="s">{escape(subtitle)}</div>
<div class="chart" style="gap:{22 if n > 3 else 60}px">{''.join(cols)}</div><div class="labels" style="gap:{22 if n > 3 else 60}px">{''.join(labs)}</div>'''
    return _page(body, tall, source)


def line(title, highlight, subtitle, pts, fmt, source, color="#3B82F6", marker=None, tall=True, p=1.0, hl_color="#3B82F6"):
    """Light-theme trend line, drawn left→right; optional labeled reference point (e.g. 'a year ago')."""
    W, H, pl, pr, pt, pb = 900, 900, 30, 170, 90, 70
    vals = [v for _, v in pts]
    lo, hi = min(vals), max(vals)
    sp = (hi - lo) or 1
    lo, hi = lo - sp * .15, hi + sp * .2
    xs = [pl + i * (W - pl - pr) / (len(pts) - 1) for i in range(len(pts))]
    ys = [pt + (hi - v) / (hi - lo) * (H - pt - pb) for v in vals]
    n = max(2, int(round(p * (len(pts) - 1))) + 1)
    path = " ".join(f"{x:.1f},{y:.1f}" for x, y in zip(xs[:n], ys[:n]))
    area = f"{xs[0]:.1f},{H - pb} " + path + f" {xs[n - 1]:.1f},{H - pb}"
    ticks, seen = "", set()
    for i, (d, _) in enumerate(pts):
        if d.month == 1 and d.year not in seen:
            seen.add(d.year)
            ticks += f'<text x="{xs[i]:.0f}" y="{H - 20}" text-anchor="middle" font-family="Nunito" font-weight="800" font-size="30" fill="#6B7280">{d.year}</text>'
    mk = ""
    if marker and marker[0] < n:
        i, text = marker
        mk = (f'<line x1="{xs[i]:.1f}" y1="{ys[i]:.1f}" x2="{xs[i]:.1f}" y2="{H - pb}" stroke="#9CA3AF" stroke-width="3" stroke-dasharray="8 8"/>'
              f'<circle cx="{xs[i]:.1f}" cy="{ys[i]:.1f}" r="14" fill="#fff" stroke="#1F2937" stroke-width="5"/>'
              f'<text x="{xs[i]:.1f}" y="{ys[i] - 30:.1f}" text-anchor="middle" font-family="Baloo 2" font-weight="800" font-size="40" fill="#1F2937">{escape(text)}</text>')
    end = (f'<circle cx="{xs[n-1]:.1f}" cy="{ys[n-1]:.1f}" r="18" fill="{color}" stroke="#fff" stroke-width="5"/>'
           f'<text x="{xs[n-1] + 26:.1f}" y="{ys[n-1] + 20:.1f}" font-family="Baloo 2" font-weight="800" font-size="70" fill="{color}" opacity="{min(1, p * 1.3):.2f}">{escape(fmt(vals[n-1]))}</text>')
    svg = f'''<svg width="100%" viewBox="0 0 {W} {H}" style="overflow:visible">
 <polygon points="{area}" fill="{color}" opacity=".12"/>
 <line x1="{pl}" y1="{H - pb}" x2="{W - pr}" y2="{H - pb}" stroke="#1F2937" stroke-width="5"/>
 <polyline points="{path}" fill="none" stroke="{color}" stroke-width="12" stroke-linecap="round" stroke-linejoin="round"/>{mk}{end}{ticks}</svg>'''
    t = escape(title).replace("{hl}", f"<em>{escape(highlight)}</em>")
    body = f'''<div class="t" style="--hl:{hl_color}">{t}</div><div class="s">{escape(subtitle)}</div>
<div style="flex:1;display:flex;align-items:center;margin-top:20px">{svg}</div>'''
    return _page(body, tall, source)


def board(title, highlight, subtitle, rows, source, tall=True, p=1.0, hl_color="#3B82F6"):
    """'Find your team' board: every team on one screen, two columns, best → worst.
    rows: [dict(icon, label, sub, value_label, color)] in display order. Rows fade in top-down with p."""
    from .helmet_art import helmet_img
    n = len(rows)
    half = (n + 1) // 2
    cols = [rows[:half], rows[half:]]
    html_cols = []
    for c, part in enumerate(cols):
        cells = []
        for j, r in enumerate(part):
            k = c * half + j
            op = max(0.0, min(1.0, (p - k / n * 0.6) / 0.4))
            sub = f'<small>{escape(r["sub"])}</small>' if r.get("sub") else ""
            cells.append(f'''<div class="row" style="opacity:{op:.2f}"><div class="rk">{k + 1}</div>
  <div class="hm">{helmet_img(r["icon"], 78)}</div><div class="nm">{escape(r["label"])}{sub}</div>
  <div class="vl" style="color:{r.get("color", "#1F2937")}">{escape(r["value_label"])}</div></div>''')
        html_cols.append(f'<div class="bcol">{"".join(cells)}</div>')
    t = escape(title).replace("{hl}", f"<em>{escape(highlight)}</em>")
    css = """<style>.board{flex:1;display:flex;gap:26px;margin-top:26px;min-height:0}
.bcol{flex:1;display:flex;flex-direction:column;justify-content:space-between;min-width:0}
.row{display:flex;align-items:center;gap:8px;background:#fff;border-radius:16px;padding:2px 14px 2px 8px;
     box-shadow:0 3px 0 rgba(0,0,0,.06);height:6.05%}
.rk{width:34px;font-family:"Baloo 2";font-weight:800;font-size:26px;color:#9CA3AF;text-align:center}
.hm{width:78px;display:flex;justify-content:center}
.nm{flex:1;font-weight:800;font-size:29px;line-height:1;white-space:nowrap;overflow:hidden;min-width:0}
.nm small{display:block;font-size:19px;color:#6B7280;font-weight:700;margin-top:3px}
.vl{font-family:"Baloo 2";font-weight:800;font-size:38px;white-space:nowrap}</style>"""
    body = f'''{css}<div class="t" style="--hl:{hl_color}">{t}</div><div class="s">{escape(subtitle)}</div>
<div class="board">{"".join(html_cols)}</div>'''
    return _page(body, tall, source)
