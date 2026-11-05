# SharpCharts tuning log

Plain-English record of what Jarvis (the weekly review) changed, why, and what to watch.

## 2026-11-02 (Mon, full review)

**Numbers (last 7 days):** 8 followers. 17 Reels, almost all reaching 85-150 people (the old betting-style
formats, retired Oct 31). The first new-style stats Reel, "last night's top NBA scorers" (Sun 11/01), reached
**318** with 428 views, about 2.5x the usual. Today's is too new to judge. Saves, shares and follows: still 0.
Average watch 2-5 s. Midday (123 avg reach) vs. evening (103): no real difference.

**Changed:**
1. **Weekly fantasy top-scorers Reel moves from Monday noon to Tuesday 8am.** On Monday the NFL week isn't over
   (Monday Night Football), so the Reel would have shown the week before: today's test build was Week 7, already
   8 days old. Tuesday morning it shows the week that just ended. If the nflverse stats aren't updated yet, the
   "250+ player rows" check blocks it and it retries later that day. Test build passed every check; hand-checked
   Burrow 28.9 (292 pass yds, 4 TD, 12 rush yds) and Smith-Njigba 31.3 (9 catches, 150 yds, 1 TD, 13 rush yds).
   Tuesday now has 3 Reels (fantasy, NBA scorers, waiver risers), the daily max.

**Not changed:** the new stats calendar has posted 3 Reels so far, not enough to judge any format.
The NBA "Find Your Team" board (today 3pm) test-built clean; one render timed out on the first try and finished
in 18 s on the retry, so it looks like a one-off.

**Watch next time:** do the NBA scorers Reels keep beating ~120 reach? If 3+ do, give NBA more slots.
First runs of the NFL/NBA team boards, offense and margin Reels. Any shares or saves at all.

## 2026-11-05 (Thu, check-in)

**Numbers (last 4 days):** 8 followers (no change). 8 Reels, no errors or blocked posts in the run log. NBA top-scorers
Reels: 333, 150, 135 reach (avg 206). NBA offense 162, NBA board 114. NFL/fantasy Reels: fantasy top scorers 124,
NFL offense 115, waiver risers 107. Average watch 2.3-5.1 s on ~7.6 s Reels (waiver risers lowest at 2.3 s).
Midday 161 avg reach vs evening 138: no real difference. Saves, shares, follows: still 0.
Wed's NBA scorers skipped because there were no NBA games on Election Day (Tue 11/3): correct, not a bug.

**Changed:** nothing. NBA looks a bit stronger than NFL (~140 vs ~115 if the 333 outlier is left out, ~1.2x), short of
the 1.5x bar, and each format has only 1-3 posts.

**Watch Monday Nov 9:** if NBA keeps beating NFL by 1.5x+ over 7 days, move an NFL slot to NBA. Waiver risers
(2.3 s watch) is the weakest hook so far: check its 2nd post on Tue 11/10. First runs of v2_rb (Thu), the margin Reels (Fri)
and the NFL Find Your Team board (Sat).
