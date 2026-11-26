"""Holiday-week NFL posts (owner, Nov 25: "post about this wednesday night game (rams vs packers)... a post out tmrw
morning about the thanksgiving games. Lets take advantage of these holiday games, they draw a ton of attention").

Stats only (the Oct 31 stats-page rule; the owner asked for odds on USC-UCLA alone). Every number comes from the
verified nflverse finals (each final score checked against ESPN in posts.Context), and each team's record must also
match the record ESPN prints on tonight's scoreboard.
"""
import json
import urllib.request
from datetime import datetime, timezone
from html import escape
from zoneinfo import ZoneInfo

from . import checks as C
from . import data as D
from . import light as L
from .logos import logo_uri
from .posts import DataError, NoContent
from .stats import NFL_DATA, nfl_teams
from .v2 import _post

PT = ZoneInfo("America/Los_Angeles")
SCOREBOARD = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?dates={}"
RED, GREEN, INK = "#DC2626", "#16A34A", "#1F2937"


def _get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=30) as r:
        return json.load(r)


def _games(day):
    """ESPN's NFL games on a date: [dict(id, kick (utc), tv, home, away, home_rec, away_rec)] in nflverse abbrs."""
    out = []
    for e in _get(SCOREBOARD.format(day.strftime("%Y%m%d"))).get("events", []):
        c = e["competitions"][0]
        side = {x["homeAway"]: x for x in c["competitors"]}
        ab = lambda k: D.ESPN_TO_NFLVERSE.get(side[k]["team"]["abbreviation"], side[k]["team"]["abbreviation"])
        rec = lambda k: next((r["summary"] for r in side[k].get("records", []) if r.get("type") in ("total", None)), "")
        out.append({"id": e["id"], "kick": datetime.fromisoformat(e["date"].replace("Z", "+00:00")),
                    "tv": next((n for b in c.get("broadcasts", []) for n in b.get("names", [])), ""),
                    "home": ab("home"), "away": ab("away"), "home_rec": rec("home"), "away_rec": rec("away")})
    return sorted(out, key=lambda g: g["kick"])


def _ranks(t):
    """1 = best: scoring (most points a game) and defense (fewest allowed)."""
    off = {a: 1 + sum(t[b]["ppg"] > t[a]["ppg"] for b in t) for a in t}
    dfn = {a: 1 + sum(t[b]["pa"] / t[b]["g"] < t[a]["pa"] / t[a]["g"] for b in t) for a in t}
    return off, dfn


def _ord(n):
    return f"{n}{'th' if 10 <= n % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')}"


def _checked(ctx, rep, games):
    t = nfl_teams(ctx, rep)
    for g in games:
        for k in ("home", "away"):
            rep.require(t[g[k]]["record"] == g[f"{k}_rec"], f"nfl: {g[k]} record matches ESPN's scoreboard",
                        f"ours {t[g[k]]['record']} vs ESPN {g[f'{k}_rec']}")
    if not rep.ok:
        raise DataError("Holiday post checks failed: " + "; ".join(i["detail"] for i in rep.blocked)[:300])
    return t


def _rows(t, off, dfn, a, b):
    """Head-to-head rows, a = left, b = right. Returns (rows, a wins, b wins)."""
    pa = lambda x: t[x]["pa"] / t[x]["g"]
    cats = [("Record", lambda x: (t[x]["w"] + t[x]["t"] / 2) / t[x]["g"], True, lambda x: t[x]["record"], lambda x: ""),
            ("Points / game", lambda x: t[x]["ppg"], True, lambda x: f"{t[x]['ppg']:.1f}", lambda x: _ord(off[x])),
            ("Allowed / game", pa, False, lambda x: f"{pa(x):.1f}", lambda x: _ord(dfn[x])),
            ("Point diff / game", lambda x: t[x]["diff"], True, lambda x: f"{t[x]['diff']:+.1f}", lambda x: "")]
    rows, wa, wb = [], 0, 0
    for label, val, high, shown, small in cats:
        x, y = round(val(a), 3), round(val(b), 3)
        win = None if x == y else ("l" if (x > y) == high else "r")
        wa, wb = wa + (win == "l"), wb + (win == "r")
        rows.append({"label": label, "l": shown(a), "r": shown(b), "lsub": small(a), "rsub": small(b), "win": win})
    return rows, wa, wb


def _when(kick, now):
    k = kick.astimezone(PT)
    day = "Tonight" if k.date() == now.astimezone(PT).date() and k.hour >= 15 else f"{k:%a}"
    return f"{day} {k:%-I:%M} PT"


