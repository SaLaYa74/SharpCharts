"""Breaking-news posts (owner, Nov 25: "a post on the potential suitors for aaron rodgers now that he just got cut...
major hot topic right now, breaking news"; and "a funny one about mike mccarthy... over or under 5 meetings that
mccarthy fell asleep in?").

Facts are ESPN's reporting, attributed in the caption; numbers are checked against a second source:
  - Rodgers' 2026 passing: ESPN's season line must equal our sum of nflverse's game-by-game stats.
  - Team records: the verified nflverse finals (every score checked against ESPN in posts.Context).
  - The Ravens' losing streak and their two games left with Pittsburgh: counted from the same finals and schedule.
No photos of real people (rights): our own cards, team logos only.
"""
import json
import urllib.request
from collections import defaultdict
from html import escape

from . import checks as C
from . import data as D
from . import light as L
from .logos import logo_uri
from .posts import DataError, _player_weeks
from .stats import nfl_teams
from .v2 import _post

RODGERS = "8439"
ATHLETE = "https://site.web.api.espn.com/apis/common/v3/sports/football/nfl/athletes/{}"
INK, RED, GOLD = "#1F2937", "#DC2626", "#FFB612"


def _get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=30) as r:
        return json.load(r)


CSS = """<style>
.nb{flex:1;display:flex;flex-direction:column;justify-content:center;gap:24px;margin-top:22px;min-height:0}
.box{background:#fff;border-radius:26px;box-shadow:0 4px 0 rgba(0,0,0,.06);padding:20px 26px}
.cap{font-family:"Baloo 2";font-weight:800;font-size:28px;letter-spacing:2px;color:#6B7280}
.tiles{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-top:10px}
.tile{background:#F3F4F6;border-radius:18px;padding:12px 6px;text-align:center}
.tile b{display:block;font-family:"Baloo 2";font-weight:800;font-size:52px;line-height:1}
.tile small{display:block;font-size:22px;font-weight:800;color:#6B7280;margin-top:4px}
.tr{display:grid;grid-template-columns:96px 1fr;align-items:center;gap:18px;margin-top:14px}
.tr .lg{width:96px;height:96px;display:flex;align-items:center;justify-content:center}
.tr .lg img{filter:drop-shadow(0 4px 6px rgba(0,0,0,.2))}
.tr b{font-family:"Baloo 2";font-weight:800;font-size:42px;line-height:1}.tr b span{color:#6B7280;font-size:32px}
.tr small{display:block;font-size:26px;font-weight:700;color:#4B5563;line-height:1.15;margin-top:4px}
.how{font-size:29px;font-weight:700;line-height:1.3;margin-top:8px}
.ask{align-self:center;background:#FDE047;border-radius:999px;padding:6px 30px;font-family:"Baloo 2";font-weight:800;font-size:40px}
</style>"""


