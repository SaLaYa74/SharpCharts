"""SharpCharts brand + post templates. Each function returns a full HTML page."""
import re
from html import escape

from .helmets import helmet

HANDLE = "@sharp_charts"

BRAND_CSS = """
:root{
  --bg:#0A0F1C; --panel:#111A2C; --panel2:#16213A; --line:#22304D;
  --text:#F2F5FA; --muted:#8C98B0; --green:#2BFF88; --red:#FF4D5E; --amber:#FFC23D;
}
*{box-sizing:border-box;margin:0;padding:0}
html,body{width:100%;height:100%}
body{background:var(--bg);color:var(--text);font-family:Inter,"Helvetica Neue",Arial,sans-serif;
  -webkit-font-smoothing:antialiased;overflow:hidden}
.frame{position:relative;width:100%;height:100%;display:flex;flex-direction:column;padding:64px 72px 56px;
  background:
    radial-gradient(900px 600px at 100% 0%, rgba(43,255,136,.10), transparent 60%),
    radial-gradient(700px 500px at 0% 100%, rgba(64,120,255,.10), transparent 60%),
    var(--bg)}
.frame.story{padding:200px 64px 240px}
.frame.reel{padding:200px 150px 380px 72px}
.grid{position:absolute;inset:0;pointer-events:none;opacity:.35;
  background-image:linear-gradient(var(--line) 1px,transparent 1px),linear-gradient(90deg,var(--line) 1px,transparent 1px);
  background-size:54px 54px;mask-image:linear-gradient(180deg,rgba(0,0,0,.6),transparent 45%)}
.cond{font-family:"Barlow Condensed","Arial Narrow",sans-serif}
.top{display:flex;align-items:center;justify-content:space-between;position:relative}
.brand{display:flex;align-items:center;gap:14px;font-weight:700;font-size:26px;letter-spacing:.3px}
.brand svg{width:46px;height:46px}
.pill{font-family:"Barlow Condensed";font-weight:700;font-size:26px;letter-spacing:2px;text-transform:uppercase;
  padding:8px 18px;border:2px solid var(--green);color:var(--green);border-radius:999px}
h1{font-family:"Barlow Condensed";font-weight:800;font-size:104px;line-height:.92;text-transform:uppercase;
  letter-spacing:-.5px;margin-top:44px;position:relative}
h1 em{font-style:normal;color:var(--green)}
.sub{font-size:30px;color:var(--muted);margin-top:18px;line-height:1.35;position:relative}
.body{flex:1;display:flex;flex-direction:column;justify-content:center;position:relative;min-height:0}
.foot{display:flex;justify-content:space-between;align-items:flex-end;font-size:20px;color:var(--muted);
  border-top:2px solid var(--line);padding-top:20px;position:relative;line-height:1.4}
.foot b{color:var(--text);font-weight:600}
.chip{display:inline-flex;align-items:center;justify-content:center;font-family:"Barlow Condensed";font-weight:800;
  color:#fff;border-radius:12px;text-shadow:0 1px 2px rgba(0,0,0,.4)}
.g{color:var(--green)} .r{color:var(--red)} .m{color:var(--muted)}
"""

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
         '<link href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@600;700;800'
         '&family=Inter:wght@400;500;600;700;800&display=block" rel="stylesheet">')


def logo_svg(size=46, bg=True):
    rect = '<rect width="100" height="100" rx="24" fill="#111A2C" stroke="#2BFF88" stroke-width="4"/>' if bg else ""
    return f'''<svg width="{size}" height="{size}" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">{rect}
  <g stroke="#22304D" stroke-width="3"><line x1="22" y1="78" x2="78" y2="78"/></g>
  <rect x="24" y="56" width="10" height="22" rx="2" fill="#2BFF88" opacity=".35"/>
  <rect x="40" y="46" width="10" height="32" rx="2" fill="#2BFF88" opacity=".5"/>
  <rect x="56" y="60" width="10" height="18" rx="2" fill="#2BFF88" opacity=".35"/>
  <polyline points="20,64 38,44 54,56 80,24" fill="none" stroke="#2BFF88" stroke-width="7" stroke-linecap="round" stroke-linejoin="round"/>
  <polygon points="84,18 68,22 80,34" fill="#2BFF88"/></svg>'''


