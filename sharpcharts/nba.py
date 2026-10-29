"""NBA Reels: the same "$100 on every game" math as the NFL posts, so the page has something every
night from October to June.

Data (all free, all ESPN):
  scores : ESPN scoreboard. Every final must equal the sum of its quarter/OT scores, and every team's
           running W-L in our data must match the record ESPN printed next to that game.
  lines  : ESPN's odds feed, DraftKings CLOSING line (spread, total, moneylines and the price on each).
           Checked for internal consistency (both sides of the spread, favorite on spread vs moneyline,
           the posted line text) and against the pre-game line our own archive job saved.
A game whose line fails a check is left out with a warning; if more than a few are left out, or any
score fails, nothing posts.
"""
import glob
import json
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from . import checks as C
from . import light as L
from .data import CACHE, ROOT, get_json
from .logos import logo_uri
from .posts import DISCLAIMER, DataError, NoContent
from .v2 import COOL, GREEN, RED, WARM, _bet, _post, money

ET = ZoneInfo("America/New_York")
SEASON = 2027                          # ESPN's season year for 2026-27
OPENING_NIGHT = date(2026, 10, 20)
SCOREBOARD = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates={}"
ODDS = "https://sports.core.api.espn.com/v2/sports/basketball/leagues/nba/events/{0}/competitions/{0}/odds"
TEAMS_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams"
NICK = {"Timberwolves": "Wolves", "Trail Blazers": "Blazers"}     # fit under a bar
SOURCE = "ESPN scores · DraftKings closing lines"
DATA_LINE = "Data: final scores from ESPN, DraftKings closing lines via ESPN."
TAGS = "#nba #nbabetting #sportsbetting #basketball"
MAX_LEFT_OUT = 0.05                    # share of games allowed to be dropped for a bad line
_teams = None


def teams():
    """abbr -> {name, color} for all 30 teams (ESPN)."""
    global _teams
    if _teams is None:
        d = get_json(TEAMS_URL)
        _teams = {}
        for t in (x["team"] for x in d["sports"][0]["leagues"][0]["teams"]):
            n = t["shortDisplayName"]
            _teams[t["abbreviation"]] = {"name": NICK.get(n, n), "color": "#" + (t.get("color") or "3A4A6B")}
    return _teams


def name(abbr):
    return teams()[abbr]["name"]


def badge(abbr, px=126):
    """Round team badge: official logo on white, or the team color + abbreviation when logos are off."""
    color = teams().get(abbr, {}).get("color", "#3A4A6B")
    uri = logo_uri(abbr, "nba")
    inner = (f'<img src="{uri}" style="width:76%;height:76%;object-fit:contain">' if uri else
             f'<span style="font-family:\'Baloo 2\';font-weight:800;color:#fff;font-size:{int(px * .32)}px">{abbr}</span>')
    return (f'<div style="width:{px}px;height:{px}px;border-radius:50%;background:{"#fff" if uri else color};'
            f'border:5px solid #1F2937;display:flex;align-items:center;justify-content:center">{inner}</div>')


# ---------------------------------------------------------------- data

def _cached(url, path, keep):
    """JSON from url; saved to data/nba/<path> once keep(json) says it can't change any more."""
    full = os.path.join(CACHE, "nba", path)
    if os.path.exists(full):
        return json.load(open(full))
    d = get_json(url)
    if keep(d):
        os.makedirs(os.path.dirname(full), exist_ok=True)
        json.dump(d, open(full, "w"))
    return d


def _today():
    return datetime.now(ET).date()


def _events(day):
    old = day < _today() - timedelta(days=2)       # scores can still be corrected for a day or two
    d = _cached(SCOREBOARD.format(day.strftime("%Y%m%d")), f"sb_{day:%Y%m%d}.json", lambda _: old)
    return [(day, e) for e in d.get("events", [])]


