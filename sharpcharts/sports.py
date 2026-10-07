"""College football and MLB posts.

CFB : ESPN scoreboard (DraftKings lines), ranks cross-checked against the AP / Coaches polls.
MLB : MLB Stats API (official: schedule, probable pitchers, series status, pitcher stats)
      cross-checked against ESPN's scoreboard (teams + start times) for DraftKings lines.
"""
import json
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from . import checks as C
from . import templates as T
from .data import _get
from .posts import DISCLAIMER, DataError, NoContent, Post, _render, with_question

ET = ZoneInfo("America/New_York")
ESPN = "https://site.api.espn.com/apis/site/v2/sports/{}/scoreboard?dates={}{}"

# Extra unranked CFB games to include this week, by "AWAY@HOME" ESPN abbreviations.
# Edit when something big is happening outside the Top 25.
CFB_EXTRA = set()


def _json(url):
    return json.loads(_get(url))


def _et(iso):
    return datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(ET)


def _kick(dt):
    return dt.strftime("%a ") + dt.strftime("%I:%M %p").lstrip("0") + " ET"


def _color(team):
    c = team.get("color") or "3A4A6B"
    if c.lower() in ("000000", "111111", "222222"):
        c = team.get("alternateColor") or "3A4A6B"
    return "#" + c


def _odds(comp):
    o = (comp.get("odds") or [{}])[0]
    return o.get("details"), o.get("overUnder"), (o.get("provider") or {}).get("name")


# ---------------------------------------------------------------- college football

def cfb_slate(out_dir, sizes=("feed",), day=None, media="feed"):
    day = day or date.today()
    data = _json(ESPN.format("football/college-football", day.strftime("%Y%m%d"), "&groups=80&limit=300"))
    polls = _json("https://site.api.espn.com/apis/site/v2/sports/football/college-football/rankings")
    poll_ranks = {}
    for p in polls.get("rankings", []):
        if p.get("type") in ("ap", "usa", "cfp"):
            for r in p.get("ranks", []):
                poll_ranks.setdefault(r["team"].get("abbreviation"), set()).add(r["current"])
    rep = C.Report("cfb slate")
    rep.require(bool(poll_ranks), "cfb: polls loaded", "could not load AP/Coaches polls")
    now = datetime.now(ET)
    games = []
    for e in data.get("events", []):
        comp = e["competitions"][0]
        side = {c["homeAway"]: c for c in comp["competitors"]}
        ranks = {k: (side[k].get("curatedRank") or {}).get("current", 99) for k in side}
        abbr = {k: side[k]["team"]["abbreviation"] for k in side}
        tag = f"{abbr['away']}@{abbr['home']}"
        if not (min(ranks.values()) <= 25 or tag in CFB_EXTRA):
            continue
        kick = _et(e["date"])
        if e["status"]["type"]["state"] != "pre" or kick < now:
            continue
        for k in side:
            if ranks[k] <= 25:
                rep.require(ranks[k] in poll_ranks.get(abbr[k], set()), f"cfb: #{ranks[k]} {abbr[k]} matches a poll",
                            f"ESPN rank #{ranks[k]} for {abbr[k]} not found in AP/Coaches polls")
        details, ou, provider = _odds(comp)
        if not details or ou is None:
            rep.expect(False, f"cfb: {tag} has a line", "no line posted, left off")
            continue
        try:
            spread = abs(float(details.rpartition(" ")[2])) if details.upper() not in ("EVEN", "PK") else 0
        except ValueError:
            rep.expect(False, f"cfb: {tag} line readable", f"unreadable line '{details}', left off")
            continue
        C.line_ranges(rep, "cfb", tag, spread, float(ou))
        fav = details.rpartition(" ")[0]

        def team(k):
            t = side[k]["team"]
            r = ranks[k]
            return {"abbr": abbr[k][:4], "color": _color(t), "rank": r if r <= 25 else None,
                    "name": (f"#{r} " if r <= 25 else "") + t.get("shortDisplayName", t["displayName"]),
                    "detail": t.get("location", ""), "line": details.rpartition(" ")[2] if abbr[k] == fav else ""}
        games.append({"kick": _kick(kick), "dt": kick, "headline": "Top 25" if min(ranks.values()) <= 25 else "Spotlight",
                      "away": team("away"), "home": team("home"), "total": f"{float(ou):g}", "details": details,
                      "rank": min(ranks.values()), "quality": sum(min(r, 40) for r in ranks.values()),
                      "provider": provider})
    if not data.get("events"):
        raise NoContent(f"No college football games on {day}.")
    rep.require(len(games) >= 3, "cfb: enough verified games", f"only {len(games)} games passed checks")
    # Biggest matchups: best combined ranking (unranked counts as 40), then closest spread.
    games.sort(key=lambda g: (g["quality"], abs(float(g["details"].rpartition(" ")[2] or 0) if g["details"][-1].isdigit() else 0)))
    games = sorted(games[:8 if media == "feed" else 10], key=lambda g: g["dt"])
    size = "story" if media == "story" else "feed"
    rows = [{"kick": g["kick"].replace(" ET", ""), "away": (g["away"]["abbr"], g["away"]["color"], g["away"]["rank"]),
             "home": (g["home"]["abbr"], g["home"]["color"], g["home"]["rank"]), "spread": g["details"], "total": g["total"]} for g in games]
    img = _render(lambda s: T.slate(0, rows, tag="CFB · Top 25", source="ESPN · DraftKings lines", size=s,
                                    title_html="College football<br><em>Top 25 board</em>",
                                    subtitle=f"{day.strftime('%A %b %-d')} · spreads &amp; totals (ET)",
                                    note="Ranks: AP Top 25 · lines move, check your book"),
                  out_dir, f"cfb_{media}", (size,))
    key = f"{day.isoformat()}-cfb-{media}"
    lines = "\n".join(f"{g['away']['name']} @ {g['home']['name']}: {g['details']}, O/U {g['total']}" for g in games)
    caption = with_question(f"College football Saturday 🏈\n\nThe Top 25 board:\n{lines}", "cfb", key)
    caption += f"\n\nLines: DraftKings via ESPN. Lines move, so check your book.\n{DISCLAIMER}\n#cfb #collegefootball #cfbbetting #sportsbetting #top25"
    return Post(key=key, caption=caption, images=[img], media=media, checks=rep)