def mascot_svg(size=64):
    """Original fox mascot: rising-chart tail (ties to the logo) + analyst glasses."""
    return f'''<svg width="{size}" height="{size}" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
  <polyline points="112,176 138,146 156,158 186,110" fill="none" stroke="#2BFF88" stroke-width="12" stroke-linecap="round" stroke-linejoin="round"/>
  <polygon points="196,94 172,103 189,121" fill="#2BFF88"/>
  <polygon points="36,30 70,82 20,94" fill="#FF7A2F"/><polygon points="40,46 60,80 32,86" fill="#7A2E12"/>
  <polygon points="144,30 110,82 160,94" fill="#FF7A2F"/><polygon points="140,46 120,80 148,86" fill="#7A2E12"/>
  <polygon points="16,88 164,88 90,176" fill="#FF7A2F"/>
  <polygon points="16,90 90,176 56,122" fill="#FFF4EA"/><polygon points="164,90 90,176 124,122" fill="#FFF4EA"/>
  <circle cx="64" cy="116" r="17" fill="rgba(255,255,255,.18)" stroke="#0A0F1C" stroke-width="6"/>
  <circle cx="116" cy="116" r="17" fill="rgba(255,255,255,.18)" stroke="#0A0F1C" stroke-width="6"/>
  <line x1="81" y1="114" x2="99" y2="114" stroke="#0A0F1C" stroke-width="6"/>
  <path d="M56 119 q8 -8 16 0" fill="none" stroke="#0A0F1C" stroke-width="5" stroke-linecap="round"/>
  <path d="M108 119 q8 -8 16 0" fill="none" stroke="#0A0F1C" stroke-width="5" stroke-linecap="round"/>
  <ellipse cx="90" cy="164" rx="9" ry="7" fill="#0A0F1C"/></svg>'''


# Stories: scale the main content up until it fills the screen (inside Instagram's safe zones),
# so short content (e.g. one MLB game) never leaves half the screen empty.
FIT_JS = """<script>(function(){
 var b=document.querySelector('.frame.story .body'); if(!b) return;
 var w=document.createElement('div'); while(b.firstChild) w.appendChild(b.firstChild); b.appendChild(w);
 w.style.display='flex'; w.style.flexDirection='column'; w.style.gap=getComputedStyle(b).gap;
 b.style.justifyContent='center';
 var z=Math.min(2.0, b.clientHeight / w.scrollHeight * 0.96);
 if(z>1.03){ w.style.zoom=z; w.style.width=(100/z)+'%'; }
})();</script>"""


def page(inner, size="feed", tag="", source="", note=""):
    frame_cls = {"story": "frame story", "reel": "frame reel"}.get(size, "frame")
    note_html = f"<div>{note}</div>" if note else ""
    return f'''<!doctype html><html><head><meta charset="utf-8">{FONTS}<style>{BRAND_CSS}</style></head>
<body><div class="{frame_cls}"><div class="grid"></div>
<div class="top"><div class="brand">{logo_svg()}<span>{HANDLE}</span></div>
<div style="display:flex;align-items:center;gap:16px">{f'<div class="pill">{escape(tag)}</div>' if tag else ''}{mascot_svg(68)}</div></div>
{inner}
<div class="foot"><div>{note_html}<div>Data: <b>{escape(source)}</b></div></div><div style="text-align:right">21+ · Gamble responsibly<br>1-800-GAMBLER</div></div>
</div></body></html>'''


def chip(abbr, color, size=64, font=30):
    return f'<span class="chip" style="background:{color};width:{size}px;height:{size}px;font-size:{font}px">{escape(abbr)}</span>'


# ---------------- templates ----------------

def profile_pic():
    """Icon-only mark sized to survive Instagram's circular crop."""
    return f'''<!doctype html><html><head><meta charset="utf-8">{FONTS}<style>{BRAND_CSS}
body{{display:flex;align-items:center;justify-content:center;
  background:radial-gradient(circle at 50% 45%, #16264a 0%, #0A0F1C 68%)}}
</style></head><body>{logo_svg(700, bg=False)}</body></html>'''


def wordmark():
    """Logo + wordmark for banners, TikTok/X headers, watermark use."""
    return f'''<!doctype html><html><head><meta charset="utf-8">{FONTS}<style>{BRAND_CSS}
body{{display:flex;align-items:center;justify-content:center;
  background:radial-gradient(circle at 50% 40%, #13213b 0%, #0A0F1C 70%)}}
.wrap{{display:flex;flex-direction:column;align-items:center;gap:26px}}
.word{{font-family:"Barlow Condensed";font-weight:800;font-size:150px;line-height:.85;text-align:center;letter-spacing:1px}}
</style></head><body><div class="wrap">{logo_svg(440, bg=False)}
<div class="word">SHARP<span class="g">CHARTS</span></div></div></body></html>'''


