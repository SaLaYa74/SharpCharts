"""One-off rivalry-week Reels (owner, Nov 25: "a post about USC versus UCLA and show the odds... with and without Ty
Dieffenbach, the UCLA quarterback... questionable to play").

The owner asked for the odds on this one, so it shows the market (the Oct 31 "no betting framing" rule otherwise
stands): what the line did, what the market and ESPN's model each give for the win, and UCLA's record by starting QB.
No picks, and the 21+ / 1-800-GAMBLER line prints because the source names the odds.

Every number has a second source or an exact recount:
  - Line: DraftKings via ESPN (open + now), checked against every book on Action Network (all within a point).
  - Win chances: DraftKings moneyline with the bookmaker margin removed; ESPN FPI from ESPN's matchup predictor.
  - QB splits: ESPN box scores game by game (starter = most pass attempts); each QB's summed passing line must equal
    his ESPN season stats, and the game results must add up to UCLA's ESPN record.
"""
import json
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from html import escape

from . import checks as C
from . import light as L
from .logos import logo_uri
from .posts import DataError, NoContent
from .v2 import _post

EVENT = "401858543"                    # USC at UCLA, Sat Nov 28, 2026 (Rose Bowl)
UCLA, USC = "26", "30"
TY, MADDEN, NICO = "5092275", "5142594", "4870799"
# Status line, word for word what's verified. Update if UCLA announces a decision before the post goes out.
STATUS = "Dieffenbach (hip) not ruled out"
STATUS_SHORT = "hip injury: not ruled out"
ESPN = "https://site.api.espn.com/apis/site/v2/sports/football/college-football"
ATHLETE = "https://site.web.api.espn.com/apis/common/v3/sports/football/college-football/athletes/{}/stats?season=2026"
ACTION = "https://api.actionnetwork.com/web/v2/scoreboard/ncaaf?bookIds=15,30,68,69,71,75,79&date=20261128&division=FBS"
OPENER_BOOK = "30"                     # Action Network's "open" line
RED, GREEN, INK, GRAY = "#DC2626", "#16A34A", "#1F2937", "#9CA3AF"


def _get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def _novig(home_ml, away_ml):
    """American moneylines -> (home %, away %) with the bookmaker margin removed."""
    imp = lambda ml: 100 / (ml + 100) if ml > 0 else -ml / (-ml + 100)
    h, a = imp(home_ml), imp(away_ml)
    return 100 * h / (h + a), 100 * a / (h + a)