def rodgers_waivers(ctx, out_dir):
    rep = C.Report("news rodgers waivers").extend(ctx.report)
    a = _get(ATHLETE.format(RODGERS))["athlete"]
    rep.require((a.get("status") or {}).get("type") == "free-agent", "rodgers: ESPN lists him as no longer on a roster",
                f"status {a.get('status')}")
    st = _get(ATHLETE.format(RODGERS) + "/stats?season=2026")
    cat = next(c for c in st["categories"] if c["name"] == "passing")
    v = dict(zip(cat["labels"], next(s["stats"] for s in cat["statistics"] if s["season"]["year"] == 2026)))
    espn = {"gp": int(v["GP"]), "yds": int(v["YDS"].replace(",", "")), "td": int(v["TD"]), "int": int(v["INT"]),
            "rtg": float(v["RTG"])}
    # Second source: nflverse game-by-game, summed
    rows = _player_weeks(ctx.season, ctx.thru_week)
    yds, tds, ints = defaultdict(int), defaultdict(int), defaultdict(int)
    for r in rows:
        n = r["player_display_name"]
        yds[n] += int(float(r["passing_yards"] or 0))
        tds[n] += int(float(r["passing_tds"] or 0))
        ints[n] += int(float(r.get("passing_interceptions") or r.get("interceptions") or 0))
    nv = {"yds": yds["Aaron Rodgers"], "td": tds["Aaron Rodgers"], "int": ints["Aaron Rodgers"]}
    rep.require((nv["yds"], nv["td"], nv["int"]) == (espn["yds"], espn["td"], espn["int"]),
                "rodgers: ESPN season line equals the nflverse game-by-game sum", f"ESPN {espn} vs nflverse {nv}")
    rank = 1 + sum(y > nv["yds"] for y in yds.values())
    t = nfl_teams(ctx, rep)
    # Ravens: losing streak and games left with Pittsburgh, from the verified finals + schedule
    bal = sorted((g for g in ctx.finals if "BAL" in (g["home_team"], g["away_team"])), key=lambda g: g["week"])
    skid = 0
    for g in reversed(bal):
        mine = g["home_score"] if g["home_team"] == "BAL" else g["away_score"]
        theirs = g["away_score"] if g["home_team"] == "BAL" else g["home_score"]
        if mine < theirs:
            skid += 1
        else:
            break
    vs_pit = sum(1 for g in ctx.games if not g["final"] and {g["home_team"], g["away_team"]} == {"BAL", "PIT"})
    rep.require(skid >= 1 and vs_pit >= 1, "ravens: skid and PIT games counted", f"skid {skid}, PIT games {vs_pit}")
    if not rep.ok:
        raise DataError("Rodgers post checks failed: " + "; ".join(i["detail"] for i in rep.blocked)[:400])
    teams = [("NE", "Drake Maye: fractured fibula (ESPN)", "coach Mike Vrabel says they're sticking with Tommy DeVito"),
             ("PHI", "playing without Jalen Hurts", "practice-squad call-up Joe Milton starts Thanksgiving"),
             ("BAL", f"{skid} straight losses without Lamar Jackson", f"and they play the Steelers {vs_pit}x down the stretch")]
    ordn = lambda n: f"{n}{'th' if 10 <= n % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')}"
    tiles = [(f"{espn['yds']:,}", f"YDS · {ordn(rank)}"), (str(espn["td"]), "TD"), (str(espn["int"]), "INT"),
             (f"{espn['rtg']:.1f}", "RATING")]

    def html(p):
        fade = lambda d: max(0.0, min(1.0, (p - d) / 0.15))
        tl = "".join(f'<div class="tile"><b>{escape(x)}</b><small>{escape(y)}</small></div>' for x, y in tiles)
        tr = "".join(f'<div class="tr"><div class="lg">{L._logo(logo_uri(ab), D.TEAMS[ab][0], 96, 100)}</div><div>'
                     f'<b>{escape(D.TEAMS[ab][0])} <span>{escape(t[ab]["record"])}</span></b><small>{escape(r1)}<br>{escape(r2)}'
                     f'</small></div></div>' for ab, r1, r2 in teams)
        fs, title = L._title("Aaron Rodgers Is on Waivers.\n{hl}", "Who Claims Him?")
        body = f'''{L.HCSS}{CSS}<div class="t" style="--hl:{RED};font-size:{fs}px">{title}</div>
<div class="s">The Steelers cut him Wednesday, hours after he ripped coach Mike McCarthy on McAfee</div>
<div class="nb">
 <div class="box" style="opacity:{fade(0):.2f}"><div class="cap">HIS 2026 · {espn['gp']} GAMES</div><div class="tiles">{tl}</div></div>
 <div class="box" style="opacity:{fade(.2):.2f}"><div class="cap">TEAMS THAT COULD USE A QB</div>{tr}</div>
 <div class="box" style="opacity:{fade(.45):.2f}"><div class="cap">HOW IT WORKS</div><div class="how">It's past the trade
  deadline, so any team can claim him off waivers. Nobody claims him? He's a free agent.</div></div>
 <div class="ask" style="opacity:{fade(.65):.2f}">Which team should claim him? 👇</div>
</div>'''
        return L._page(body, True, "ESPN reporting · ESPN + nflverse stats")
    cap = "\n".join([
        "Aaron Rodgers is on waivers. Who claims him? 👀",
        "",
        "The Steelers waived him Wednesday, hours after he ripped coach Mike McCarthy on The Pat McAfee Show (ESPN). "
        "It's past the trade deadline, so any team can claim him; if nobody does, he's a free agent.",
        "",
        f"His 2026: {espn['yds']:,} passing yards ({ordn(rank)} in the NFL), {espn['td']} TD, {espn['int']} INT, "
        f"{espn['rtg']:.1f} rating in {espn['gp']} games.",
        "",
        "Teams that could use a QB:",
        f"🔵 Patriots ({t['NE']['record']}): Drake Maye has a fractured fibula, but coach Mike Vrabel says they're "
        "sticking with Tommy DeVito.",
        f"🟢 Eagles ({t['PHI']['record']}): without Jalen Hurts, Joe Milton starts on Thanksgiving.",
        f"🟣 Ravens ({t['BAL']['record']}): {skid} straight losses without Lamar Jackson, and {vs_pit} games left "
        "against Pittsburgh.",
        "",
        "ESPN's insiders are skeptical anyone bites, even at the minimum. Are they wrong? Which team should claim him? 👇",
        "📤 Send this to the fan who'd take him in a heartbeat.",
        "",
        "Sources: ESPN reporting (release, injuries, team quotes). Stats: ESPN, matched to nflverse game-by-game totals; "
        "records from verified final scores.",
        "#nfl #aaronrodgers #steelers #nflnews #football",
    ])
    C.caption(rep, cap)
    return _post(out_dir, "news-2026-11-25-rodgers-waivers", "rodgers_waivers", html, cap, rep, hold=7.0)