def intro_post(size="feed"):
    items = [
        ("ATS + O/U trends", "Who's covering, who isn't, and by how much"),
        ("League splits", "Favorites vs. dogs, home vs. away, overs vs. unders"),
        ("Matchup cards", "Every big game, broken down before kickoff"),
        ("Weekly receipts", "We track how our highlighted trends actually hit"),
    ]
    rows = "".join(f'''<div style="display:flex;gap:26px;align-items:flex-start;padding:26px 0;border-bottom:2px solid var(--line)">
      <div class="cond g" style="font-size:54px;font-weight:800;width:70px">0{i+1}</div>
      <div><div style="font-size:38px;font-weight:700">{t}</div><div class="m" style="font-size:27px;margin-top:6px">{d}</div></div></div>'''
                   for i, (t, d) in enumerate(items))
    inner = f'''<h1>Data over<br><em>hunches.</em></h1>
<div class="sub">Clean, verified betting stats &amp; trends. No locks, no hype, just numbers.</div>
<div class="body">{rows}</div>'''
    return page(inner, size, tag="Welcome", source="nflverse · ESPN · verified before posting",
                note="Follow for daily NFL · NBA · MLB charts")


def _head(title_html, subtitle, hook=None):
    if not hook:
        return f'<h1>{title_html}</h1><div class="sub">{subtitle}</div>'
    if not title_html:
        em = ' style="color:var(--red)"' if len(hook) > 2 and hook[2] == "red" else ""
        return f'<h1 style="font-size:96px;line-height:.93;margin-top:30px">{escape(hook[0])}<br><em{em}>{escape(hook[1])}</em></h1>'
    plain = re.sub(r"<[^>]+>", " ", title_html).replace("&amp;", "&")
    plain = escape(re.sub(r"\s+", " ", plain).strip())
    em = ' style="color:var(--red)"' if len(hook) > 2 and hook[2] == "red" else ""
    return (f'<h1 style="font-size:96px;line-height:.93;margin-top:30px">{escape(hook[0])}<br><em{em}>{escape(hook[1])}</em></h1>'
            f'<div class="sub" style="font-size:30px;margin-top:14px"><b style="color:var(--text)">{plain}</b> · {subtitle}</div>')


def big_stat(title_html, subtitle, number, number_label, context_rows, tag, source, size="feed", color="var(--green)", p=1.0, hook=None):
    ctx = "".join(f'''<div style="display:flex;justify-content:space-between;align-items:center;padding:22px 0;border-bottom:2px solid var(--line);font-size:32px">
       <span class="m">{escape(k)}</span><span class="cond" style="font-size:46px;font-weight:700">{v}</span></div>''' for k, v in context_rows)
    inner = f'''{_head(title_html, subtitle, hook)}
<div class="body"><div style="text-align:center;padding:10px 0 30px">
  <div class="cond" style="font-size:300px;font-weight:800;line-height:.9;color:{color};text-shadow:0 0 60px rgba(43,255,136,.25);opacity:{min(1, p * 1.4):.2f};transform:scale({0.55 + 0.45 * p:.3f})">{number}</div>
  <div style="font-size:32px;font-weight:600;letter-spacing:3px;text-transform:uppercase;margin-top:8px">{number_label}</div></div>
  <div>{ctx}</div></div>'''
    return page(inner, size, tag=tag, source=source)