def _line(rep):
    s = _get(f"{ESPN}/summary?event={EVENT}")
    pc = s["pickcenter"][0]
    rep.require("draft" in pc["provider"]["name"].lower(), "odds: DraftKings line on ESPN", pc["provider"]["name"])
    sp, ml = pc["pointSpread"], pc["moneyline"]
    num = lambda x: float(str(x).replace("+", ""))
    line = {"open": num(sp["away"]["open"]["line"]), "now": num(sp["away"]["close"]["line"]),        # USC (away) spread
            "ml_open": (num(ml["home"]["open"]["odds"]), num(ml["away"]["open"]["odds"])),
            "ml_now": (num(ml["home"]["close"]["odds"]), num(ml["away"]["close"]["odds"]))}
    rep.require(num(sp["home"]["close"]["line"]) == -line["now"], "odds: both sides of the spread match", f"{sp}")
    fpi = {t["id"] if "id" in t else k: float(t["gameProjection"])
           for k, t in (("home", s["predictor"]["homeTeam"]), ("away", s["predictor"]["awayTeam"]))}
    rep.require(abs(sum(fpi.values()) - 100) <= 1.0, "fpi: home + away add to 100%", f"{fpi}")
    line["fpi_ucla"], line["fpi_usc"] = fpi[UCLA], fpi[USC]
    comp = s["header"]["competitions"][0]
    line["kick"] = comp["date"]
    line["tv"] = next((b.get("media", {}).get("shortName") for b in s.get("broadcasts", []) if b.get("media")), "")
    # Second source: every book Action Network lists must sit within a point of DraftKings now. If Action Network
    # won't answer (it may block cloud servers), ESPN's own weekly betting-lines story (a different book) is the backup.
    try:
        an = _get(ACTION)
    except (urllib.error.URLError, ValueError) as e:
        alt = _espn_story_line()
        rep.require(alt is not None and abs(alt - line["now"]) <= 1.0, "odds: ESPN betting story within 1 point of DraftKings",
                    f"Action Network down ({type(e).__name__}); ESPN story says {alt}, DraftKings {line['now']}")
        line["books"], line["an_open"] = 1, None
        return line
    g = next((g for g in an.get("games", []) if {t.get("abbr") for t in g.get("teams", [])} >= {"USC", "UCLA"}), None)
    if not rep.require(g is not None, "odds: game found on Action Network", "missing"):
        raise DataError("Action Network doesn't list USC-UCLA")
    usc_side = "away" if line["now"] < 0 else "home"
    books = {}
    for bid, m in (g.get("markets") or {}).items():
        for o in m.get("event", {}).get("spread", []):
            if o.get("side") == "away":
                books[bid] = float(o["value"])
    current = {b: v for b, v in books.items() if b != OPENER_BOOK}
    rep.require(len(current) >= 3, "odds: at least 3 other books quote it", f"{len(current)} books")
    rep.require(all(abs(v - line["now"]) <= 1.0 for v in current.values()), "odds: every book within 1 point of DraftKings",
                f"DK {line['now']} vs {current}")
    if OPENER_BOOK in books:
        rep.expect(abs(books[OPENER_BOOK] - line["open"]) <= 1.5, "odds: Action Network's opener near DraftKings'",
                   f"{books[OPENER_BOOK]} vs {line['open']}")
    line["books"] = len(current)
    line["an_open"] = books.get(OPENER_BOOK)
    return line


STORY = "https://content.core.api.espn.com/v1/sports/news/50571004"     # ESPN "Top 25 betting lines", Week 13


def _espn_story_line():
    """USC's spread as printed in ESPN's Week 13 betting-lines story ('No. 15 USC -7 at No. 9 UCLA'), or None."""
    import html
    import re
    try:
        d = _get(STORY)
    except (urllib.error.URLError, ValueError):
        return None
    text = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", d["headlines"][0]["story"])))
    m = re.search(r"USC (-\d+(?:\.\d)?) at No\. \d+ UCLA", text)
    return float(m.group(1)) if m else None


def _games(tid):
    d = _get(f"{ESPN}/teams/{tid}/schedule?season=2026&seasontype=2")
    return [e["id"] for e in d["events"] if e["competitions"][0]["status"]["type"]["completed"]]


def _box(eid, tid):
    s = _get(f"{ESPN}/summary?event={eid}")
    comp = s["header"]["competitions"][0]
    me = next(c for c in comp["competitors"] if c["id"] == tid)
    op = next(c for c in comp["competitors"] if c["id"] != tid)
    qbs = {}
    for t in s["boxscore"]["players"]:
        if t["team"]["id"] != tid:
            continue
        for cat in t["statistics"]:
            if cat["name"] == "passing":
                for a in cat["athletes"]:
                    st = dict(zip(cat["keys"], a["stats"]))
                    c, att = (int(x) for x in st["completions/passingAttempts"].split("/"))
                    qbs[a["athlete"].get("id", a["athlete"]["displayName"])] = {
                        "cmp": c, "att": att, "yds": int(st["passingYards"]), "td": int(st["passingTouchdowns"]),
                        "int": int(st["interceptions"])}
    return {"date": comp["date"][:10], "pf": int(me["score"]), "pa": int(op["score"]), "qbs": qbs,
            "starter": max(qbs, key=lambda k: qbs[k]["att"]) if qbs else None}