def nfl_h2h(ctx, out_dir, day, home, posted=None):
    """Tale of the tape for one game (by home team, nflverse abbr). Refuses after kickoff."""
    now = datetime.now(timezone.utc)
    g = next((g for g in _games(day) if g["home"] == home), None)
    if g is None:
        raise NoContent(f"No {home} home game on {day}.")
    if now >= g["kick"]:
        raise NoContent("Kickoff has passed.")
    rep = C.Report(f"holiday h2h {g['away']}@{home}").extend(ctx.report)
    t = _checked(ctx, rep, [g])
    off, dfn = _ranks(t)
    a, b = g["away"], g["home"]                 # away on the left: "Packers at Rams"
    rows, wa, wb = _rows(t, off, dfn, a, b)
    name = lambda x: D.TEAMS[x][0]
    if wa == wb:
        title, hl, col, tally = "Dead Even\n{hl}", "on Paper", INK, f"Dead even {wa}-{wb}"
    else:
        lead = a if wa > wb else b
        title, hl, col = "{hl} Win\nthe Tale of the Tape", f"The {name(lead)}", GREEN
        tally = f"Edge: {name(lead)} {max(wa, wb)}-{min(wa, wb)}"
    when = _when(g["kick"], now)
    sub = f"{name(a)} at {name(b)} · {when}" + (f" · {g['tv']}" if g["tv"] else "") + f" · thru Week {ctx.thru_week}"
    side = lambda x: {"logo": logo_uri(x), "name": name(x), "sub": t[x]["record"]}
    lines = "\n".join(f"• {r['label']}: {name(a)} {r['l']}{' (' + r['lsub'] + ')' if r['lsub'] else ''}, "
                      f"{name(b)} {r['r']}{' (' + r['rsub'] + ')' if r['rsub'] else ''}" for r in rows)
    cap = (f"{name(a)} ({t[a]['record']}) at {name(b)} ({t[b]['record']}), {'tonight ' + when.split(' ', 1)[1] if when.startswith('Tonight') else when}"
           f"{' on ' + g['tv'] if g['tv'] else ''} 🏈\n\nSide by side, thru Week {ctx.thru_week} "
           f"(ranks out of 32):\n{lines}\n\n{tally}. Who wins it? 👇\n\n📤 Send this to a {name(a)} fan and a {name(b)} fan."
           f"\n\nRegular-season points scored and allowed per game.\n{NFL_DATA}\n"
           f"#nfl #{name(a).lower().replace(' ', '')} #{name(b).lower().replace(' ', '')} #football #nflstats")
    C.caption(rep, cap)
    key = f"{ctx.season}-{day:%m%d}-h2h-{a}-{b}".lower()
    return _post(out_dir, key, f"h2h_{a}_{b}".lower(), lambda p: L.h2h(
        title, hl, sub, side(a), side(b), rows, tally, "nflverse · scores verified vs ESPN", p=p, hl_color=col,
        tally_bg=INK), cap, rep, hold=6.0)


def nfl_slate(ctx, out_dir, day, label="Thanksgiving", posted=None):
    """Every game on a day as one board: both teams' records and scoring, plus who wins the tale of the tape."""
    now = datetime.now(timezone.utc)
    games = [g for g in _games(day) if g["kick"] > now]
    if len(games) < 2:
        raise NoContent(f"Fewer than 2 games left on {day}.")
    rep = C.Report(f"holiday slate {day}").extend(ctx.report)
    t = _checked(ctx, rep, games)
    off, dfn = _ranks(t)
    name = lambda x: D.TEAMS[x][0]
    board, lines = [], []
    for g in games:
        a, b = g["away"], g["home"]
        rows, wa, wb = _rows(t, off, dfn, a, b)
        k = g["kick"].astimezone(PT)
        if wa == wb:
            tag, bg, fg = f"{k:%-I:%M} PT · DEAD EVEN ON PAPER", "#FDE047", INK
        else:
            lead = a if wa > wb else b
            tag, bg, fg = f"{k:%-I:%M} PT · EDGE: {name(lead).upper()} {max(wa, wb)}-{min(wa, wb)}", "#DCFCE7", "#15803D"
        sd = lambda x: {"seed": "", "logo": logo_uri(x), "name": name(x),
                        "line": f"{t[x]['record']} · {t[x]['ppg']:.1f} pts · {t[x]['pa'] / t[x]['g']:.1f} allowed"}
        board.append({"l": sd(a), "r": sd(b), "tag": tag + (f" · {g['tv']}" if g["tv"] else ""), "tag_bg": bg, "tag_fg": fg})
        lines.append(f"🦃 {name(a)} ({t[a]['record']}) at {name(b)} ({t[b]['record']}), {k:%-I:%M} PT"
                     f"{' on ' + g['tv'] if g['tv'] else ''}\n   Scoring: {name(a)} {t[a]['ppg']:.1f} ({_ord(off[a])}), "
                     f"{name(b)} {t[b]['ppg']:.1f} ({_ord(off[b])}). Allowed: {name(a)} {t[a]['pa'] / t[a]['g']:.1f} "
                     f"({_ord(dfn[a])}), {name(b)} {t[b]['pa'] / t[b]['g']:.1f} ({_ord(dfn[b])}).\n   "
                     + (f"Edge on paper: {name(a if wa > wb else b)} {max(wa, wb)}-{min(wa, wb)}" if wa != wb else "Dead even on paper"))
    title, hl = f"{label}:\n{{hl}}", f"{len(games)} Games, 1 Chart"
    sub = f"Record · points scored · points allowed · thru Week {ctx.thru_week}"
    cap = (f"Your {label} football, side by side 🦃🏈\n\n" + "\n\n".join(lines) +
           f"\n\n(Edge = who wins more of: record, points scored, points allowed, point differential. Ranks out of 32.)"
           f"\n\nWhich one's the upset? 👇\n\n📤 Send this to the family group chat before kickoff."
           f"\n\nRegular season thru Week {ctx.thru_week}.\n{NFL_DATA}\n#nfl #thanksgiving #thanksgivingfootball #football #nflstats")
    C.caption(rep, cap)
    key = f"{ctx.season}-{day:%m%d}-slate"
    return _post(out_dir, key, f"slate_{day:%m%d}", lambda p: L.matchups(
        title, hl, sub, board, [], "nflverse · scores verified vs ESPN", p=p, hl_color="#EA580C"), cap, rep, hold=7.0)


def rams_packers(ctx, out_dir):
    from datetime import date
    return nfl_h2h(ctx, out_dir, date(2026, 11, 25), "LA")


def thanksgiving(ctx, out_dir):
    from datetime import date
    return nfl_slate(ctx, out_dir, date(2026, 11, 26))


BUILDERS_CTX = {"rams_packers": rams_packers, "thanksgiving": thanksgiving}