def bar_ranking(title_html, subtitle, rows, tag, source, size="feed", note="", scale=None, diverging=True, p=1.0, hook=None,
                glance=False):
    """rows: list of dict(abbr,color,name,value,value_label,record). Diverging bars around 0,
    or left-anchored bars when diverging=False (all-positive data like usage share)."""
    scale = scale or max(abs(r["value"]) for r in rows) or 1
    row_h = 104 if glance else {"feed": 66, "story": 80, "reel": 82}.get(size, 66)
    name_px, detail_px, value_px, chip_px = (36, 22, 54, 66) if glance else (27, 20, 38, 54)
    html_rows = []
    for r in rows:
        pct = abs(r["value"]) / scale * (50 if diverging else 100) * p
        pos = r["value"] >= 0
        if not diverging:
            pct = min(pct, 100)
        left = "50%" if diverging else "0"
        bar_style = (f"left:{left};width:{pct}%;background:linear-gradient(90deg,rgba(43,255,136,.55),var(--green))" if pos else
                     f"right:50%;width:{pct}%;background:linear-gradient(270deg,rgba(255,77,94,.55),var(--red))")
        html_rows.append(f'''<div style="display:flex;align-items:center;gap:18px;height:{row_h}px">
  {_row_badge(r["abbr"], r["color"], chip_px)}
  <div style="width:{330 if glance else 250}px"><div style="font-size:{name_px}px;font-weight:700;line-height:1.1">{escape(r["name"])}</div>
     <div class="m" style="font-size:{detail_px}px">{escape(r.get("record",""))}</div></div>
  <div style="flex:1;position:relative;height:{44 if glance else 30}px;background:var(--panel);border-radius:8px">
     {'<div style="position:absolute;top:-6px;bottom:-6px;left:50%;width:2px;background:var(--line)"></div>' if diverging else ''}
     <div style="position:absolute;top:0;bottom:0;border-radius:6px;{bar_style}"></div></div>
  <div class="cond {'g' if pos else 'r'}" style="width:{130 if glance else 110}px;text-align:right;font-size:{value_px}px;font-weight:800;opacity:{min(1, p * 1.25):.2f}">{escape(r["value_label"])}</div></div>''')
    inner = f'''{_head(title_html, subtitle, hook)}
<div class="body" style="gap:2px">{''.join(html_rows)}</div>'''
    return page(inner, size, tag=tag, source=source, note=note)


def splits(title_html, subtitle, items, tag, source, size="feed", note=""):
    """items: list of dict(label, left=(name,count), right=(name,count))."""
    blocks = []
    pad = 14 if size == "feed" else 30
    for it in items:
        (ln, lc), (rn, rc) = it["left"], it["right"]
        tot = lc + rc or 1
        lp = round(lc / tot * 100)
        lead_left = lc >= rc
        blocks.append(f'''<div style="padding:{pad}px 0;border-bottom:2px solid var(--line)">
  <div class="m" style="font-size:24px;letter-spacing:3px;text-transform:uppercase;font-weight:600;margin-bottom:6px">{escape(it["label"])}</div>
  <div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:8px">
    <div><span class="cond" style="font-size:54px;font-weight:800;{'color:var(--green)' if lead_left else ''}">{lc}</span>
         <span style="font-size:28px;font-weight:600;margin-left:10px">{escape(ln)}</span></div>
    <div><span style="font-size:28px;font-weight:600;margin-right:10px">{escape(rn)}</span>
         <span class="cond" style="font-size:54px;font-weight:800;{'' if lead_left else 'color:var(--green)'}">{rc}</span></div></div>
  <div style="display:flex;height:22px;border-radius:999px;overflow:hidden;background:var(--panel)">
    <div style="width:{lp}%;background:{'var(--green)' if lead_left else '#3A4A6B'}"></div>
    <div style="flex:1;background:{'#3A4A6B' if lead_left else 'var(--green)'}"></div></div>
  <div style="display:flex;justify-content:space-between;font-size:21px;margin-top:6px" class="m"><span>{lp}%</span><span>{100-lp}%</span></div></div>''')
    inner = f'''<h1>{title_html}</h1><div class="sub">{subtitle}</div>
<div class="body">{''.join(blocks)}</div>'''
    return page(inner, size, tag=tag, source=source, note=note)


def _dots(record, k=1.0, over_under=False):
    """'4-1-0' → five dots: wins green, losses red, pushes grey (O/U: overs gold, unders slate)."""
    parts = [int(x) for x in record.split("-")] + [0, 0]
    w, l, p = parts[0], parts[1], parts[2]
    c_w, c_l = ("var(--amber)", "#5B6B8C") if over_under else ("var(--green)", "var(--red)")
    sz = int(38 * k)
    dot = lambda c: f'<span style="display:inline-block;width:{sz}px;height:{sz}px;border-radius:50%;background:{c};margin:0 {int(4 * k)}px"></span>'
    return "".join([dot(c_w)] * w + [dot(c_l)] * l + [dot("#8C98B0")] * p)


