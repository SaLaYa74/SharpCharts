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

## 2026-11-06 (Claude, with the owner): more variety + College Football Playoff

**Owner:** "the posts all look exactly the same", likes the bar charts, wants horizontal bars, a scatter plot with team
logos (offense vs defense), and to jump on trending topics: the first College Football Playoff rankings just came out.

**Changed:**
1. **CFP rankings Reel** (sharpcharts/cfp.py, new "ladder" look): counts down the committee's Top 10, #10 → #1, with
   logos and an UNBEATEN tag; the caption lists all 25. ESPN's rankings feed must match collegefootballplayoff.com on
   every rank, school, record and the release date, or nothing posts (Nov 3 ranking: 68 checks passed). Job runs daily
   at 8am and posts once per new ranking; first one Sat Nov 7 (Miami #1 at 8-0; Utah and UCLA also unbeaten).
2. **Offense vs defense scatter** (new look): every team as a logo, points scored per game (x) vs allowed (y, flipped so
   better defense is higher), green "good at both" corner, red "struggling" corner. NFL replaces the NFL offense bars on
   Wednesday; NBA replaces the NBA margin bars on Friday (from Nov 13). New check: league-wide points scored must equal
   points allowed. Hand-checked from raw nflverse scores: Bills 33.3 scored/game, Vikings 13.3 allowed/game.
3. **Horizontal bars** for the NFL margin Reel (Fri) and NBA offense Reel (moved Wed → Thu so Wednesday stays at 3 posts).

**Watch:** does the CFP Reel beat the ~120-200 reach of the NBA scorers Reels? Do the scatter plots get shares
(they're built for "find your team")? Saturday is now CFP + NFL board + NBA scorers (3, the max).

## 2026-11-06 (later, Claude with the owner): Champions League + a daily cap

**Owner:** keep the big hooks and tags ("big gold UNBEATEN"), the first 2 seconds are everything; add some Champions
League posts about the big clubs only (Real Madrid, Man City, Barcelona, Bayern, Chelsea, PSG...).

**Changed:**
1. **Giants table** (sharpcharts/ucl.py, ladder look): the 10 most famous clubs in this season's Champions League, in
   table order, with PERFECT / TOP 8 / PLAYOFFS / DANGER tags. Hook picks itself from the data: a giant in the bottom 12
   ("___ Would Be Out Today"), else "Only N Giants Are Still Perfect" (now: PSG and Real Madrid). Posts the morning after
   each matchday finishes (first: Sun Nov 8, Matchday 4). 66 checks: every giant's position, points and W-D-L match
   UEFA's own table, points add up (3 per win, 1 per draw), and ESPN's zone notes match the top 8 / 9-24 / 25-36 rules.
2. **Superstar scorers** (hbars): goals by players at those clubs, ties for the last spot included (so Kane makes it).
   "5 Goals in 3 Games. Who?" → Haaland. Goals and games match between UEFA's player stats and ESPN for every player;
   the caption also names the overall leader if he isn't at a giant (Como's Douvikas, 6). Mondays after a matchday
   (first: Mon Nov 9).
3. **3 posts a day, enforced** in autopost.py (MAX_POSTS_PER_DAY). Earliest jobs win; later ones wait and then skip.
   Next squeeze: Thanksgiving Thu Nov 26 (Matchday 5 table at 7am) will push out the 3pm NBA offense Reel.
4. Daily once-per-event jobs (CFP, Champions League) now stop before rendering when that event already posted.

**Watch:** do soccer Reels reach a different audience (non-follower reach, shares) than NFL/NBA? If the giants table
beats ~150 reach, add a "giant vs giant" matchday preview next.