def mccarthy_ou(out_dir):
    """The joke one: over/under 5.5 meetings. Everything on it is attributed: Rodgers' claim, ESPN's sources, the
    Steelers' backing of McCarthy. No real bet, no odds."""
    rep = C.Report("news mccarthy over under")
    css = """<style>
.nb{flex:1;display:flex;flex-direction:column;justify-content:center;gap:24px;margin-top:20px;min-height:0}
.zz{text-align:center;font-size:150px;line-height:1}
.ou{display:grid;grid-template-columns:1fr 1fr;gap:20px}
.ou div{border-radius:28px;text-align:center;padding:22px 10px;font-family:"Baloo 2";font-weight:800;font-size:64px;line-height:1;color:#fff}
.ou small{display:block;font-family:Nunito;font-size:28px;font-weight:800;margin-top:8px;opacity:.9}
.box{background:#fff;border-radius:26px;box-shadow:0 4px 0 rgba(0,0,0,.06);padding:18px 26px}
.cap{font-family:"Baloo 2";font-weight:800;font-size:28px;letter-spacing:2px;color:#6B7280}
.pt{font-size:30px;font-weight:700;line-height:1.3;margin-top:6px}
</style>"""

    def html(p):
        fade = lambda d: max(0.0, min(1.0, (p - d) / 0.15))
        fs, title = L._title("Over/Under:\n{hl} Meetings", "5.5")
        body = f'''{L.HCSS}{css}<div class="t" style="--hl:{GOLD};font-size:{fs}px">{title}</div>
<div class="s">How many meetings did Mike McCarthy sleep through? (per Aaron Rodgers)</div>
<div class="nb">
 <div class="zz" style="opacity:{fade(0):.2f}">😴💤</div>
 <div class="ou" style="opacity:{fade(.1):.2f}"><div style="background:#111827">OVER<small>comment 😴</small></div>
  <div style="background:{GOLD};color:#111827">UNDER<small>comment ☕</small></div></div>
 <div class="box" style="opacity:{fade(.3):.2f}"><div class="cap">THE CASE FOR OVER</div><div class="pt">Rodgers on McAfee:
  McCarthy started snoring 10 minutes into a QB meeting, again 5 minutes later, and called it "not an abnormal week."
  ESPN says multiple league sources backed his account.</div></div>
 <div class="box" style="opacity:{fade(.5):.2f}"><div class="cap">THE CASE FOR UNDER</div><div class="pt">McCarthy keeps the
  Steelers' full support and stays as coach, per ESPN and NFL Network.</div></div>
</div>'''
        return L._page(body, True, "ESPN, The Pat McAfee Show · just for fun")
    cap = "\n".join([
        "Over/under: 5.5 meetings Mike McCarthy slept through this season? 😴",
        "",
        "Aaron Rodgers told The Pat McAfee Show that McCarthy started snoring about 10 minutes into a quarterback meeting "
        "last week, did it again 5 minutes later, and that it was \"not an abnormal week.\" ESPN reports multiple league "
        "sources corroborated Rodgers' account. The Steelers waived Rodgers hours later; McCarthy keeps the team's full "
        "support, per ESPN and NFL Network.",
        "",
        "Set your line: comment 😴 for OVER or ☕ for UNDER 👇",
        "📤 Send this to the coworker who naps in every meeting.",
        "",
        "Just for fun. Sources: ESPN reporting and The Pat McAfee Show (Nov 25).",
        "#nfl #steelers #mikemccarthy #aaronrodgers #nflnews",
    ])
    C.caption(rep, cap)
    return _post(out_dir, "news-2026-11-25-mccarthy-ou", "mccarthy_ou", html, cap, rep, hold=6.0)


def mccarthy_ou_ctx(ctx, out_dir):
    return mccarthy_ou(out_dir)


BUILDERS_CTX = {"rodgers_waivers": rodgers_waivers, "mccarthy_ou": mccarthy_ou_ctx}
