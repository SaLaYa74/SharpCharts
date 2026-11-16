"""College Football Playoff committee rankings (owner, Nov 6: "throw in some college football playoff stuff").

Two independent copies of the same ranking must agree before anything posts: ESPN's rankings feed (the
"Playoff Committee Rankings" poll) and the official site, collegefootballplayoff.com. Every rank, school and
record has to match, the release dates have to match, and the ranking must be fresh (posted within days).

Keys start "cfp-", never "cfb": voice.py gives "cfb" posts a betting-era opener line.
"""
import html
import json
import re
from datetime import date, datetime, timedelta, timezone

from . import checks as C
from . import light as L
from .data import _get
from .logos import logo_uri
from .posts import DataError, NoContent, already_posted
from .v2 import _post

ESPN = "https://site.api.espn.com/apis/site/v2/sports/football/college-football/rankings"
OFFICIAL = "https://collegefootballplayoff.com/rankings"
TOP = 10                     # the Reel counts down the Top 10; the caption lists all 25
FRESH_DAYS = 5               # a ranking older than this is old news
# How the official site spells schools that ESPN spells differently (compared lower-case).
ALIASES = {"miami (fla.)": "miami", "miami (fl)": "miami", "southern california": "usc", "ole miss": "ole miss",
           "brigham young": "byu", "louisiana state": "lsu", "texas christian": "tcu", "southern methodist": "smu",
           "central florida": "ucf", "mississippi": "ole miss", "nc state": "nc state"}
TAGS = "#collegefootball #cfb #cfp #collegefootballplayoff"


def _norm(name):
    n = re.sub(r"\s+", " ", name.strip().lower().replace("&amp;", "&"))
    return ALIASES.get(n, n)


def espn_ranking():
    """(release date, [dict(rank, name, abbr, id, record, previous)]) from ESPN's CFP poll."""
    d = json.loads(_get(ESPN))
    poll = next((p for p in d.get("rankings", []) if p.get("type") == "cfp"), None)
    if not poll:
        raise NoContent("No CFP committee ranking in ESPN's feed (season not there yet).")
    rows = [{"rank": r["current"], "name": r["team"].get("location") or r["team"]["name"],
             "abbr": r["team"].get("abbreviation", ""), "id": r["team"]["id"], "record": r.get("recordSummary", ""),
             "previous": r.get("previous", 0)} for r in poll.get("ranks", [])]
    released = datetime.fromisoformat(poll["date"].replace("Z", "+00:00")).date()
    return released, rows


def official_ranking():
    """(date label like 'Nov. 3', [(rank, school, record)]) scraped from collegefootballplayoff.com's text."""
    page = _get(OFFICIAL).decode("utf-8", "replace")
    text = html.unescape(re.sub(r"<[^>]+>", " ", re.sub(r"<(script|style)\b.*?</\1>", " ", page, flags=re.S)))
    text = re.sub(r"\s+", " ", text)
    i = text.find("Full Rankings")
    if i < 0:
        raise DataError("collegefootballplayoff.com: 'Full Rankings' section not found (page layout changed?)")
    seg = text[i + len("Full Rankings"):i + 3000]
    rows = [(int(r), s.strip(), rec) for r, s, rec in re.findall(r"\b(\d{1,2}) ([A-Z][\w.&'() -]*?) (\d{1,2}-\d{1,2})\b", seg)]
    # The week menu sits just before "Top 4 Seeds", newest first ("... 2014 Nov. 10 Nov. 3 Top 4 Seeds"), and the page
    # shows the newest week. Nov 11: this used to take the label nearest "Top 4 Seeds", i.e. the OLDEST week.
    k = text.find("Top 4 Seeds")
    weeks = re.findall(r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)\.? \d{1,2}\b", text[max(0, k - 200):k]) if k >= 0 else []
    return (weeks[0] if weeks else ""), rows


