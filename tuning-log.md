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

## 2026-11-08 (Sun, Claude): fix for failing runs

**What happened:** the Champions League jobs added Nov 6 were scheduled but never wired into autopost.py's builder
dispatch. From 7am PT today the ucl_giants job crashed (KeyError) on every 15-minute run, so each run failed and GitHub
emailed the owner. Nothing else was affected: the CFP Reel (Sat), NFL board, NBA scorers and today's WR Reel all posted.

**Fixed:** ucl builders wired in; both build cleanly through the runner (66 and 86 checks, 0 blocking). New guard:
`python3 autopost.py --list` now exits with an error if any scheduled job has no builder (Jarvis already runs it after
every calendar change). The Matchday 4 giants table posts on the next run today instead of 7am.

## 2026-11-09 (Mon, Jarvis full review)

**Numbers (7 days, 17 Reels):** 8 followers. **Champions League giants table: 1,070 reach / 1,404 views** (Sun 11/8),
the page's best ever, ~9x the usual. CFP Top 10: 295. NBA top scorers: 226 avg over 7 posts (607 best). Every NFL
format: 107-125 (offense, margin, board, RB/WR share, waiver). Watch time 3.4-7.2 s; the boards hold best (7.2 s NFL).
Saves, shares, comments: still 0 on all 62 posts. Midday 234 avg reach vs evening 130, but that gap is the formats
(the winners all post midday), not the clock. No errors in the run log. Today's 8am CFP skip is expected: ESPN's feed
shows the CFP poll only after the committee releases it (Tue Nov 10).

**Changed:**
1. **"Comment your team" on both Find Your Team boards** (NFL Sat, NBA Mon), plus a follow reason ("New NFL board every
   Saturday. Follow to track your team all season."). Same conversion test as Paycheck Math. 0 comments in 62 posts
   so far. Test builds: NBA 771 checks, NFL 474, 0 blocking; hand-checked Wolves +122 (1,299-1,177, 8-3) and
   Bulls -150 (1,014-1,164, 1-8) against ESPN standings.

**Not changed:** NBA vs NFL. NBA scorers is the only NBA format beating NFL. Other NBA formats sit at 109-167, so
"more NBA" isn't the answer. Event-driven formats (Champions League, CFP, last night's scorers) are what break out.
Soccer gets one post so far (n=1). Waiting for today's first Champions League scorers Reel before building a spin-off.

**Watch Thu Nov 12:** Champions League scorers (Mon noon) reach. If it also tops ~500, build a "giant vs giant" or
Mbappé-vs-Haaland Reel at the Nov 16 review, ahead of Matchday 5 (Nov 24-25). Comments on the NBA board (today 3pm).
Waiver risers' 3rd post (Tue): retire it if it stays under ~3 s watch (now 2.3 and 2.7 s). First CFP ranking
week 2 (Tue).

## 2026-11-11 (Wed, Claude): CFP Reel held back by a date-check bug; new "fallen #1" hook

**What happened:** the Nov 10 CFP rankings matched rank-for-rank and record-for-record between ESPN and
collegefootballplayoff.com, but the post kept waiting: the date check read the official site's week menu
("Nov. 10 Nov. 3", newest first) from the wrong end and compared ESPN's Nov 10 with "Nov. 3". By tonight that would have
become a failed run (and a failure email). Fixed: compare with the newest week in the menu (68 checks pass).
**Hook:** when last week's #1 has fallen, the Reel leads with it: "Last Week's #1 Is Now #7" (Miami, #1 → #7). ESPN's
previous-rank field must agree with the #1 in our own posted Reel from last week, or the hook isn't used.
Today's 6 "startup failure" emails (12:30 and 12:45 PT) were a GitHub outage, not this.