def _season(aid):
    d = _get(ATHLETE.format(aid))
    cat = next(c for c in d["categories"] if c["name"] == "passing")
    row = next(s["stats"] for s in cat["statistics"] if s["season"]["year"] == 2026)
    v = dict(zip(cat["labels"], row))
    return {"cmp": int(v["CMP"]), "att": int(v["ATT"]), "yds": int(v["YDS"].replace(",", "")), "td": int(v["TD"]), "int": int(v["INT"])}


def _team_record(tid):
    t = _get(f"{ESPN}/teams/{tid}")["team"]
    return t["record"]["items"][0]["summary"]


def _splits(tid, rep, check_qbs=()):
    with ThreadPoolExecutor(6) as ex:
        games = list(ex.map(lambda e: _box(e, tid), _games(tid)))
    w = sum(g["pf"] > g["pa"] for g in games)
    rec = _team_record(tid)
    rep.require(f"{w}-{len(games) - w}" == rec, f"{tid}: game results add up to ESPN's record", f"{w}-{len(games) - w} vs {rec}")
    for aid in check_qbs:
        tot = {k: sum(g["qbs"].get(aid, {}).get(k, 0) for g in games) for k in ("cmp", "att", "yds", "td", "int")}
        rep.require(tot == _season(aid), f"{aid}: box scores add up to his ESPN season line", f"{tot}")
    return games


def _by_starter(games, aid):
    gs = [g for g in games if g["starter"] == aid]
    if not gs:
        return {"g": 0}
    w = sum(g["pf"] > g["pa"] for g in gs)
    return {"g": len(gs), "w": w, "l": len(gs) - w, "ppg": sum(g["pf"] for g in gs) / len(gs),
            "papg": sum(g["pa"] for g in gs) / len(gs)}


def split_bg(left, right, w=1080, h=1920, top=650, bottom=430, teeth=9, amp=46):
    """Rivalry background (owner, Nov 25: "half red half blue... a jagged line angled across the middle"): left team's
    color on the left, right team's on the right, split by a zigzag seam that leans from top-right to bottom-left."""
    pts = []
    for k in range(teeth + 1):
        y = h * k / teeth
        x = top + (bottom - top) * k / teeth + (amp if k % 2 else -amp) * (0 < k < teeth)
        pts.append((x, y))
    seam = " ".join(f"{x:.0f},{y:.0f}" for x, y in pts)
    return (f'<svg class="split" viewBox="0 0 {w} {h}" preserveAspectRatio="none">'
            f'<defs><radialGradient id="vg" cx="50%" cy="40%" r="75%"><stop offset="60%" stop-color="#000" stop-opacity="0"/>'
            f'<stop offset="100%" stop-color="#000" stop-opacity=".28"/></radialGradient></defs>'
            f'<rect width="{w}" height="{h}" fill="{right}"/>'
            f'<polygon points="0,0 {seam} 0,{h}" fill="{left}"/>'
            f'<polyline points="{seam}" fill="none" stroke="#FFD23F" stroke-width="12" stroke-linejoin="miter"/>'
            f'<rect width="{w}" height="{h}" fill="url(#vg)"/></svg>')


