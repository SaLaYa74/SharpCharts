"""Data layer: fetch NFL results + betting lines, verify them, compute bettor trends.

Primary source : nflverse games.csv (open data, scores + closing lines + moneylines)
Cross-check    : ESPN public scoreboard API (final scores + DraftKings current lines)

Every post the generator renders is built from numbers computed here, and
`verify_scores()` must pass before anything is exported.
"""
import csv
import io
import json
import os
import time
import urllib.request
from collections import defaultdict
from datetime import date, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "data")
NFLVERSE_URL = "https://github.com/nflverse/nfldata/raw/master/data/games.csv"
ESPN_URL = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?dates={}"

# ESPN uses a few different abbreviations than nflverse.
ESPN_TO_NFLVERSE = {"WSH": "WAS", "LAR": "LA"}

TEAMS = {
    "ARI": ("Cardinals", "#97233F"), "ATL": ("Falcons", "#A71930"), "BAL": ("Ravens", "#4B2E9A"),
    "BUF": ("Bills", "#00338D"), "CAR": ("Panthers", "#0085CA"), "CHI": ("Bears", "#C83803"),
    "CIN": ("Bengals", "#FB4F14"), "CLE": ("Browns", "#FF3C00"), "DAL": ("Cowboys", "#003594"),
    "DEN": ("Broncos", "#FB4F14"), "DET": ("Lions", "#0076B6"), "GB": ("Packers", "#203731"),
    "HOU": ("Texans", "#A71930"), "IND": ("Colts", "#002C5F"), "JAX": ("Jaguars", "#006778"),
    "KC": ("Chiefs", "#E31837"), "LV": ("Raiders", "#A5ACAF"), "LAC": ("Chargers", "#0080C6"),
    "LA": ("Rams", "#003594"), "MIA": ("Dolphins", "#008E97"), "MIN": ("Vikings", "#4F2683"),
    "NE": ("Patriots", "#C60C30"), "NO": ("Saints", "#D3BC8D"), "NYG": ("Giants", "#0B2265"),
    "NYJ": ("Jets", "#125740"), "PHI": ("Eagles", "#004C54"), "PIT": ("Steelers", "#FFB612"),
    "SF": ("49ers", "#AA0000"), "SEA": ("Seahawks", "#69BE28"), "TB": ("Buccaneers", "#D50A0A"),
    "TEN": ("Titans", "#4B92DB"), "WAS": ("Commanders", "#5A1414"),
}


def _get(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": "SharpCharts/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def load_games(season, refresh=True):
    """All games for a season from nflverse (cached to data/games.csv)."""
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, "games.csv")
    stale = not os.path.exists(path) or time.time() - os.path.getmtime(path) > 3600
    if refresh and stale:
        with open(path, "wb") as f:
            f.write(_get(NFLVERSE_URL))
    games = []
    for r in csv.DictReader(open(path)):
        if r["season"] != str(season):
            continue
        g = dict(r)
        for k in ("week", "away_score", "home_score", "result", "total"):
            g[k] = int(g[k]) if g[k] not in ("", "NA") else None
        for k in ("spread_line", "total_line", "away_moneyline", "home_moneyline"):
            g[k] = float(g[k]) if g[k] not in ("", "NA") else None
        g["final"] = g["home_score"] is not None
        games.append(g)
    return games


def espn_scoreboard(day):
    data = json.loads(_get(ESPN_URL.format(day.strftime("%Y%m%d"))))
    out = []
    for e in data.get("events", []):
        c = e["competitions"][0]
        side = {}
        for t in c["competitors"]:
            ab = ESPN_TO_NFLVERSE.get(t["team"]["abbreviation"], t["team"]["abbreviation"])
            side[t["homeAway"]] = (ab, t.get("score"))
        odds = (c.get("odds") or [{}])[0]
        out.append({
            "away": side["away"][0], "home": side["home"][0],
            "away_score": int(side["away"][1]) if side["away"][1] not in (None, "") else None,
            "home_score": int(side["home"][1]) if side["home"][1] not in (None, "") else None,
            "final": e["status"]["type"].get("completed", False),
            "details": odds.get("details"), "over_under": odds.get("overUnder"),
            "provider": (odds.get("provider") or {}).get("name"),
        })
    return out


