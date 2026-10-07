"""SharpCharts brand + post templates. Each function returns a full HTML page."""
from html import escape

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
.frame.story{padding:230px 72px 270px}
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


def page(inner, size="feed", tag="", source="", note=""):
    frame_cls = "frame story" if size == "story" else "frame"
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


def big_stat(title_html, subtitle, number, number_label, context_rows, tag, source, size="feed", color="var(--green)"):
    ctx = "".join(f'''<div style="display:flex;justify-content:space-between;align-items:center;padding:22px 0;border-bottom:2px solid var(--line);font-size:32px">
       <span class="m">{escape(k)}</span><span class="cond" style="font-size:46px;font-weight:700">{v}</span></div>''' for k, v in context_rows)
    inner = f'''<h1>{title_html}</h1><div class="sub">{subtitle}</div>
<div class="body"><div style="text-align:center;padding:10px 0 30px">
  <div class="cond" style="font-size:300px;font-weight:800;line-height:.9;color:{color};text-shadow:0 0 60px rgba(43,255,136,.25)">{number}</div>
  <div style="font-size:32px;font-weight:600;letter-spacing:3px;text-transform:uppercase;margin-top:8px">{number_label}</div></div>
  <div>{ctx}</div></div>'''
    return page(inner, size, tag=tag, source=source)


def bar_ranking(title_html, subtitle, rows, tag, source, size="feed", note="", scale=None, diverging=True):
    """rows: list of dict(abbr,color,name,value,value_label,record). Diverging bars around 0,
    or left-anchored bars when diverging=False (all-positive data like usage share)."""
    scale = scale or max(abs(r["value"]) for r in rows) or 1
    row_h = 66 if size == "feed" else 80
    html_rows = []
    for r in rows:
        pct = abs(r["value"]) / scale * (50 if diverging else 100)
        pos = r["value"] >= 0
        if not diverging:
            pct = min(pct, 100)
        left = "50%" if diverging else "0"
        bar_style = (f"left:{left};width:{pct}%;background:linear-gradient(90deg,rgba(43,255,136,.55),var(--green))" if pos else
                     f"right:50%;width:{pct}%;background:linear-gradient(270deg,rgba(255,77,94,.55),var(--red))")
        html_rows.append(f'''<div style="display:flex;align-items:center;gap:18px;height:{row_h}px">
  {chip(r["abbr"], r["color"], 54, 25)}
  <div style="width:250px"><div style="font-size:27px;font-weight:700">{escape(r["name"])}</div>
     <div class="m" style="font-size:20px">{escape(r.get("record",""))}</div></div>
  <div style="flex:1;position:relative;height:30px;background:var(--panel);border-radius:6px">
     {'<div style="position:absolute;top:-6px;bottom:-6px;left:50%;width:2px;background:var(--line)"></div>' if diverging else ''}
     <div style="position:absolute;top:0;bottom:0;border-radius:6px;{bar_style}"></div></div>
  <div class="cond {'g' if pos else 'r'}" style="width:110px;text-align:right;font-size:38px;font-weight:800">{escape(r["value_label"])}</div></div>''')
    inner = f'''<h1>{title_html}</h1><div class="sub">{subtitle}</div>
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


def matchup(away, home, line_info, stat_rows, tag, source, size="feed", note=""):
    """away/home: dict(abbr,name,color). line_info: list of (label, value). stat_rows: (label, away_val, home_val, better)."""
    def side(t, label):
        return f'''<div style="flex:1;display:flex;flex-direction:column;align-items:center;gap:14px">
  {chip(t["abbr"], t["color"], 170, 72)}
  <div class="cond" style="font-size:52px;font-weight:800;text-transform:uppercase">{escape(t["name"])}</div>
  <div class="m" style="font-size:22px;letter-spacing:3px;text-transform:uppercase">{label}</div></div>'''
    lines = "".join(f'''<div style="flex:1;text-align:center;padding:18px 8px">
   <div class="m" style="font-size:20px;letter-spacing:2px;text-transform:uppercase">{escape(k)}</div>
   <div class="cond" style="font-size:50px;font-weight:800;margin-top:4px">{escape(v)}</div></div>''' for k, v in line_info)
    rows = "".join(f'''<div style="display:flex;align-items:center;padding:16px 0;border-bottom:2px solid var(--line)">
   <div class="cond" style="flex:1;text-align:left;font-size:44px;font-weight:800;{'color:var(--green)' if b=='away' else ''}">{escape(a)}</div>
   <div class="m" style="flex:1.3;text-align:center;font-size:22px;letter-spacing:2px;text-transform:uppercase;font-weight:600">{escape(lbl)}</div>
   <div class="cond" style="flex:1;text-align:right;font-size:44px;font-weight:800;{'color:var(--green)' if b=='home' else ''}">{escape(h)}</div></div>'''
                   for lbl, a, h, b in stat_rows)
    inner = f'''<div class="body" style="gap:30px">
 <div style="display:flex;align-items:center">{side(away,"Away")}
   <div class="cond m" style="font-size:60px;font-weight:800">@</div>{side(home,"Home")}</div>
 <div style="display:flex;background:var(--panel);border:2px solid var(--line);border-radius:20px">{lines}</div>
 <div>{rows}</div></div>'''
    return page(inner, size, tag=tag, source=source, note=note)


def _rank(team):
    """Small '#7' label when a (abbr, color, rank) tuple carries a ranking."""
    rank = team[2] if len(team) > 2 else None
    return f'<span class="cond g" style="font-size:24px;font-weight:800;width:36px;text-align:right">#{rank}</span>' if rank else (
        '<span style="width:36px"></span>' if len(team) > 2 else "")


def slate(week, rows, tag, source, size="feed", note="", title_html=None,
          subtitle="Every game · spread &amp; total · swipe for breakdowns →"):
    """Every game of the week with spread + total. rows: dict(kick, away, home, spread, total, fav_home)."""
    n = len(rows)
    row_h = min(64, int((760 if size == "feed" else 1060) / max(n, 1)))
    chip_sz = min(46, row_h - 12)
    head = '''<div style="display:flex;align-items:center;padding:0 0 10px;font-size:20px;letter-spacing:2px;text-transform:uppercase;font-weight:600" class="m">
  <div style="width:170px">Kickoff (ET)</div><div style="flex:1">Matchup</div>
  <div style="width:190px;text-align:right">Spread</div><div style="width:120px;text-align:right">Total</div></div>'''
    body = []
    for r in rows:
        body.append(f'''<div style="display:flex;align-items:center;height:{row_h}px;border-top:2px solid var(--line)">
  <div class="m" style="width:170px;font-size:22px;font-weight:600">{escape(r["kick"])}</div>
  <div style="flex:1;display:flex;align-items:center;gap:10px">
    {_rank(r["away"])}{chip(r["away"][0], r["away"][1], chip_sz, int(chip_sz*.42))}<span class="m cond" style="font-size:28px;font-weight:700">@</span>
    {_rank(r["home"])}{chip(r["home"][0], r["home"][1], chip_sz, int(chip_sz*.42))}</div>
  <div class="cond" style="width:190px;text-align:right;font-size:36px;font-weight:800">{escape(r["spread"])}</div>
  <div class="cond g" style="width:120px;text-align:right;font-size:36px;font-weight:800">{escape(r["total"])}</div></div>''')
    title_html = title_html or f"Week {week}<br><em>betting slate</em>"
    inner = f'''<h1 style="font-size:96px">{title_html}</h1>
