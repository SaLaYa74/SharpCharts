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
BIG_DAY_MAX = 5            # Nov 20: "big" jobs (Selection Sunday, playoff game days) may go up to this many

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
    big: bool = False     # a big moment: allowed past MAX_POSTS_PER_DAY, up to BIG_DAY_MAX


JOBS = [
    # ---- Oct 31: SharpCharts is a STATS page now (owner: "just raw data... like a stat page"). No betting framing,
    # fewer but better Reels. Every Reel opens on a bold claim (the #1 number), then counts down to who it is.
    # NFL: fantasy + usage (our best performers) and team scoring; NBA: nightly top scorers + weekly team stats.
    # Jarvis Nov 2: Tuesday, not Monday. On Mondays the week isn't over (MNF), so the Reel showed the week before.
    # Nov 14 (owner + Claude, 28 days: 78 posts, ~110-140 reach each, 10 followers): "sports debates, settled with data".
    # Half the volume. Kept only what sparked reactions: NBA big-scorer nights (up to 949 reach), the logo scatters
    # (10.8 s watch, 6 comments), CFP rankings (440 avg + comments), Champions League giants (1,076). Everything else
    # (fantasy usage, margins, offense bars, Find Your Team boards: ~60-140 reach, no shares) retired.
    Job("nba_scorers", "nba_scorers", EVERY_DAY, "09:30", live=True, start="2026-11-01", note="Reel: last night's top NBA scorers"),
    Job("st_scatter",  "st_scatter",  (WED,), "12:00", live=True, note="Reel: NFL offense vs defense, every team as a logo"),
    Job("nba_scatter", "nba_scatter", (FRI,), "15:00", live=True, start="2026-11-07", note="Reel: NBA offense vs defense, every team as a logo"),
    # Jarvis Nov 24 (roundtable, owner: "Apply all"): the NBA scatter broke out (4,741 views, 16 shares, Nov 20), so a
    # second everyone-on-one-chart NBA Reel on Tuesdays: home vs road point margin ("who's only good at home?").
    Job("nba_homeroad", "nba_homeroad", (TUE,), "15:00", live=True, start="2026-11-24",
        note="Reel: NBA home vs road point margin, every team as a logo"),
    # CFP committee ranking (Tuesdays, final one a Sunday): checks every morning, posts once per new ranking.
    # Nov 20 (owner): the Top 10 ladder is retired (234 views on Nov 18; ESPN already shows everyone the Top 10). The
    # scatter is our take nobody else has, so it gets the slot.
    # ---- Nov 20, the playoff calendar (owner: "Selection Sunday, huge. We need multiple posts"; "each playoff game day,
    # a head-to-head card"). Each job waits until its data exists (bracket announced, game on today) and posts once.
    Job("sel_field",   "sel_field",   (SUN, MON), "09:30", live=True, start="2026-12-06", big=True,
        note="Reel: Selection Sunday, the 12-team field on the total offense vs defense scatter"),
    Job("sel_snub",    "sel_snub",    (SUN, MON), "11:30", live=True, start="2026-12-06", big=True,
        note="Reel: Selection Sunday, first team OUT vs last team IN, head to head"),
    Job("sel_bracket", "sel_bracket", (SUN, MON), "15:00", live=True, start="2026-12-06", big=True,
        note="Reel: Selection Sunday, all four first-round games on paper + upset alerts + byes"),
    Job("cfp_game1",   "cfp_game1",   EVERY_DAY, "06:00", live=True, start="2026-12-18", big=True,
        note="Reel: playoff game day, head-to-head card for the day's 1st game (none = skip)"),
    Job("cfp_game2",   "cfp_game2",   EVERY_DAY, "08:30", live=True, start="2026-12-18", big=True,
        note="Reel: playoff game day, 2nd game"),
    Job("cfp_game3",   "cfp_game3",   EVERY_DAY, "11:00", live=True, start="2026-12-18", big=True,
        note="Reel: playoff game day, 3rd game"),
    Job("cfp_game4",   "cfp_game4",   EVERY_DAY, "13:30", live=True, start="2026-12-18", big=True,
        note="Reel: playoff game day, 4th game"),
    # Nov 25 (owner: "a post about USC versus UCLA and show the odds... with and without Ty Dieffenbach"; "post it at
    # 9am PST thanksgiving day"). One-off, owner approved the preview. The builder refuses within 2 hours of kickoff.
    # Nov 25 (owner: "post about this wednesday night game (rams vs packers)... a post out tmrw morning about the
    # thanksgiving games... take advantage of these holiday games"). Stats only; each refuses after kickoff.
    Job("rams_packers", "rams_packers", (WED,), "16:15", live=True, start="2026-11-25", big=True,
        note="Reel: Packers at Rams tale of the tape (Wed night, Netflix)"),
    Job("thanksgiving", "thanksgiving", (THU,), "07:00", live=True, start="2026-11-26", big=True,
        note="Reel: all three Thanksgiving games on one board"),
    # TEMP (remove after Nov 25): preview-only build on the GitHub runner, to prove every source answers from there.
    Job("usc_ucla_ci", "usc_ucla",    (WED,), "16:00", live=False, start="2026-11-25", note="TEMP preview: CI source check"),
    Job("usc_ucla",    "usc_ucla",    (THU,), "09:00", live=True, start="2026-11-26",
        note="Reel: USC at UCLA, is one QB worth 5 points? (line move, market vs FPI, UCLA by starting QB)"),
    # Jarvis Nov 16: the CFP Top 25 as an offense-vs-defense logo scatter, Thursdays after each new ranking (the CFP
    # Reel and the NFL scatter are this page's best formats). Every team's points match ESPN vs NCAA.com or it blocks.
    Job("cfp_scatter", "cfp_scatter", (THU,), "12:00", live=True, start="2026-11-19",
        note="Reel: CFP Top 25 national rank in total offense vs total defense, logo scatter (NCAA.com, checked vs "
             "ESPN box scores; falls back to points per game if the yards sources disagree)"),
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
# Retired Nov 14 (the debates reset): st_fantasy, v2_waiver, v2_rb, v2_wr, st_margin, st_board, nba_board, nba_offense.
# Builders still exist. Judge the reset on Dec 5: if reach and followers are still flat, pause the page.
# Retired Oct 31 (stats page, no betting framing): v2_angles/best/worst/overs/upsets/all32/sunday, the Sunday
# game-day Story (betting lines), nba_night/best/worst/all30. Their builders still exist.
# Retired Oct 24 (reached ~5 people each or replaced by v2): NFL slate/recap/MNF images, primetime Stories,
# college football board, MLB Stories, old dark Reels. Their builders still exist if we want them back.