def _game(day, e):
    comp = e["competitions"][0]
    st = e["status"]["type"]
    side = {c["homeAway"]: c for c in comp["competitors"]}
    g = {"id": e["id"], "day": day, "tip": e["date"], "status": st.get("name"),
         "final": bool(st.get("completed")) and st.get("state") == "post",
         "regular": (e.get("season") or {}).get("type") == 2}
    for k in ("home", "away"):
        c = side[k]
        g[k] = c["team"]["abbreviation"]
        g[f"{k}_score"] = int(c["score"]) if c.get("score") not in (None, "") else None
        g[f"{k}_periods"] = [ls.get("value") for ls in c.get("linescores", [])]
        g[f"{k}_record"] = next((r.get("summary") for r in c.get("records", []) if r.get("type") == "total"), None)
    return g


def _num(v):
    """American price / line from ESPN text ('+6.5', '-110', 'EVEN', 'PK')."""
    s = str(v).strip().upper()
    if s in ("EVEN", "EV"):
        return 100.0
    if s in ("PK", "PICK"):
        return 0.0
    try:
        return float(s.replace("+", ""))
    except ValueError:
        return None


def _spread_from_text(details, home, away):
    """Home team's spread from a line like 'LAL -6.5'."""
    if not details:
        return None
    if details.strip().upper() in ("EVEN", "PK", "PICK"):
        return 0.0
    fav, _, n = details.rpartition(" ")
    n = _num(n)
    if n is None or fav not in (home, away):
        return None
    return -abs(n) if fav == home else abs(n)


def archived_lines():
    """Pre-game lines our archive job saved: game id -> (home spread, total), latest capture before tip."""
    out = {}
    for f in sorted(glob.glob(os.path.join(ROOT, "archive", "nba", "*.json"))):
        try:
            for e in json.load(open(f))["events"]:
                o = e.get("odds") or {}
                if e.get("state") == "pre" and o.get("details"):
                    s = _spread_from_text(o["details"], e["teams"]["home"]["abbr"], e["teams"]["away"]["abbr"])
                    if s is not None:
                        out[e["id"]] = (s, o.get("over_under"))
        except (ValueError, KeyError):
            continue
    return out


def _closing(g, rep, archive):
    """Attach the DraftKings closing line to a final game. Returns False (game left out) if any check fails."""
    label = f"{g['away']}@{g['home']} {g['day']}"
    d = _cached(ODDS.format(g["id"]), f"odds_{g['id']}.json", lambda d: bool(d.get("items")))
    items = [i for i in d.get("items", []) if "draft" in ((i.get("provider") or {}).get("name") or "").lower()]
    if not rep.expect(bool(items), f"{label}: DraftKings line", "no DraftKings line in ESPN's odds feed; left out"):
        return False
    o = items[0]
    hc = (o.get("homeTeamOdds") or {}).get("close") or {}
    ac = (o.get("awayTeamOdds") or {}).get("close") or {}
    t = o.get("close") or {}
    try:
        line = dict(spread=_num(hc["pointSpread"]["american"]), away_spread=_num(ac["pointSpread"]["american"]),
                    total=_num(t["total"]["american"]),
                    home_ml=_num(hc["moneyLine"]["american"]), away_ml=_num(ac["moneyLine"]["american"]),
                    home_spread_odds=_num(hc["spread"]["american"]), away_spread_odds=_num(ac["spread"]["american"]),
                    over_odds=_num(t["over"]["american"]), under_odds=_num(t["under"]["american"]))
    except (KeyError, TypeError):
        line = {}
    if not rep.expect(line and all(v is not None for v in line.values()), f"{label}: closing line complete",
                      "closing line incomplete; left out"):
        return False
    checks = [
        (line["spread"] == -line["away_spread"], "both sides of the spread match",
         f"home {line['spread']} vs away {line['away_spread']}"),
        (_spread_from_text(o.get("details"), g["home"], g["away"]) == line["spread"], "line text matches the spread",
         f"'{o.get('details')}' vs home {line['spread']:+g}"),
        (abs(line["spread"]) < 2 or (line["home_ml"] < line["away_ml"]) == (line["spread"] < 0),
         "spread and moneyline agree on the favorite", f"spread {line['spread']:+g}, ML {line['home_ml']:+g}/{line['away_ml']:+g}"),
        (all(100 <= abs(line[k]) <= 250 for k in ("home_spread_odds", "away_spread_odds", "over_odds", "under_odds")),
         "spread/total prices plausible", str({k: line[k] for k in ("home_spread_odds", "away_spread_odds", "over_odds", "under_odds")})),
    ]
    if g["id"] in archive:
        s0, t0 = archive[g["id"]]
        checks.append((abs(s0 - line["spread"]) <= 4 and (t0 is None or abs(t0 - line["total"]) <= 8),
                       "close is near the pre-game line we archived",
                       f"archived {s0:+g}/{t0}, close {line['spread']:+g}/{line['total']:g}"))
    for ok, what, detail in checks:
        if not rep.expect(ok, f"{label}: {what}", detail + "; left out"):
            return False
    C.line_ranges(rep, "nba", label, line["spread"], line["total"], moneylines=(line["home_ml"], line["away_ml"]))
    g.update(line)
    g["archived"] = g["id"] in archive
    return True