def card(title, hl, sub, usc, ucla, line, win, qbs, source, p=1.0):
    """USC-UCLA QB-swing card: teams, the line move, the two win chances, UCLA by starting QB. Sections fade in."""
    fade = lambda d: max(0.0, min(1.0, (p - d) / 0.15))
    css = """<style>
.qs{flex:1;display:flex;flex-direction:column;justify-content:center;gap:26px;margin-top:22px;min-height:0}
.tm{display:flex;align-items:center;justify-content:space-between}
.tm .t1{display:flex;align-items:center;gap:18px}.tm .t1.r{flex-direction:row-reverse;text-align:right}
.tm .lg{width:150px;height:150px;display:flex;align-items:center;justify-content:center}
.tm .lg img{filter:drop-shadow(0 6px 8px rgba(0,0,0,.2))}
.tm b{display:block;font-family:"Baloo 2";font-weight:800;font-size:54px;line-height:1}.tm small{font-size:30px;font-weight:800;color:#6B7280}
.vs{font-family:"Baloo 2";font-weight:800;font-size:52px;color:#9CA3AF}
.box{background:#fff;border-radius:26px;box-shadow:0 4px 0 rgba(0,0,0,.06);padding:20px 26px}
.cap{font-family:"Baloo 2";font-weight:800;font-size:28px;letter-spacing:2px;color:#6B7280}
.mv{display:flex;align-items:center;justify-content:center;gap:26px;margin-top:4px}
.mv .o{font-family:"Baloo 2";font-weight:800;font-size:64px;color:#9CA3AF;text-decoration:line-through;text-decoration-thickness:5px}
.mv .n{font-family:"Baloo 2";font-weight:800;font-size:96px;line-height:1;color:#1F2937}
.mv .a{font-size:60px;font-weight:900;color:#9CA3AF}
.pill{display:inline-block;background:#FDE047;border-radius:999px;padding:2px 22px;font-family:"Baloo 2";font-weight:800;font-size:32px}
.wr{display:grid;grid-template-columns:230px 1fr;align-items:center;gap:16px;margin-top:12px}
.wr .lb{font-weight:800;font-size:30px;line-height:1.05}
.sb{display:flex;height:68px;border-radius:16px;overflow:hidden;font-family:"Baloo 2";font-weight:800;font-size:38px;color:#fff}
.sb div{display:flex;align-items:center;padding:0 18px;white-space:nowrap}
.qr{display:grid;grid-template-columns:22px 1fr auto;align-items:center;gap:16px;margin-top:12px}
.qr i{width:22px;height:22px;border-radius:50%}
.qr .nm{font-weight:800;font-size:34px;line-height:1.05}.qr .nm small{display:block;font-size:24px;color:#6B7280}
.qr .st{font-family:"Baloo 2";font-weight:800;font-size:40px;text-align:right;line-height:1}
.qr .st small{display:block;font-family:Nunito;font-size:24px;color:#6B7280}
.f{position:relative;background:#2D68C4}
.f>*{position:relative;z-index:1}
.f>svg.split{position:absolute;inset:0;width:100%;height:100%;z-index:0}
.f>.t{color:#fff;text-shadow:0 4px 18px rgba(0,0,0,.35)}
.f>.t em{color:#FFD23F}
.f>.s{color:rgba(255,255,255,.92);text-shadow:0 2px 10px rgba(0,0,0,.35)}
.tm b{color:#fff;text-shadow:0 3px 12px rgba(0,0,0,.35)}.tm small{color:rgba(255,255,255,.85)}
.vs{color:rgba(255,255,255,.8)}
.tm .lg img{filter:drop-shadow(3px 0 0 #fff) drop-shadow(-3px 0 0 #fff) drop-shadow(0 3px 0 #fff) drop-shadow(0 -3px 0 #fff)
  drop-shadow(0 8px 10px rgba(0,0,0,.35))}
.box{box-shadow:0 10px 30px rgba(0,0,0,.25)}
.foot,.foot .brand{color:#fff}
</style>"""
    team = lambda t, cls="": (f'<div class="t1{cls}"><div class="lg">{L._logo(t["logo"], t["name"], 150, 100)}</div>'
                              f'<div><b>{escape(t["name"])}</b><small>{escape(t["sub"])}</small></div></div>')
    bar = lambda lab, a, b: (f'<div class="wr"><div class="lb">{escape(lab)}</div><div class="sb">'
                             f'<div style="width:{a:.1f}%;background:{usc["color"]}">USC {a:.0f}%</div>'
                             f'<div style="width:{b:.1f}%;background:{ucla["color"]};justify-content:flex-end">UCLA {b:.0f}%</div></div></div>')
    q = "".join(f'<div class="qr"><i style="background:{c}"></i><div class="nm">{escape(n)}<small>{escape(s)}</small></div>'
                f'<div class="st">{escape(v)}<small>{escape(vs)}</small></div></div>' for c, n, s, v, vs in qbs)
    fs, t = L._title(title, hl)
    body = f'''{L.HCSS}{css}{split_bg(usc["color"], ucla["color"])}<div class="t" style="font-size:{fs}px">{t}</div><div class="s">{escape(sub)}</div>
<div class="qs">
 <div class="tm" style="opacity:{fade(0):.2f}">{team(usc)}<div class="vs">at</div>{team(ucla, " r")}</div>
 <div class="box" style="opacity:{fade(.15):.2f};text-align:center"><div class="cap">THE LINE</div>
  <div class="mv"><span class="o">{escape(line[0])}</span><span class="a">→</span><span class="n">{escape(line[1])}</span></div>
  <div style="margin-top:8px"><span class="pill">{escape(line[2])}</span></div></div>
 <div class="box" style="opacity:{fade(.4):.2f}"><div class="cap">WHO WINS?</div>{bar(*win[0])}{bar(*win[1])}</div>
 <div class="box" style="opacity:{fade(.65):.2f}"><div class="cap">UCLA AT QB THIS SEASON</div>{q}</div>
</div>'''
    return L._page(body, True, source)