def verify_scores(games):
    """Cross-check every final nflverse score against ESPN. Returns (checked, problems)."""
    finals = [g for g in games if g["final"]]
    days = sorted({g["gameday"] for g in finals})
    espn = {}
    for d in days:
        for e in espn_scoreboard(date.fromisoformat(d)):
            espn[(e["away"], e["home"])] = e
    problems = []
    for g in finals:
        e = espn.get((g["away_team"], g["home_team"]))
        if e is None:
            problems.append(f"{g['game_id']}: not found on ESPN")
        elif e["final"] and (e["away_score"], e["home_score"]) != (g["away_score"], g["home_score"]):
            problems.append(f"{g['game_id']}: nflverse {g['away_score']}-{g['home_score']} "
                            f"vs ESPN {e['away_score']}-{e['home_score']}")
    return len(finals), problems


def espn_lines_for_week(games, week):
    """Current DraftKings lines from ESPN for a week's games, keyed by game_id."""
    wk = [g for g in games if g["week"] == week]
    lines = {}
    for d in sorted({g["gameday"] for g in wk}):
        for e in espn_scoreboard(date.fromisoformat(d)):
            for g in wk:
                if (g["away_team"], g["home_team"]) == (e["away"], e["home"]):
                    lines[g["game_id"]] = e
    return lines


# ---------- bettor math ----------
# nflverse convention: result = home - away; spread_line > 0 means HOME favored by that many.

def ats_side(g, team):
    """'W', 'L' or 'P' against the spread for `team` in a final game."""
    margin = g["result"] - g["spread_line"]  # home cover margin
    if team == g["away_team"]:
        margin = -margin
    return "P" if margin == 0 else ("W" if margin > 0 else "L")


def ou_side(g):
    d = g["total"] - g["total_line"]
    return "P" if d == 0 else ("O" if d > 0 else "U")


def is_favorite(g, team):
    if g["spread_line"] == 0:
        return None
    home_fav = g["spread_line"] > 0
    return home_fav if team == g["home_team"] else not home_fav


def team_records(games):
    """Per-team ATS / O-U / straight-up records over final games."""
    rec = defaultdict(lambda: defaultdict(int))
    for g in games:
        if not g["final"] or g["spread_line"] is None:
            continue
        for t in (g["away_team"], g["home_team"]):
            r = rec[t]
            a = ats_side(g, t)
            r["ats_" + a] += 1
            o = ou_side(g)
            r["ou_" + o] += 1
            won = (g["result"] > 0) == (t == g["home_team"]) if g["result"] != 0 else None
            r["su_W" if won else ("su_T" if won is None else "su_L")] += 1
            pts_for = g["home_score"] if t == g["home_team"] else g["away_score"]
            pts_against = g["away_score"] if t == g["home_team"] else g["home_score"]
            exp_margin = g["spread_line"] if t == g["home_team"] else -g["spread_line"]
            r["cover_margin_sum"] += (pts_for - pts_against) - exp_margin
            r["ou_margin_sum"] += g["total"] - g["total_line"]
            r["games"] += 1
    return rec


def league_splits(games):
    """League-wide favorite/underdog, home/away, over/under splits."""
    s = defaultdict(int)
    for g in games:
        if not g["final"] or g["spread_line"] is None:
            continue
        home = ats_side(g, g["home_team"])
        if home != "P":
            s["home_" + home] += 1
            if g["spread_line"] != 0:
                fav_is_home = g["spread_line"] > 0
                fav_res = home if fav_is_home else ("W" if home == "L" else "L")
                s["fav_" + fav_res] += 1
                if not fav_is_home:
                    s["homedog_" + home] += 1
        s["ou_" + ou_side(g)] += 1
        # underdogs winning outright
        if g["spread_line"] != 0 and g["result"] != 0:
            fav_home = g["spread_line"] > 0
            s["dog_outright_" + ("W" if (g["result"] > 0) != fav_home else "L")] += 1
        s["games"] += 1
    return s


def last_final_week(games):
    weeks = [g["week"] for g in games if g["final"]]
    return max(weeks) if weeks else 0


def week_complete(games, week):
    return all(g["final"] for g in games if g["week"] == week)