def _verify_score(g, rep):
    label = f"{g['away']}@{g['home']} {g['day']}"
    for k in ("home", "away"):
        p = g[f"{k}_periods"]
        rep.require(g[f"{k}_score"] is not None and len(p) >= 4 and sum(p) == g[f"{k}_score"],
                    f"{label}: {k} score equals its quarter scores", f"{g[f'{k}_score']} vs {p}")
    rep.require(g["home_score"] != g["away_score"], f"{label}: has a winner", "tied final")


def load_finals(days, rep):
    """Regular-season finals on the given days, scores verified, closing lines attached.
    Returns (games with lines, all verified finals)."""
    with ThreadPoolExecutor(8) as ex:
        raw = [x for day_events in ex.map(_events, days) for x in day_events]
    games = [_game(d, e) for d, e in raw]
    games = [g for g in games if g["regular"]]
    finals = [g for g in games if g["final"]]
    for g in finals:
        _verify_score(g, rep)
    archive = archived_lines()
    with ThreadPoolExecutor(8) as ex:
        ok = list(ex.map(lambda g: _closing(g, rep, archive), finals))
    lined = [g for g, k in zip(finals, ok) if k]
    left = len(finals) - len(lined)
    if finals:
        rep.require(left <= max(1, MAX_LEFT_OUT * len(finals)), "few games left out for line problems",
                    f"{left} of {len(finals)} games left out")
        checked = sum(g["archived"] for g in lined)
        rep.expect(checked >= 0.5 * len(lined), "most lines cross-checked against our archive",
                   f"only {checked} of {len(lined)} had an archived pre-game line")
    return lined, finals, games


def season(rep, through=None):
    """Every regular-season final from opening night through `through` (default: last night)."""
    through = through or _today() - timedelta(days=1)
    days = [OPENING_NIGHT + timedelta(n) for n in range((through - OPENING_NIGHT).days + 1)]
    if not days:
        raise NoContent("The NBA season hasn't started.")
    lined, finals, games = load_finals(days, rep)
    pending = [g for g in games if not g["final"] and g["status"] not in ("STATUS_POSTPONED", "STATUS_CANCELED")]
    if pending:
        raise DataError(f"{len(pending)} game(s) through {through} not final yet")
    # ESPN prints each team's record as of that game; our running W-L must match it game by game.
    run = {}
    for g in sorted(finals, key=lambda g: g["tip"]):
        hw = g["home_score"] > g["away_score"]
        for k, won in (("home", hw), ("away", not hw)):
            w, l_ = run.get(g[k], (0, 0))
            run[g[k]] = (w + won, l_ + (not won))
            if g[f"{k}_record"]:
                rep.require(g[f"{k}_record"] == f"{run[g[k]][0]}-{run[g[k]][1]}",
                            f"{g[k]} record after {g['day']} matches ESPN",
                            f"ours {run[g[k]][0]}-{run[g[k]][1]} vs ESPN {g[f'{k}_record']}")
    return lined, through


# ---------------------------------------------------------------- $100 math

def _ats(g, k):
    """'W'/'L'/'P' for side k ('home'/'away') against the closing spread."""
    m = (g["home_score"] - g["away_score"]) if k == "home" else (g["away_score"] - g["home_score"])
    s = g["spread"] if k == "home" else -g["spread"]
    return "W" if m + s > 0 else ("L" if m + s < 0 else "P")