def usc_ucla(out_dir, posted=None):
    key = "cfb-2026-usc-ucla-qb"
    if key in (posted or {}):
        raise NoContent("USC-UCLA QB post already made")
    rep = C.Report("rivalry usc ucla")
    line = _line(rep)
    from datetime import datetime, timedelta, timezone
    if datetime.now(timezone.utc) >= datetime.fromisoformat(line["kick"].replace("Z", "+00:00")) - timedelta(hours=2):
        raise NoContent("Too close to kickoff (or the game is over): this preview no longer fits.")
    ucla = _splits(UCLA, rep, check_qbs=(TY, MADDEN))
    usc_games = _splits(USC, rep)
    if not rep.ok:
        raise DataError("USC-UCLA checks failed: " + "; ".join(i["detail"] for i in rep.blocked)[:400])
    ty, nico = _by_starter(ucla, TY), _by_starter(ucla, NICO)
    md = _season(MADDEN)
    rep.require(ty["g"] >= 1 and nico["g"] >= 1, "qb: UCLA starts split between Nico and Ty", f"Ty {ty['g']}, Nico {nico['g']}")
    rep.require(_by_starter(ucla, MADDEN)["g"] == 0, "qb: Madden Iamaleava has no starts", "he has started")
    tys = _season(TY)
    uw = sum(g["pf"] > g["pa"] for g in usc_games)
    usc_ppg = sum(g["pf"] for g in usc_games) / len(usc_games)
    usc_pa = sum(g["pa"] for g in usc_games) / len(usc_games)
    mkt_ucla, mkt_usc = _novig(*line["ml_now"])
    open_ucla, _ = _novig(*line["ml_open"])
    moved = abs(line["open"]) - abs(line["now"])
    rep.require(moved > 0 and line["now"] < 0, "odds: USC still favored, line moved toward UCLA", f"{line}")
    fmt = lambda v: f"USC {v:+g}".replace("-", "−")
    usc_t = {"name": "USC", "sub": f"{uw}-{len(usc_games) - uw}", "logo": logo_uri(USC, "ncaa"), "color": "#990000"}
    ucla_w = sum(g["pf"] > g["pa"] for g in ucla)
    ucla_t = {"name": "UCLA", "sub": f"{ucla_w}-{len(ucla) - ucla_w}", "logo": logo_uri(UCLA, "ncaa"), "color": "#2D68C4"}
    rec = lambda s: f"{s['w']}-{s['l']}"
    qbs = [(GREEN, "Ty Dieffenbach", STATUS_SHORT, rec(ty), f"{ty['ppg']:.1f} pts/g · {ty['papg']:.1f} allowed"),
           (GRAY, "Madden Iamaleava", "next up if Ty can't go", "0 starts", f"{md['cmp']}-of-{md['att']}, {md['yds']} yds"),
           (RED, "Nico Iamaleava", "out for season (torn ACL)", rec(nico), f"{nico['ppg']:.1f} pts/g · {nico['papg']:.1f} allowed")]
    from datetime import datetime
    from zoneinfo import ZoneInfo
    kick = datetime.fromisoformat(line["kick"].replace("Z", "+00:00")).astimezone(ZoneInfo("America/Los_Angeles"))
    when = f"{kick:%a} {kick:%-I:%M} PT" + (f" · {line['tv']}" if line["tv"] else "")
    title, hl = "Is One QB Worth\n{hl}?", f"{moved:g} Points"
    sub = f"USC at UCLA · {when} · {STATUS}"
    source = "DraftKings via ESPN · Action Network · ESPN"
    win = [("Betting market", mkt_usc, mkt_ucla), ("ESPN FPI model", line["fpi_usc"], line["fpi_ucla"])]
    cap = "\n".join([
        f"Is Ty Dieffenbach worth {moved:g} points? 🏈",
        "",
        f"USC at UCLA, {kick:%A} {kick:%-I:%M} PT{' on ' + line['tv'] if line['tv'] else ''}. UCLA's QB was carted off "
        "at Michigan last week. His coach says he's \"doing better than we thought\" (ESPN), and he hasn't been ruled out.",
        "",
        f"📉 The line: {fmt(line['open'])} when DraftKings opened it. {fmt(line['now'])} now, "
        f"{moved:g} points toward UCLA. The other major books are all within a point.",
        f"🎲 Who wins? Betting market: USC {mkt_usc:.0f}%, UCLA {mkt_ucla:.0f}% (it was UCLA {open_ucla:.0f}% at the open). "
        f"ESPN's FPI model: UCLA {line['fpi_ucla']:.0f}%.",
        "",
        "UCLA at QB this season:",
        f"✅ Ty Dieffenbach starting: {rec(ty)}, {ty['ppg']:.1f} points a game, {ty['papg']:.1f} allowed "
        f"({tys['yds']:,} passing yards, {tys['td']} TD, {tys['int']} INT)",
        f"❓ Madden Iamaleava, next up: no starts, {md['cmp']} of {md['att']} for {md['yds']} yards",
        f"🚑 Nico Iamaleava, out for the season: {rec(nico)}, {nico['ppg']:.1f} points a game",
        "",
        f"USC: {usc_t['sub']}, {usc_ppg:.1f} points a game, {usc_pa:.1f} allowed.",
        "",
        "Is one QB worth that much? And who wins if he can't go? 👇",
        "📤 Send this to the UCLA fan in your group chat.",
        "",
        "Odds: DraftKings via ESPN, checked against other books on Action Network. Win chances: moneyline with the "
        "bookmaker's margin removed, and ESPN's FPI matchup predictor. Stats: ESPN box scores (each QB's totals match his "
        "ESPN season line). Not betting advice. 21+, gamble responsibly: 1-800-GAMBLER.",
        "#usc #ucla #collegefootball #rivalryweek #cfb",
    ])
    C.caption(rep, cap)
    return _post(out_dir, key, "usc_ucla_qb", lambda p: card(title, hl, sub, usc_t, ucla_t,
                 (fmt(line["open"]), fmt(line["now"]), f"{moved:g} points toward UCLA"), win, qbs, source, p=p),
                 cap, rep, hold=7.0)


BUILDERS = {"usc_ucla": usc_ucla}