def checked_ranking(rep, today=None):
    """The ranking both sources agree on, or DataError/NoContent. Returns (release date, rows)."""
    today = today or datetime.now(timezone.utc).date()
    released, espn = espn_ranking()
    label, official = official_ranking()
    rep.require(len(espn) == 25, "cfp: ESPN has 25 teams", f"{len(espn)} teams")
    rep.require([r for r, _, _ in official[:25]] == list(range(1, 26)), "cfp: official site lists ranks 1-25 in order",
                f"ranks {[r for r, _, _ in official[:25]]}")
    rep.require(label.replace(".", "").replace("Sept", "Sep") == f"{released:%b} {released.day}",
                "cfp: both sources show the same release date",
                f"ESPN {released} vs official '{label}'")
    for e, (rank, school, rec) in zip(espn, official[:25]):
        rep.require(e["rank"] == rank and _norm(e["name"]) == _norm(school) and e["record"] == rec,
                    f"cfp: #{e['rank']} {e['name']} {e['record']} matches the official site",
                    f"ESPN #{e['rank']} {e['name']} {e['record']} vs official #{rank} {school} {rec}")
        w, l_ = map(int, e["record"].split("-"))
        rep.require(0 <= l_ <= w + l_ <= 15, f"cfp: {e['name']} record plausible", e["record"])
    if not rep.ok:
        raise DataError("CFP ranking: ESPN and collegefootballplayoff.com disagree; see checks.")
    if (today - released).days > FRESH_DAYS:
        raise NoContent(f"Latest CFP ranking is from {released}; nothing new.")
    return released, espn


def last_week_number_one():
    """The #1 team in our most recent posted CFP Reel (its caption's '1. Team (record)' line), or None."""
    import glob
    import os
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    caps = sorted(glob.glob(os.path.join(root, "media", "*_cfp_rankings", "caption.txt")))
    for path in reversed(caps):
        m = re.search(r"^1\. (.+?) \(\d{1,2}-\d{1,2}\)$", open(path).read(), re.M)
        if m:
            return m.group(1)
    return None


def cfp_rankings(out_dir):
    rep = C.Report("cfp rankings")
    released, rows = checked_ranking(rep)
    first = all(not r["previous"] for r in rows)                  # no previous ranks = the season's first ranking
    top = rows[:TOP]
    unbeaten = [r for r in rows if r["record"].endswith("-0")]
    lad = [{"rank": r["rank"], "logo": logo_uri(str(r["id"]), "ncaa"), "name": r["name"], "record": r["record"],
            "tag": "UNBEATEN" if r["record"].endswith("-0") else ""} for r in top]
    when = f"{released:%b} {released.day}"
    key = f"cfp-rankings-{released:%Y-%m-%d}"
    already_posted(key)
    lead = rows[0]
    title, hl = ("{hl} and #1.\nGuess Who?", lead["record"]) if lead["record"].endswith("-0") else ("Who's {hl}?", "#1")
    # Nov 11: when last week's #1 has fallen, that's the headline ("Last Week's #1 Is Now #7"). ESPN's previous-rank
    # field must agree with the #1 in our own verified post from last week, or we don't make the claim.
    fallen = next((r for r in rows if r["previous"] == 1 and r["rank"] != 1), None)
    if fallen and last_week_number_one() == fallen["name"]:
        rep.add(C.PASS, "cfp: last week's #1 matches our previous post", fallen["name"])
        title, hl = "Last Week's #1\nIs Now {hl}", f"#{fallen['rank']}"
    else:
        fallen = None
    sub = f"{'First ' if first else ''}College Football Playoff rankings · {when}"
    cap = (
        f"The {'first ' if first else ''}College Football Playoff rankings are out 🏈 {lead['name']} is #1 at {lead['record']}."
        + (f" Last week's #1, {fallen['name']}, fell to #{fallen['rank']} 😳" if fallen else "") + "\n\n"
        + "\n".join(f"{r['rank']}. {r['name']} ({r['record']})" for r in rows)
        + (f"\n\nStill unbeaten in the Top 25: {', '.join(r['name'] for r in unbeaten)}." if unbeaten else "")
        + "\n\nWho's ranked too high? Who got robbed? 👇"
        + "\n\n📤 Send this to the fan who swears their team is underrated."
        + f"\n\nCFP committee rankings released {when}; records as of the release."
        + "\nData: ESPN rankings feed, every rank, school and record matched against collegefootballplayoff.com."
        + f"\n{TAGS}")
    C.caption(rep, cap)
    return _post(out_dir, key, "cfp_rankings", lambda r, t: L.ladder(
        title, hl, sub, lad, "CFP committee via ESPN · checked vs collegefootballplayoff.com", reveal=r, tease=t),
        cap, rep, countdown=len(lad))