def _ou(g):
    pts = g["home_score"] + g["away_score"]
    return "O" if pts > g["total"] else ("U" if pts < g["total"] else "P")


def angles(games):
    a = {k: 0.0 for k in ("Favorites", "Underdogs", "Home teams", "Road teams", "Overs", "Unders")}
    for g in games:
        rh, ra = _ats(g, "home"), _ats(g, "away")
        bh, ba = _bet(rh, g["home_spread_odds"]), _bet(ra, g["away_spread_odds"])
        a["Home teams"] += bh
        a["Road teams"] += ba
        if g["spread"]:
            a["Favorites"] += bh if g["spread"] < 0 else ba
            a["Underdogs"] += ba if g["spread"] < 0 else bh
        ou = _ou(g)
        a["Overs"] += _bet({"O": "W", "U": "L"}.get(ou, "P"), g["over_odds"])
        a["Unders"] += _bet({"U": "W", "O": "L"}.get(ou, "P"), g["under_odds"])
    return a


def by_team(games):
    """abbr -> {ats $, over $, W/L/P against the spread, games}."""
    t = {}
    for g in games:
        ou = _ou(g)
        for k in ("home", "away"):
            r = t.setdefault(g[k], {"ats": 0.0, "over": 0.0, "W": 0, "L": 0, "P": 0, "n": 0})
            res = _ats(g, k)
            r["ats"] += _bet(res, g[f"{k}_spread_odds"])
            r["over"] += _bet({"O": "W", "U": "L"}.get(ou, "P"), g["over_odds"])
            r[res] += 1
            r["n"] += 1
    return t


def upsets(games):
    """[(moneyline, dog, fav, 'dog_score-fav_score')] for underdogs that won outright."""
    out = []
    for g in games:
        if max(g["home_ml"], g["away_ml"]) < 100 or g["home_ml"] == g["away_ml"]:
            continue
        dog = "home" if g["home_ml"] > g["away_ml"] else "away"
        fav = "away" if dog == "home" else "home"
        if g[f"{dog}_score"] > g[f"{fav}_score"]:
            out.append((g[f"{dog}_ml"], g[dog], g[fav], f"{g[f'{dog}_score']}-{g[f'{fav}_score']}"))
    return sorted(out, reverse=True)


def _plausible(rep, totals, n):
    for k, v in totals.items():
        rep.require(abs(v) <= n * 260, f"{k} total plausible", f"{v:.0f} over {n} games")


def _rec(r):
    return f"{r['W']}-{r['L']}" + (f"-{r['P']}" if r["P"] else "") + " ATS"


def _thru(d):
    return f"thru {d:%b} {d.day}"


ICONS = {"Favorites": "crown", "Underdogs": "dog", "Home teams": "home", "Road teams": "plane", "Overs": "up", "Unders": "down"}
ONE = {"Favorites": "favorite", "Underdogs": "underdog", "Home teams": "home team", "Road teams": "road team",
       "Overs": "over", "Unders": "under"}


# ---------------------------------------------------------------- posts

