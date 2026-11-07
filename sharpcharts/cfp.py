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
    label = re.search(r"\b((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)\.? \d{1,2}) Top 4 Seeds", text)
    return (label.group(1) if label else ""), rows


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
    sub = f"{'First ' if first else ''}College Football Playoff rankings · {when}"
    cap = (
        f"The {'first ' if first else ''}College Football Playoff rankings are out 🏈 {lead['name']} is #1 at {lead['record']}.\n\n"
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
