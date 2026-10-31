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
    start: str = ""       # "YYYY-MM-DD": don't run before this date (lets a replacement job start the next day)


JOBS = [
    # ---- Oct 31: SharpCharts is a STATS page now (owner: "just raw data... like a stat page"). No betting framing,
    # fewer but better Reels. Every Reel opens on a bold claim (the #1 number), then counts down to who it is.
    # NFL: fantasy + usage (our best performers) and team scoring; NBA: nightly top scorers + weekly team stats.
    Job("st_fantasy",  "st_fantasy",  (MON,), "12:00", live=True, note="Reel: last week's top fantasy scorers (PPR)"),
    Job("v2_waiver",   "v2_waiver",   (TUE,), "12:00", live=True, note="Reel: waiver risers (share of team touches)"),
    Job("st_offense",  "st_offense",  (WED,), "12:00", live=True, note="Reel: highest-scoring NFL offenses"),
    Job("v2_rb",       "v2_rb",       (THU,), "12:00", live=True, note="Reel: RB share of team touches"),
    Job("st_margin",   "st_margin",   (FRI,), "12:00", live=True, note="Reel: biggest average winning margin (NFL)"),
    Job("st_board",    "st_board",    (SAT,), "09:00", live=True, start="2026-11-01", note="Reel: Find Your Team (all 32, point differential)"),
    Job("v2_wr",       "v2_wr",       (SUN,), "08:00", live=True, note="Reel: WR/TE share of team targets"),
    Job("nba_scorers", "nba_scorers", EVERY_DAY, "09:30", live=True, start="2026-11-01", note="Reel: last night's top NBA scorers"),
    Job("nba_board",   "nba_board",   (MON,), "15:00", live=True, note="Reel: NBA Find Your Team (all 30, point differential)"),
    Job("nba_offense", "nba_offense", (WED,), "15:00", live=True, note="Reel: highest-scoring NBA offenses"),
    Job("nba_margin",  "nba_margin",  (FRI,), "15:00", live=True, note="Reel: biggest average winning margin (NBA)"),
    # ---- Background: multi-sport line archive (never posts)
    Job("archive_am",   "archive",  EVERY_DAY, "06:00", live=True, note="Save lines + results"),
    Job("archive_pm",   "archive",  EVERY_DAY, "14:00", live=True, note="Save lines closer to game time"),
]
# Retired Oct 31 (stats page, no betting framing): v2_angles/best/worst/overs/upsets/all32/sunday, the Sunday
# game-day Story (betting lines), nba_night/best/worst/all30. Their builders still exist.
# Retired Oct 24 (reached ~5 people each or replaced by v2): NFL slate/recap/MNF images, primetime Stories,
# college football board, MLB Stories, old dark Reels. Their builders still exist if we want them back.