def last_night(out_dir, day=None):
    """'Last night in $': what $100 on every favorite / underdog / home / road / over / under paid on
    last night's NBA slate, plus the biggest upset. Posted the next morning."""
    day = day or _today() - timedelta(days=1)
    rep = C.Report("nba last night")
    lined, finals, games = load_finals([day], rep)
    if len(games) < 4:
        raise NoContent(f"Only {len(games)} NBA games on {day}.")
    pending = [g for g in games if not g["final"] and g["status"] not in ("STATUS_POSTPONED", "STATUS_CANCELED")]
    if pending:
        raise DataError(f"Waiting on {len(pending)} game(s) from {day} to go final")
    rep.require(len(lined) >= 4, "enough games with verified lines", f"only {len(lined)}")
    a = angles(lined)
    _plausible(rep, a, len(lined))
    order = sorted(a, key=lambda k: -a[k])
    items = [{"label": k, "sub": "last night", "value": abs(a[k]), "icon": ICONS[k], "value_label": money(a[k]),
              "color": GREEN if a[k] >= 0 else RED} for k in order]
    best, worst = order[0], order[-1]
    ups = upsets(lined)
    lines = [f"Last night in the NBA 💸 $100 on every {ONE[best]}: {money(a[best])}. Every {ONE[worst]}: {money(a[worst])}."]
    if ups:
        ml, dog, fav, sc = ups[0]
        lines.append(f"Biggest upset: the {name(dog)} (+{ml:.0f}) beat the {name(fav)} {sc}. $100 on them paid ${ml:,.0f} 🐶")
    lines.append("\n".join(f"{'🟢' if a[k] >= 0 else '🔴'} Every {ONE[k]}: {money(a[k])}" for k in order))
    lines.append("Which way are you going tonight? 👇")
    lines.append(f"📤 Send this to the friend who rode the {worst.lower()} last night 😅")
    left = len(finals) - len(lined)
    cap = "\n\n".join(lines) + (
        f"\n\n$100 per game at closing lines, {len(lined)} NBA games on {day:%a %b} {day.day}"
        f"{f' ({left} left out: line could not be verified)' if left else ''}.\n{DATA_LINE}\n{DISCLAIMER}\n{TAGS}")
    key = f"nba-{day.isoformat()}-night"
    return _post(out_dir, key, "nba_night", lambda r, t: L.bars(
        "Who Got {hl} Last Night?", "Paid", f"$100 on every bet type · {len(lined)} NBA games · {day:%b} {day.day}",
        items, SOURCE, hl_color=GREEN, reveal=r, tease=t), cap, rep, countdown=len(items))


MIN_GAMES = 3


def _season_teams(rep):
    lined, thru = season(rep)
    t = by_team(lined)
    rep.require(len(t) == 30, "all 30 teams have played", f"{len(t)} teams")
    if min(r["n"] for r in t.values()) < MIN_GAMES:
        raise NoContent("Too early: some teams have fewer than 3 games.")
    _plausible(rep, {k: v["ats"] for k, v in t.items()}, max(r["n"] for r in t.values()))
    return t, thru, len(lined)


def _ranked(t, sign):
    """Teams sorted by $ (sign=-1: most profit first), ties broken alphabetically so every post agrees."""
    return sorted(t.items(), key=lambda kv: (sign * round(kv[1]["ats"], 2), name(kv[0])))


def _tied(rows):
    """Names of every team tied with the first row ('Knicks, Heat and Jazz'), and how many."""
    top = sorted(name(k) for k, v in rows if round(v["ats"], 2) == round(rows[0][1]["ats"], 2))
    return (", ".join(top[:-1]) + " and " + top[-1] if len(top) > 1 else top[0]), len(top)


def _week_key(thru, what):
    y, w, _ = thru.isocalendar()
    return f"nba-{SEASON}-w{y % 100:02d}{w:02d}-{what}"


def _team_items(rows, palette, sub):
    return [{"label": name(k), "sub": sub(v), "value": abs(v["ats"]), "icon": f"nba:{k}", "value_label": money(v["ats"]),
             "color": palette[i % len(palette)]} for i, (k, v) in enumerate(rows)]


def best(out_dir):
    rep = C.Report("nba best")
    t, thru, n = _season_teams(rep)
    rows = _ranked(t, -1)[:5]
    if rows[0][1]["ats"] <= 0:
        raise NoContent("No NBA team is profitable yet.")
    top = rows[0]
    who, n_tied = _tied(rows)
    won = lambda v: f"won {v['W']} of {v['n']} bets"
    cap = ((f"The {name(top[0])} have been printing money for bettors 💰 $100 on them every game = up ${top[1]['ats']:,.0f}.\n\n"
            if n_tied == 1 else
            f"The {who} are all up ${top[1]['ats']:,.0f} for bettors 💰 $100 on any of them every game, and you're cashing.\n\n")
           + "\n".join(f"🟢 {name(k)}: {money(v['ats'])} ({won(v)})" for k, v in rows)
           + f"\n\n{name(top[0])} the rest of the way: ride them or fade them? 👇"
           + f"\n\n📤 Send this to a {name(top[0])} fan. They've earned it."
           + f"\n\n$100 on every game against the spread, at closing odds, {n} games through {thru:%b} {thru.day}.\n"
           f"{DATA_LINE}\n{DISCLAIMER}\n{TAGS}")
    return _post(out_dir, _week_key(thru, "best"), "nba_best", lambda r, tz: L.bars(
        "Which Team {hl} Bettors Most?", "Paid", f"$100 on every NBA game, against the spread · {_thru(thru)}",
        _team_items(rows, COOL, won), SOURCE, hl_color=GREEN, reveal=r, tease=tz), cap, rep, countdown=len(rows))