BUILDERS = {"cfp_rankings": cfp_rankings}


# ---------------------------------------------------------------- Top 25 offense vs defense (Jarvis, Nov 16)
# The College Football Playoff Top 25 as a logo scatter: points scored vs allowed per game. Every team's games,
# points scored and points allowed must match exactly between ESPN (each team's schedule, game by game) and NCAA.com
# (official FBS scoring offense + scoring defense tables), or the post is blocked. The ranking itself is the same
# two-source checked ranking as cfp_rankings.
TEAM_SCHED = "https://site.api.espn.com/apis/site/v2/sports/football/college-football/teams/{}/schedule"
NCAA_STATS = "https://www.ncaa.com/stats/football/fbs/current/team/{}{}"     # 27 = scoring offense, 28 = scoring defense
NCAA_ALIASES = {"southern california": "usc", "army west point": "army", "miami (fl)": "miami", "ole miss": "ole miss",
                "app state": "appalachian state", "fiu": "florida international", "uconn": "uconn",
                "ga. southern": "georgia southern", "ucf": "ucf", "smu": "smu", "tcu": "tcu", "byu": "byu", "lsu": "lsu"}


def _ncaa_norm(name):
    n = re.sub(r"\s+", " ", html.unescape(name).strip().lower())
    n = NCAA_ALIASES.get(n, n)
    return re.sub(r" st\.$", " state", n)


def _ncaa_table(stat):
    """{normalized school: (games, total points)} from every page of an NCAA.com FBS team-stat table."""
    out, page = {}, ""
    for i in range(1, 6):
        s = _get(NCAA_STATS.format(stat, page)).decode("utf-8", "replace")
        head = re.search(r"<thead>(.*?)</thead>", s, re.S)
        cols = [re.sub(r"<[^>]+>", "", c).strip() for c in re.findall(r"<th[^>]*>(.*?)</th>", head.group(1), re.S)] if head else []
        if "Team" not in cols or "G" not in cols or "Pts" not in cols:
            raise DataError(f"NCAA.com stat {stat}: table columns changed ({cols})")
        rows = re.findall(r"<tr>(.*?)</tr>", re.search(r"<tbody>(.*?)</tbody>", s, re.S).group(1), re.S)
        for r in rows:
            cells = [re.sub(r"<[^>]+>", "", c).strip() for c in re.findall(r"<td[^>]*>(.*?)</td>", r, re.S)]
            if len(cells) == len(cols):
                row = dict(zip(cols, cells))
                out[_ncaa_norm(row["Team"])] = (int(row["G"]), int(float(row["Pts"].replace(",", ""))))
        if f"/team/{stat}/p{i + 1}\"" not in s:
            break
        page = f"/p{i + 1}"
    return out


def _espn_points(team_id):
    """(games, points for, points against, last game date, color) from ESPN's game-by-game schedule (completed games)."""
    d = json.loads(_get(TEAM_SCHED.format(team_id)))
    g = pf = pa = 0
    last = None
    for e in d.get("events", []):
        c = e["competitions"][0]
        if not c["status"]["type"].get("completed"):
            continue
        us = next(x for x in c["competitors"] if x["team"]["id"] == str(team_id))
        them = next(x for x in c["competitors"] if x["team"]["id"] != str(team_id))
        g += 1
        pf += int(us["score"]["value"])
        pa += int(them["score"]["value"])
        last = max(last or e["date"], e["date"])
    return g, pf, pa, last, "#" + (d.get("team", {}).get("color") or "3A4A6B")