def matchup(away, home, line_info, stat_rows, tag, source, size="feed", note=""):
    """Visual-first card: helmets face off, one big spread, records as colored dots."""
    k = 1.3 if size == "story" else 1.0
    stats = {lbl: (a, h) for lbl, a, h, _ in stat_rows}
    spread = dict(line_info).get("Spread", "")
    total = dict(line_info).get("Total", "")

    def team(t, facing):
        return f'''<div style="flex:1;display:flex;flex-direction:column;align-items:center;gap:{int(8 * k)}px">
  {helmet(t["abbr"], int(330 * k), facing)}
  <div class="cond" style="font-size:{int(58 * k)}px;font-weight:800;text-transform:uppercase;line-height:1">{escape(t["name"])}</div>
  <div class="m" style="font-size:{int(26 * k)}px;font-weight:600">{escape(stats.get("Record", ("", ""))[0 if facing == "right" else 1])}</div></div>'''

    def dots_row(label, key, ou=False):
        a, h = stats.get(key, ("0-0", "0-0"))
        return f'''<div style="display:flex;align-items:center;padding:{int(18 * k)}px 0;border-top:2px solid var(--line)">
   <div style="flex:1;text-align:left">{_dots(a, k, ou)}</div>
   <div class="m" style="width:{int(190 * k)}px;text-align:center;font-size:{int(22 * k)}px;letter-spacing:2px;text-transform:uppercase;font-weight:700">{label}</div>
   <div style="flex:1;text-align:right">{_dots(h, k, ou)}</div></div>'''
    inner = f'''<div class="body" style="gap:{int(22 * k)}px;justify-content:{'space-evenly' if size == 'story' else 'center'}">
 <div style="display:flex;align-items:flex-end">{team(away, "right")}
   <div class="cond m" style="font-size:{int(60 * k)}px;font-weight:800;padding-bottom:{int(70 * k)}px">@</div>{team(home, "left")}</div>
 <div style="text-align:center;background:var(--panel);border:2px solid var(--line);border-radius:24px;padding:{int(18 * k)}px">
   <div class="m" style="font-size:{int(22 * k)}px;letter-spacing:3px;text-transform:uppercase;font-weight:700">The line</div>
   <div class="cond" style="font-size:{int(96 * k)}px;font-weight:800;line-height:1">{escape(spread)}</div>
   <div class="m" style="font-size:{int(26 * k)}px;font-weight:600">Total {escape(total)}</div></div>
 <div>{dots_row("vs the spread", "ATS")}{dots_row("over / under", "Over / Under", ou=True)}
  <div class="m" style="text-align:center;font-size:{int(20 * k)}px;margin-top:{int(10 * k)}px">
   <span class="g">●</span> covered &nbsp; <span class="r">●</span> didn't &nbsp; <span style="color:var(--amber)">●</span> over &nbsp; <span style="color:#5B6B8C">●</span> under &nbsp; ● push · this season</div></div></div>'''
    return page(inner, size, tag=tag, source=source, note=note)


def _row_badge(abbr, color, px):
    from .helmets import H
    return helmet(abbr, int(px * 1.5), "right") if abbr in H else chip(abbr, color, px, int(px * .46))


def _badge(team, sz, facing):
    """NFL teams get a helmet; other sports (no helmet data) keep the color chip."""
    from .helmets import H
    if team[0] in H and len(team) < 3:
        lab = f'<span class="cond" style="font-size:{int(sz * .62)}px;font-weight:800">{escape(team[0])}</span>'
        hel = helmet(team[0], int(sz * 1.55), facing)
        return f'<span style="display:inline-flex;align-items:center;gap:6px">{hel if facing == "right" else lab}{lab if facing == "right" else hel}</span>'
    return chip(team[0], team[1], sz, int(sz * .42))


def _rank(team):
    """Small '#7' label when a (abbr, color, rank) tuple carries a ranking."""
    rank = team[2] if len(team) > 2 else None
    return f'<span class="cond g" style="font-size:24px;font-weight:800;width:36px;text-align:right">#{rank}</span>' if rank else (
        '<span style="width:36px"></span>' if len(team) > 2 else "")