<div class="sub" style="font-size:26px">{subtitle}</div>
<div class="body" style="justify-content:flex-start;margin-top:26px">{head}{''.join(body)}</div>'''
    return page(inner, size, tag=tag, source=source, note=note)


def game_blocks(title_html, subtitle, games, tag, source, size="feed", note=""):
    """Stacked game cards (any sport). games: dict(kick, headline, total,
    away/home=dict(abbr,color,name,line,detail))."""
    n = max(len(games), 1)
    avail = 700 if size == "feed" else 1000
    block_h = min(240, int(avail / n) - 14)
    big = block_h >= 190
    chip_sz = 62 if big else 50

    def side(t):
        return f'''<div style="display:flex;align-items:center;gap:16px;height:{chip_sz + 8}px">
      {chip(t["abbr"], t["color"], chip_sz, int(chip_sz * .38))}
      <div style="flex:1;min-width:0"><div style="font-size:{28 if big else 24}px;font-weight:700;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{escape(t["name"])}</div>
        <div class="m" style="font-size:{20 if big else 18}px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{escape(t.get("detail", ""))}</div></div>
      <div class="cond" style="font-size:{44 if big else 38}px;font-weight:800;text-align:right;width:130px">{escape(t.get("line", ""))}</div></div>'''
    blocks = "".join(f'''<div style="background:var(--panel);border:2px solid var(--line);border-radius:20px;padding:{14 if big else 10}px 22px;display:flex;flex-direction:column;justify-content:center;gap:6px;height:{block_h}px">
    <div style="display:flex;justify-content:space-between;font-size:19px;letter-spacing:2px;text-transform:uppercase;font-weight:600">
      <span class="m">{escape(g["kick"])} · <span style="color:var(--text)">O/U {escape(g.get("total", "—"))}</span></span><span class="g">{escape(g.get("headline", ""))}</span></div>
    {side(g["away"])}{side(g["home"])}</div>''' for g in games)
    inner = f'''<h1 style="font-size:92px">{title_html}</h1><div class="sub" style="font-size:26px">{subtitle}</div>
<div class="body" style="justify-content:flex-start;gap:14px;margin-top:24px">{blocks}</div>'''
    return page(inner, size, tag=tag, source=source, note=note)
