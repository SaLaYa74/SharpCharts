"""The posting calendar. Edit this file to change what posts when; no workflow changes needed.

Times are US Pacific. Days: 0=Mon … 6=Sun.
live=False means PREVIEW: the post is built, checked and saved to GitHub for review,
but not published. Flip to True once approved.
A job that can't run (no games today, data not ready, checks failed) is retried
hourly for WINDOW_HOURS, then skipped for the day.
"""
from dataclasses import dataclass

WINDOW_HOURS = 12

MON, TUE, WED, THU, FRI, SAT, SUN = range(7)
EVERY_DAY = (MON, TUE, WED, THU, FRI, SAT, SUN)


@dataclass(frozen=True)
class Job:
    name: str          # unique job id
    builder: str       # key in posts.BUILDERS / sports.BUILDERS, or "archive"
    days: tuple
    time: str          # "HH:MM" Pacific
    live: bool = False
    note: str = ""
    trial: bool = False   # Reels only: post as a Trial Reel (non-followers first)


JOBS = [
    # ---- v2 (Oct 24 rework): plain-English Reels (two on Tue/Sat since Oct 26: share-bait formats), light design, team badges, $100-bet framing.
    # Midday Reels reached ~54% more people than evening in the Oct 2026 test, so everything posts at noon PT.
    Job("v2_angles",  "v2_angles", (MON,), "12:00", live=True, note="Reel: Which bet pays? (favs/dogs/home/road/overs/unders)"),
    Job("v2_upsets",  "v2_upsets", (TUE,), "09:00", live=True, note="Reel: underdogs that paid last week ($100 moneyline)"),
    Job("v2_waiver",  "v2_waiver", (TUE,), "12:00", live=True, note="Reel: waiver wire risers"),
    Job("v2_best",    "v2_best",   (WED,), "12:00", live=True, note="Reel: best teams to bet on ($100 every game)"),
    Job("v2_rb",      "v2_rb",     (THU,), "12:00", live=True, note="Reel: who gets the ball (RB touch share)"),
    Job("v2_worst",   "v2_worst",  (FRI,), "12:00", live=True, note="Reel: worst teams to bet on"),
    Job("v2_all32",   "v2_all32",  (SAT,), "09:00", live=True, note="Reel: find your team (all 32, $100 every game)"),
    Job("v2_overs",   "v2_overs",  (SAT,), "12:00", live=True, note="Reel: best teams for the over"),
    Job("v2_wr",      "v2_wr",     (SUN,), "08:00", live=True, note="Reel: who gets targeted (WR/TE target share)"),
    # ---- Moments, not the calendar: same-day recap while people are still talking about the games.
    # Waits (retries hourly) until every afternoon game is final; ESPN scores, nflverse lines.
    Job("v2_sunday",  "v2_sunday", (SUN,), "17:30", live=True, note="Reel: Sunday in $ (today's favorites/dogs/overs/unders)"),
    # ---- NBA (Oct 26): year-round content once football ends. Same $100 math, DraftKings closing lines via ESPN.
    # Nightly recap the next morning; season leaderboards on days with only one NFL Reel, before tip-off.
    Job("nba_night",  "nba_night", EVERY_DAY, "09:30", live=True, note="Reel: NBA last night in $ (favs/dogs/home/road/overs/unders)"),
    Job("nba_all30",  "nba_all30", (MON,), "15:00", live=True, note="Reel: NBA find your team (all 30, $100 every game)"),
    Job("nba_best",   "nba_best",  (WED,), "15:00", live=True, note="Reel: NBA teams that paid bettors most"),
    Job("nba_worst",  "nba_worst", (FRI,), "15:00", live=True, note="Reel: NBA teams that burned bettors most"),
    # ---- Game-day Story (cheap, keeps followers engaged on Sundays)
    Job("nfl_gameday", "gameday_story", (SUN,), "07:00", live=True, note="NFL Sunday slate Story"),
    # ---- Background: multi-sport line archive (never posts)
    Job("archive_am",   "archive",  EVERY_DAY, "06:00", live=True, note="Save lines + results"),
    Job("archive_pm",   "archive",  EVERY_DAY, "14:00", live=True, note="Save lines closer to game time"),
]
# Retired Oct 24 (reached ~5 people each or replaced by v2): NFL slate/recap/MNF images, primetime Stories,
# college football board, MLB Stories, old dark Reels. Their builders still exist if we want them back.
