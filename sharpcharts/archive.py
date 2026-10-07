"""Daily snapshots of every sport's lines and results from ESPN (DraftKings odds).

Builds our own verified betting history for sports without a free historical source,
so future ATS/O-U trends for NBA, NHL, MLB and college can be computed from data we
captured ourselves. Never posts anything.
"""
import json
import os
from datetime import date, datetime, timedelta, timezone

from .data import _get

SPORTS = {
    "nfl": "football/nfl",
    "cfb": "football/college-football",
    "nba": "basketball/nba",
    "ncaab": "basketball/mens-college-basketball",
    "nhl": "hockey/nhl",
    "mlb": "baseball/mlb",
}
EXTRA = {"cfb": "&groups=80&limit=300", "ncaab": "&groups=50&limit=400"}


def _event(e):
    comp = e["competitions"][0]
    o = (comp.get("odds") or [{}])[0]
    teams = {}
    for c in comp["competitors"]:
        teams[c["homeAway"]] = {"abbr": c["team"].get("abbreviation"), "name": c["team"].get("displayName"),
                                "score": c.get("score"), "rank": (c.get("curatedRank") or {}).get("current")}
    return {"id": e["id"], "date": e["date"], "state": e["status"]["type"]["state"],
            "completed": e["status"]["type"].get("completed", False), "teams": teams,
            "odds": {"provider": (o.get("provider") or {}).get("name"), "details": o.get("details"),
                     "spread": o.get("spread"), "over_under": o.get("overUnder"),
                     "home_ml": (o.get("homeTeamOdds") or {}).get("moneyLine"),
                     "away_ml": (o.get("awayTeamOdds") or {}).get("moneyLine")} if o else None}


def snapshot(root, today=None):
    """Save yesterday's results and today's lines for every sport. Returns files written."""
    today = today or date.today()
    stamp = datetime.now(timezone.utc).strftime("%H%MZ")
    written = []
    for sport, path in SPORTS.items():
        for day in (today - timedelta(days=1), today):
            url = (f"https://site.api.espn.com/apis/site/v2/sports/{path}/scoreboard"
                   f"?dates={day.strftime('%Y%m%d')}{EXTRA.get(sport, '')}")
            try:
                events = json.loads(_get(url)).get("events", [])
            except Exception as ex:  # one sport failing never stops the others
                print(f"  ! archive {sport} {day}: {ex}")
                continue
            if not events:
                continue
            out = os.path.join(root, "archive", sport, f"{day.isoformat()}_{stamp}.json")
            os.makedirs(os.path.dirname(out), exist_ok=True)
            with open(out, "w") as f:
                json.dump({"sport": sport, "day": day.isoformat(), "captured_utc": stamp,
                           "source": "ESPN scoreboard (DraftKings odds)", "events": [_event(e) for e in events]},
                          f, separators=(",", ":"))
            written.append(out)
    return written
