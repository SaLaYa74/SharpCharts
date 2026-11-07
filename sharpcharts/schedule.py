"""The posting calendar. Edit this file to change what posts when; no workflow changes needed.

Times are US Pacific. Days: 0=Mon … 6=Sun.
live=False means PREVIEW: the post is built, checked and saved to GitHub for review,
but not published. Flip to True once approved.
A job that can't run (no games today, data not ready, checks failed) is retried
hourly for WINDOW_HOURS, then skipped for the day.
"""
from dataclasses import dataclass

WINDOW_HOURS = 12
MAX_POSTS_PER_DAY = 3      # feed posts + Reels per day (Stories don't count); earliest jobs win

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
    # Jarvis Nov 2: Tuesday, not Monday. On Mondays the week isn't over (MNF), so the Reel showed the week before.
    Job("st_fantasy",  "st_fantasy",  (TUE,), "08:00", live=True, note="Reel: last week's top fantasy scorers (PPR)"),
    Job("v2_waiver",   "v2_waiver",   (TUE,), "12:00", live=True, note="Reel: waiver risers (share of team touches)"),
    # Nov 6 (owner: "the posts all look the same"): more looks. Scatter plots replace NFL offense (Wed) and NBA margin (Fri);
    # NFL margin and NBA offense (moved to Thu) are horizontal bars now; CFP rankings ladder whenever a new ranking is out.
    Job("st_scatter",  "st_scatter",  (WED,), "12:00", live=True, note="Reel: NFL offense vs defense, every team as a logo"),
    Job("v2_rb",       "v2_rb",       (THU,), "12:00", live=True, note="Reel: RB share of team touches"),
    Job("st_margin",   "st_margin",   (FRI,), "12:00", live=True, note="Reel: biggest average winning margin (NFL, horizontal bars)"),
    Job("st_board",    "st_board",    (SAT,), "09:00", live=True, start="2026-11-01", note="Reel: Find Your Team (all 32, point differential)"),
    Job("v2_wr",       "v2_wr",       (SUN,), "08:00", live=True, note="Reel: WR/TE share of team targets"),
    Job("nba_scorers", "nba_scorers", EVERY_DAY, "09:30", live=True, start="2026-11-01", note="Reel: last night's top NBA scorers"),
    Job("nba_board",   "nba_board",   (MON,), "15:00", live=True, note="Reel: NBA Find Your Team (all 30, point differential)"),
    Job("nba_offense", "nba_offense", (THU,), "15:00", live=True, note="Reel: highest-scoring NBA offenses (horizontal bars)"),
    Job("nba_scatter", "nba_scatter", (FRI,), "15:00", live=True, start="2026-11-07", note="Reel: NBA offense vs defense, every team as a logo"),
    # CFP committee ranking (Tuesdays, final one a Sunday): checks every morning, posts once per new ranking.
    Job("cfp_rankings", "cfp_rankings", EVERY_DAY, "08:00", live=True, start="2026-11-07",
        note="Reel: College Football Playoff Top 10 (ESPN, checked vs collegefootballplayoff.com)"),
    # Nov 6 (owner: "throw in some soccer... Champions League... the big names only"): the giants' table the morning
    # after each matchday finishes, the superstar scorers race the following Monday. Both idle between matchdays.
    Job("ucl_giants",  "ucl_giants",  EVERY_DAY, "07:00", live=True, start="2026-11-08",
        note="Reel: Champions League table, biggest clubs only (ESPN, checked vs UEFA)"),
    Job("ucl_scorers", "ucl_scorers", (MON,), "12:00", live=True, start="2026-11-09",
        note="Reel: Champions League goals, stars at the biggest clubs (UEFA, checked vs ESPN)"),
    # ---- Background: multi-sport line archive (never posts)
    Job("archive_am",   "archive",  EVERY_DAY, "06:00", live=True, note="Save lines + results"),
    Job("archive_pm",   "archive",  EVERY_DAY, "14:00", live=True, note="Save lines closer to game time"),
]
# Retired Oct 31 (stats page, no betting framing): v2_angles/best/worst/overs/upsets/all32/sunday, the Sunday
# game-day Story (betting lines), nba_night/best/worst/all30. Their builders still exist.
# Retired Oct 24 (reached ~5 people each or replaced by v2): NFL slate/recap/MNF images, primetime Stories,
# college football board, MLB Stories, old dark Reels. Their builders still exist if we want them back.