# ---------------------------------------------------------------- MLB

def _pitcher(pid, season):
    if not pid:
        return None
    d = _json(f"https://statsapi.mlb.com/api/v1/people/{pid}/stats?stats=season&group=pitching&season={season}")
    splits = (d.get("stats") or [{}])[0].get("splits") or []
    return splits[0]["stat"] if splits else None


def mlb_tonight(out_dir, sizes=("story",), day=None, media="story"):
    day = day or date.today()
    sched = _json("https://statsapi.mlb.com/api/v1/schedule?sportId=1&date=" + day.isoformat()
                  + "&gameType=R,F,D,L,W&hydrate=probablePitcher,team,seriesStatus")
    mlb_games = [g for d in sched.get("dates", []) for g in d["games"]]
    if not mlb_games:
        raise NoContent(f"No MLB games on {day}.")
    espn = _json(ESPN.format("baseball/mlb", day.strftime("%Y%m%d"), ""))
    by_names = {}
    for e in espn.get("events", []):
        comp = e["competitions"][0]
        side = {c["homeAway"]: c["team"] for c in comp["competitors"]}
        by_names[(side["away"]["displayName"], side["home"]["displayName"])] = (e, comp, side)
    rep = C.Report("mlb tonight")
    now = datetime.now(ET)
    games = []
    for g in mlb_games:
        t = g["teams"]
        names = (t["away"]["team"]["name"], t["home"]["team"]["name"])
        label = f"{t['away']['team']['abbreviation']}@{t['home']['team']['abbreviation']}"
        if g["status"]["abstractGameState"] != "Preview":
            continue
        match = by_names.get(names)
        if not rep.require(match is not None, f"mlb: {label} found on ESPN", "game missing from ESPN, left off"):
            continue
        e, comp, side = match
        start_mlb, start_espn = _et(g["gameDate"]), _et(e["date"])
        if not rep.require(abs((start_mlb - start_espn).total_seconds()) <= 1800, f"mlb: {label} start time agrees",
                           f"MLB {start_mlb:%H:%M} vs ESPN {start_espn:%H:%M}"):
            continue
        details, ou, provider = _odds(comp)
        if not details or ou is None:
            rep.expect(False, f"mlb: {label} has a line", "no line yet, left off")
            continue
        fav, _, ml = details.rpartition(" ")
        try:
            ml = int(float(ml))
        except ValueError:
            rep.expect(False, f"mlb: {label} line readable", f"'{details}' unreadable, left off")
            continue
        C.line_ranges(rep, "mlb", label, total=float(ou), moneylines=(ml,))

        def team(k):
            tm = t[k]["team"]
            sp = t[k].get("probablePitcher") or {}
            st = _pitcher(sp.get("id"), day.year)
            rep.expect(bool(sp), f"mlb: {label} {k} starter announced", "starter TBD")
            pdesc = (f"SP {sp.get('fullName')}" + (f" · {st.get('era')} ERA · {st.get('whip')} WHIP" if st else "")) if sp else "SP TBD"
            espn_abbr = side[k]["abbreviation"]
            return {"abbr": tm["abbreviation"], "color": _color(side[k]), "name": tm["teamName"], "detail": pdesc,
                    "line": f"{ml:+d}" if espn_abbr == fav else "", "sp": sp.get("fullName", "TBD")}
        series = (g.get("seriesStatus") or {})
        games.append({"kick": _kick(start_mlb), "dt": start_mlb,
                      "headline": series.get("result") or series.get("shortDescription") or "",
                      "away": team("away"), "home": team("home"), "total": f"{float(ou):g}",
                      "series": series.get("description", ""), "details": details})
    if not games and not any(g["status"]["abstractGameState"] == "Preview" for g in mlb_games):
        raise NoContent("All of today's MLB games have started or finished.")
    rep.require(len(games) >= 1, "mlb: at least one verified game", "no games passed checks")
    games.sort(key=lambda g: g["dt"])
    games = games[:6]
    size = "story" if media == "story" else "feed"
    post_season = any(g["series"] for g in games)
    title = "MLB playoffs<br><em>tonight</em>" if post_season else "MLB<br><em>tonight</em>"
    img = _render(lambda s: T.game_blocks(title, f"{day.strftime('%A %b %-d')} · moneyline favorite &amp; total",
                                          games, tag="MLB" + (" · Postseason" if post_season else ""),
                                          source="MLB Stats API · ESPN/DraftKings", size=s,
                                          note="Starters &amp; series: MLB official · lines move"),
                  out_dir, f"mlb_{media}", (size,))
    key = f"{day.isoformat()}-mlb-{media}"
    lines = "\n".join(f"{g['away']['name']} ({g['away']['sp']}) @ {g['home']['name']} ({g['home']['sp']}): "
                      f"{g['details']}, O/U {g['total']}" for g in games)
    caption = with_question(f"{'MLB playoffs' if post_season else 'MLB'} tonight ⚾\n\n{lines}", "mlb", key)
    caption += f"\n\nStarters: MLB official. Lines: DraftKings via ESPN.\n{DISCLAIMER}\n#mlb #mlbplayoffs #mlbbetting #sportsbetting #baseball"
    return Post(key=key, caption=caption, images=[img], media=media, checks=rep)


BUILDERS = {
    "cfb": lambda out_dir, **kw: cfb_slate(out_dir, media="feed", **kw),
    "cfb_story": lambda out_dir, **kw: cfb_slate(out_dir, media="story", **kw),
    "mlb": lambda out_dir, **kw: mlb_tonight(out_dir, media="feed", **kw),
    "mlb_story": lambda out_dir, **kw: mlb_tonight(out_dir, media="story", **kw),
}