def slate(week, rows, tag, source, size="feed", note="", title_html=None,
          subtitle="Every game · spread &amp; total · swipe for breakdowns →"):
    """Every game of the week with spread + total. rows: dict(kick, away, home, spread, total, fav_home)."""
    n = len(rows)
    if size == "story":                       # grow rows + text to fill the tall Story screen
        row_h = min(118, int(1000 / max(n, 1)))
        k = max(1.0, min(1.7, row_h / 64))
    else:
        row_h, k = min(64, int(760 / max(n, 1))), 1.0
    w = min(k, 1.3)                           # column widths grow less than text so nothing collides
    chip_sz = min(int(54 * k), row_h - 8)
    head = f'''<div style="display:flex;align-items:center;padding:0 0 10px;font-size:{int(20 * w)}px;letter-spacing:2px;text-transform:uppercase;font-weight:600" class="m">
  <div style="width:{int(170 * w)}px">Kickoff (ET)</div><div style="flex:1">Matchup</div>
  <div style="width:{int(200 * w)}px;text-align:right">Spread</div><div style="width:{int(120 * w)}px;text-align:right">Total</div></div>'''
    body = []
    for r in rows:
        body.append(f'''<div style="display:flex;align-items:center;height:{row_h}px;border-top:2px solid var(--line)">
  <div class="m" style="width:{int(170 * w)}px;font-size:{int(22 * w)}px;font-weight:600;white-space:nowrap">{escape(r["kick"])}</div>
  <div style="flex:1;display:flex;align-items:center;gap:{int(10 * w)}px">
    {_rank(r["away"])}{_badge(r["away"], chip_sz, "right")}<span class="m cond" style="font-size:{int(28 * w)}px;font-weight:700">@</span>
    {_rank(r["home"])}{_badge(r["home"], chip_sz, "left")}</div>
  <div class="cond" style="width:{int(200 * w)}px;text-align:right;font-size:{int(36 * k)}px;font-weight:800;white-space:nowrap">{escape(r["spread"])}</div>
  <div class="cond g" style="width:{int(120 * w)}px;text-align:right;font-size:{int(36 * k)}px;font-weight:800">{escape(r["total"])}</div></div>''')
    title_html = title_html or f"Week {week}<br><em>betting slate</em>"
    inner = f'''<h1 style="font-size:96px">{title_html}</h1>
<div class="sub" style="font-size:26px">{subtitle}</div>
<div class="body" style="justify-content:flex-start;margin-top:26px">{head}{''.join(body)}</div>'''
    return page(inner, size, tag=tag, source=source, note=note)


def _line_row(g, k):
    fav = g["away"] if g["away"].get("line") else g["home"]
    return (f'<div style="display:flex;justify-content:space-between;align-items:baseline;border-top:2px solid var(--line);'
            f'padding-top:{int(12 * k)}px;margin-top:{int(6 * k)}px"><span class="m" style="font-size:{int(18 * k)}px;'
            f'letter-spacing:2px;text-transform:uppercase;font-weight:600">Moneyline favorite</span>'
            f'<span class="cond" style="font-size:{int(46 * k)}px;font-weight:800;white-space:nowrap">{escape(fav["abbr"])} {escape(fav.get("line", ""))}</span></div>')


