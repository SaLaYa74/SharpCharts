"""The posting calendar. Edit this file to change what posts when; no workflow changes needed.

Times are US Pacific. Days: 0=Mon … 6=Sun.
live=True means PREVIEW: the post is built, checked and saved to GitHub for review,
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


JOBS = [
    # ---- NFL (feed)
    Job("nfl_recap",    "recap",    (TUE,), "09:00", live=True,  note="Weekly recap carousel"),
    Job("nfl_slate",    "slate",    (THU,), "10:00", live=True,  note="Week slate carousel"),
    Job("nfl_mnf",      "mnf",      (MON,), "10:00", live=True, note="Monday Night breakdown"),
    Job("nfl_trend",    "trend",    (FRI,), "11:00", live=True, note="Trend of the day"),
    # ---- Fantasy (feed): Wed RB opportunity, early Sun WR/TE target share
    Job("fantasy_wed",  "fantasy_rb",  (WED,), "08:00", live=True, note="RB opportunity share"),
    Job("fantasy_sun",  "fantasy_wr",  (SUN,), "06:00", live=True, note="WR/TE target share"),
    # ---- College football (Saturday)
    Job("cfb_story",    "cfb_story", (SAT,), "07:00", live=True, note="Top 25 board Story"),
    Job("cfb_feed",     "cfb",       (SAT,), "08:00", live=True, note="Top 25 board post"),
    # ---- MLB (postseason now; skips itself on days without games)
    Job("mlb_story",    "mlb_story", EVERY_DAY, "11:00", live=True, note="MLB tonight Story"),
    Job("mlb_feed",     "mlb",       (WED,), "10:00", live=True, note="MLB pitching matchups post"),
    # ---- NFL game-day Stories
    Job("nfl_tnf_story", "tnf_story",     (THU,), "15:00", live=True, note="TNF card Story"),
    Job("nfl_snf_story", "snf_story",     (SAT,), "17:00", live=True, note="SNF preview Story"),
    Job("nfl_gameday",   "gameday_story", (SUN,), "07:00", live=True, note="NFL Sunday slate Story"),
    Job("nfl_mnf_story", "mnf_story",     (MON,), "15:00", live=True, note="MNF card Story"),
    # ---- Reels (animated chart + original beat), shared to the feed
    Job("reel_ou",      "reel_ou",      (MON,), "12:00", live=True, note="Reel: over/under teams"),
    Job("reel_ats",     "reel_ats",     (TUE,), "12:00", live=True, note="Reel: best/worst ATS"),
    Job("reel_fantasy", "reel_fantasy", (THU,), "12:00", live=True, note="Reel: target share leaders"),
    Job("reel_trend",   "reel_trend",   (FRI,), "13:00", live=True, note="Reel: stat of the day"),
    # ---- Background: multi-sport line archive (never posts)
    Job("archive_am",   "archive",  EVERY_DAY, "06:00", live=True, note="Save lines + results"),
    Job("archive_pm",   "archive",  EVERY_DAY, "14:00", live=True, note="Save lines closer to game time"),
]
