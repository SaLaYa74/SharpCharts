"""The posting calendar. Edit this file to change what posts when; no workflow changes needed.

Times are US Pacific. Days: 0=Mon … 6=Sun.
live=False means PREVIEW: the post is built, checked and saved to GitHub for review,
but not published. Flip to True once approved.
A job that can't run (no games today, data not ready, checks failed) is retried
hourly for WINDOW_HOURS, then skipped for the day.
"""
from dataclasses import dataclass

WINDOW_HOURS = 6

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
    # ---- NFL (feed)
    Job("nfl_recap",    "recap",    (TUE,), "09:00", live=True,  note="Weekly recap carousel"),
    Job("nfl_slate",    "slate",    (THU,), "10:00", live=True,  note="Week slate carousel"),
    Job("nfl_mnf",      "mnf",      (MON,), "10:00", live=True, note="Monday Night breakdown"),
    # ---- College football (Saturday)
    Job("cfb_story",    "cfb_story", (SAT,), "07:00", live=True, note="Top 25 board Story"),
    Job("cfb_feed",     "cfb",       (SAT,), "08:00", live=True, note="Top 25 board post"),
    # ---- MLB (postseason now; skips itself on days without games)
    Job("mlb_story",    "mlb_story", EVERY_DAY, "11:00", live=True, note="MLB tonight Story"),
    # ---- NFL game-day Stories
    Job("nfl_tnf_story", "tnf_story",     (THU,), "15:00", live=True, note="TNF card Story"),
    Job("nfl_snf_story", "snf_story",     (SAT,), "17:00", live=True, note="SNF preview Story"),
    Job("nfl_gameday",   "gameday_story", (SUN,), "07:00", live=True, note="NFL Sunday slate Story"),
    Job("nfl_mnf_story", "mnf_story",     (MON,), "15:00", live=True, note="MNF card Story"),
    # ---- Reels: motion from frame 1, ~7s, glance mode, original beat (shared to the feed)
    # Time test: Reels alternate between 12:00 PT (3pm ET) and 16:00 PT (7pm ET); insights.py compares them.
    Job("reel_ou",         "reel_ou",         (MON,), "16:00", live=True, note="Reel: over/under teams (7pm ET)"),
    Job("reel_waiver",     "reel_waiver",     (TUE,), "12:00", live=True, note="Reel: waiver usage risers/fallers"),
    Job("reel_fantasy_rb", "reel_fantasy_rb", (WED,), "08:00", live=True, note="Reel: RB usage leaders"),
    Job("reel_ats",        "reel_ats",        (WED,), "16:00", live=True, note="Reel: best/worst ATS (7pm ET)"),
    Job("reel_fantasy",    "reel_fantasy_wr", (THU,), "12:00", live=True, note="Reel: WR/TE target share"),
    Job("reel_trend",      "reel_trend",      (FRI,), "16:00", live=True, note="Reel: stat of the day (7pm ET)"),
    Job("reel_onestat",    "reel_onestat",    (SAT,), "16:00", live=True, trial=True, note="Trial Reel: one big stat"),
    Job("reel_trend_sun",  "reel_onestat",    (SUN,), "08:00", live=True, note="Reel: game-day one big stat"),
    # ---- Background: multi-sport line archive (never posts)
    Job("archive_am",   "archive",  EVERY_DAY, "06:00", live=True, note="Save lines + results"),
    Job("archive_pm",   "archive",  EVERY_DAY, "14:00", live=True, note="Save lines closer to game time"),
]