def game_blocks(title_html, subtitle, games, tag, source, size="feed", note=""):
    """Stacked game cards (any sport). games: dict(kick, headline, total,
    away/home=dict(abbr,color,name,line,detail))."""
    n = max(len(games), 1)
    story = size == "story"
    avail = 1180 if story else 700
    block_h = min(820 if story else 240, int(avail / n) - 16)
    k = max(1.0, min(3.1, block_h / 240)) if story else 1.0   # fewer games → bigger cards + text
    big = block_h >= 190
    chip_sz = int((62 if big else 50) * k)

    stacked = story and n <= 2      # few games: team rows without a line column, line gets its own big row
    if stacked:
        k = min(k, 2.0 if n == 1 else 1.2)
        chip_sz = int(62 * k)

    def side(t):
        if stacked:
            return f'''<div style="display:flex;align-items:center;gap:{int(14 * k)}px">
      {chip(t["abbr"], t["color"], chip_sz, int(chip_sz * .38))}
      <div style="flex:1;min-width:0"><div style="font-size:{int(28 * k)}px;font-weight:700;line-height:1">{escape(t["name"])}</div>
        <div class="m" style="font-size:{int(20 * min(k, 1.8))}px;line-height:1.3;margin-top:6px">{escape(t.get("detail", ""))}</div></div></div>'''
        return f'''<div style="display:flex;align-items:center;gap:{int(16 * k)}px;height:{chip_sz + 8}px">
      {chip(t["abbr"], t["color"], chip_sz, int(chip_sz * .38))}
      <div style="flex:1;min-width:0"><div style="font-size:{int((28 if big else 24) * k)}px;font-weight:700;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{escape(t["name"])}</div>
        <div class="m" style="font-size:{int((20 if big else 18) * min(k, 1.5))}px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{escape(t.get("detail", ""))}</div></div>
      <div class="cond" style="font-size:{int((44 if big else 38) * k)}px;font-weight:800;text-align:right;width:{int(130 * min(k, 1.9))}px">{escape(t.get("line", ""))}</div></div>'''
    blocks = "".join(f'''<div style="background:var(--panel);border:2px solid var(--line);border-radius:{int(20 * k)}px;padding:{int((14 if big else 10) * k)}px {int(22 * k)}px;display:flex;flex-direction:column;justify-content:{'space-evenly' if stacked else 'center'};gap:{int(6 * k)}px;{'min-' if stacked and n == 1 else ''}height:{block_h if not stacked or n == 1 else int(avail / n) - 24}px">
    <div style="display:flex;justify-content:space-between;font-size:{int(19 * min(k, 1.5))}px;letter-spacing:2px;text-transform:uppercase;font-weight:600">
      <span class="m">{escape(g["kick"])} · <span style="color:var(--text)">O/U {escape(g.get("total", "—"))}</span></span><span class="g">{escape(g.get("headline", ""))}</span></div>
    {side(g["away"])}{side(g["home"])}{_line_row(g, k) if stacked else ""}</div>''' for g in games)
    inner = f'''<h1 style="font-size:92px">{title_html}</h1><div class="sub" style="font-size:26px">{subtitle}</div>
<div class="body" style="justify-content:{'center' if story and n == 1 else 'flex-start'};gap:14px;margin-top:24px">{blocks}</div>'''
    return page(inner, size, tag=tag, source=source, note=note)


def reel_hook(line1, line2, tag, p=1.0):
    """Opening Reel frame: the hook, big and centered, with the mascot."""
    inner = f'''<div class="body" style="align-items:center;text-align:center;gap:40px">
  <div style="transform:scale({0.9 + 0.1 * p:.3f});opacity:{min(1, p * 1.5):.2f}">{mascot_svg(260)}</div>
  <h1 style="margin:0;font-size:122px;line-height:.95">{line1}<br><em>{line2}</em></h1>
  <div class="sub" style="font-size:34px">Watch the chart <span class="g">↓</span></div></div>'''
    return page(inner, "reel", tag=tag, source="verified before posting")


def reel_outro(tag):
    """Closing Reel frame: follow call-to-action."""
    inner = f'''<div class="body" style="align-items:center;text-align:center;gap:34px">
  {mascot_svg(340)}
  <h1 style="margin:0;font-size:110px">Follow<br><em>{HANDLE}</em></h1>
  <div class="sub" style="font-size:36px">Verified betting &amp; fantasy data, every day</div>
  <div class="pill" style="font-size:30px;margin-top:10px">Save this · send it to your group chat</div></div>'''
    return page(inner, "reel", tag=tag, source="nflverse · MLB · ESPN")


def one_stat(hook, number, label, who, color, tag, source, p=1.0, note="Digit's stat of the day 🦊"):
    """One giant number, readable in under a second. who = dict(abbr, color, name)."""
    c = "var(--green)" if color == "green" else "var(--red)"
    glow = "rgba(43,255,136,.30)" if color == "green" else "rgba(255,77,94,.30)"
    inner = f'''{_head("", "", hook) if hook else ""}
<div class="body" style="align-items:center;text-align:center;gap:26px">
  <div style="display:flex;align-items:center;gap:20px;opacity:{min(1, p * 2):.2f}">
    {chip(who["abbr"], who["color"], 84, 36)}
    <div class="cond" style="font-size:64px;font-weight:800;text-transform:uppercase">{escape(who["name"])}</div></div>
  <div class="cond" style="font-size:{int(250 + 170 * p)}px;font-weight:800;line-height:.85;color:{c};text-shadow:0 0 80px {glow}">{escape(number)}</div>
  <div style="font-size:40px;font-weight:700;letter-spacing:4px;text-transform:uppercase;opacity:{min(1, p * 1.5):.2f}">{escape(label)}</div></div>'''
    return page(inner, "reel", tag=tag, source=source, note=note)