def worst(out_dir):
    rep = C.Report("nba worst")
    t, thru, n = _season_teams(rep)
    rows = _ranked(t, 1)[:5]
    if rows[0][1]["ats"] >= 0:
        raise NoContent("No NBA team is losing money yet.")
    w = rows[0]
    who, n_tied = _tied(rows)
    lost = lambda v: f"lost {v['L']} of {v['n']} bets"
    cap = ((f"The {name(w[0])} have cost bettors {money(w[1]['ats'])[1:]} this season. Nobody's been worse 😬\n\n"
            if n_tied == 1 else
            f"The {who} have each cost bettors {money(w[1]['ats'])[1:]} this season. Nobody's been worse 😬\n\n")
           + "\n".join(f"🔴 {name(k)}: {money(v['ats'])} ({lost(v)})" for k, v in rows)
           + f"\n\n{name(w[0])}: buy-low spot or stay away? 👇"
           + f"\n\n📤 Send this to the {name(w[0])} fan in your group chat 😬"
           + f"\n\n$100 on every game against the spread, at closing odds, {n} games through {thru:%b} {thru.day}.\n"
           f"{DATA_LINE}\n{DISCLAIMER}\n{TAGS}")
    return _post(out_dir, _week_key(thru, "worst"), "nba_worst", lambda r, tz: L.bars(
        "Which Team {hl} Bettors Most?", "Burned", f"$100 on every NBA game, against the spread · {_thru(thru)}",
        _team_items(rows, WARM, lost), SOURCE, hl_color=RED, reveal=r, tease=tz), cap, rep, countdown=len(rows))


def all30(out_dir):
    """Every team on one screen. Built to be shared: everyone looks for their team."""
    rep = C.Report("nba all30")
    t, thru, n = _season_teams(rep)
    rows = _ranked(t, -1)
    board = [{"icon": f"nba:{k}", "label": name(k), "sub": _rec(v), "value_label": money(v["ats"]),
              "color": GREEN if v["ats"] >= 0 else RED} for k, v in rows]
    b, w = rows[0], rows[-1]
    up = sum(1 for _, v in rows if v["ats"] > 0)
    best_who, _ = _tied(rows)
    worst_who, _ = _tied(rows[::-1])
    cap = (f"Find your team 👇 $100 on every NBA game this season, all 30 teams.\n\n"
           f"Best: {best_who} {money(b[1]['ats'])}. Worst: {worst_who} {money(w[1]['ats'])}. "
           f"{up} of 30 teams have made you money.\n\n"
           + "\n".join(f"{i + 1}. {name(k)}: {money(v['ats'])}" for i, (k, v) in enumerate(rows))
           + "\n\nWhere's your team, and are you buying it? 👇"
           + f"\n\n📤 Send this to the {name(w[0])} fan in your group chat 😬 📌 Save it to check next week."
           + f"\n\n$100 on every game against the spread, at closing odds, {n} games through {thru:%b} {thru.day}.\n"
           f"{DATA_LINE}\n{DISCLAIMER}\n{TAGS}")
    return _post(out_dir, _week_key(thru, "all30"), "nba_all30", lambda p: L.board(
        "Find Your {hl}", "Team", f"$100 on every NBA game, against the spread · {_thru(thru)}",
        board, SOURCE, p=p, hl_color="#3B82F6"), cap, rep, hold=7.0)


BUILDERS = {"nba_night": last_night, "nba_best": best, "nba_worst": worst, "nba_all30": all30}