def top25_scatter(out_dir, rows, released, poll_label, rep):
    """rows: the checked ranking (dicts with rank, name, id). Builds the scatter Reel."""
    QUADS = ("ELITE AT BOTH", "DEFENSE FIRST", "ALL OFFENSE", "BELOW AVG")    # vs the Top 25 average
    off, dfn = _ncaa_table(27), _ncaa_table(28)
    rep.require(len(off) >= 120 and len(dfn) >= 120, "ncaa: full FBS scoring tables loaded",
                f"{len(off)} offense rows, {len(dfn)} defense rows")
    t, last = {}, None
    for r in rows:
        g, pf, pa, when, color = _espn_points(r["id"])
        k = _ncaa_norm(r["name"])
        if not rep.require(k in off and k in dfn, f"ncaa: {r['name']} found on NCAA.com", f"no NCAA.com row for {k!r}"):
            continue
        (go, po), (gd, pd) = off[k], dfn[k]
        rep.require(g == go == gd and pf == po and pa == pd, f"{r['name']}: games and points match (ESPN vs NCAA.com)",
                    f"ESPN {g} g, {pf}-{pa} vs NCAA.com {go} g {po} scored, {gd} g {pd} allowed")
        rep.require(8 <= pf / max(g, 1) <= 60 and 3 <= pa / max(g, 1) <= 45, f"{r['name']}: per-game points plausible",
                    f"{pf / max(g, 1):.1f} scored, {pa / max(g, 1):.1f} allowed")
        t[r["id"]] = {"name": r["name"], "rank": r["rank"], "g": g, "ppg": pf / g if g else 0, "papg": pa / g if g else 0,
                      "color": color}
        last = max(last or when, when)
    rep.require(len(t) == len(rows) == 25, "cfp scatter: all 25 ranked teams plotted", f"{len(t)} of {len(rows)}")
    if not rep.ok:
        raise DataError("CFP scatter: ESPN and NCAA.com disagree; see checks.")
    ax = sum(r["ppg"] for r in t.values()) / len(t)
    ay = sum(r["papg"] for r in t.values()) / len(t)
    both = sorted((i for i, r in t.items() if r["ppg"] > ax and r["papg"] < ay), key=lambda i: t[i]["rank"])
    if not both:
        raise NoContent("No ranked team is above the Top 25 average on both sides.")
    best_o = max(t, key=lambda i: (t[i]["ppg"], -t[i]["rank"]))
    best_d = min(t, key=lambda i: (t[i]["papg"], t[i]["rank"]))
    thru = datetime.fromisoformat(last.replace("Z", "+00:00")).astimezone(timezone(timedelta(hours=-5))).date()
    pts = [{"x": r["ppg"], "y": r["papg"], "abbr": r["name"][:4].upper(), "logo": logo_uri(i, "ncaa"), "color": r["color"]}
           for i, r in t.items()]
    n = len(both)
    title = "Only {hl} of the Top 25\nAre Elite at Both" if n <= 8 else "{hl} of the Top 25\nAre Elite at Both"
    name = lambda i: f"#{t[i]['rank']} {t[i]['name']}"
    cap = (
        f"{'Only ' if n <= 8 else ''}{n} of the College Football Playoff Top 25 score more AND allow less than the "
        f"Top 25 average ({ax:.1f} scored, {ay:.1f} allowed per game) 👀\n\n"
        f"🟢 Elite at both: {', '.join(name(i) for i in both)}\n\n"
        f"Best offense: {name(best_o)}, {t[best_o]['ppg']:.1f} points a game. "
        f"Best defense: {name(best_d)}, {t[best_d]['papg']:.1f} allowed.\n\n"
        "Most complete team in the country? Who's ranked on reputation? 👇"
        "\n\n📤 Send this to the fan who swears their team is underrated."
        f"\n\n{poll_label} ({released:%b} {released.day}). Points per game, all games through {thru:%b} {thru.day}."
        "\nData: ESPN game-by-game scores, every team's games and points matched against NCAA.com's official FBS stats."
        f"\n{TAGS}")
    C.caption(rep, cap)
    key = f"cfp-scatter-{released:%Y-%m-%d}"
    return _post(out_dir, key, "cfp_scatter", lambda p: L.scatter(
        title, str(n), f"Above the Top 25 average on offense and defense · thru {thru:%b} {thru.day}", pts,
        "Points scored per game →", "Points allowed per game (fewer = higher) →",
        "ESPN · checked vs NCAA.com", (ax, ay), QUADS, p=p), cap, rep, hold=5.0)


def cfp_scatter(out_dir):
    rep = C.Report("cfp scatter")
    released, rows = checked_ranking(rep)
    key = f"cfp-scatter-{released:%Y-%m-%d}"
    already_posted(key)
    return top25_scatter(out_dir, rows, released, "College Football Playoff committee Top 25", rep)


BUILDERS["cfp_scatter"] = cfp_scatter
