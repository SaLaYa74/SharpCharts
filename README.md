# SharpCharts (@sharp_charts)

Verified sports-betting data graphics for Instagram, TikTok and X.

## Make this week's posts

```bash
cd ~/Documents/SharpCharts
python3 generate.py
```

The finished PNGs and `captions.md` land in `out/<today's date>/`. No installs are needed beyond Python 3 and Google Chrome.

| File | Size | Use |
|---|---|---|
| `*_feed.png` | 1080×1350 (4:5) | Instagram feed posts |
| `*_story.png` | 1080×1920 (9:16) | IG Stories, Reels covers, TikTok photo posts. Safe zones are built in |
| `profile_pic.png` | 1080×1080 | Profile photo on every platform (built for the circle crop) |
| `logo_wordmark.png` | 1080×1080 | Banners, watermark, X header art |
| `weekN_matchups/` | both | One breakdown card for every game next week |

**Best time to run it:** Tuesday morning, after Monday Night Football is final. That way "Thru Wk N" covers the full week. Run it again Saturday for fresh lines on the matchup cards.

## Data sources: why we trust them

| Source | What we use | Why it's reliable |
|---|---|---|
| **nflverse** (`nflverse/nfldata` games.csv) | Final scores, closing spread and total, moneylines, kickoff times | The standard open dataset of the NFL analytics community, maintained by Lee Sharpe. Used by ESPN analysts, the Athletic writers and academic researchers. Updated within hours of games. |
| **ESPN scoreboard API** | Independent score check and the current DraftKings line | ESPN's own live feed. The DraftKings line comes straight from a major regulated sportsbook. |

**The verification gate:** every run compares each final score in nflverse to ESPN's. If even one game disagrees, **nothing is exported** and the mismatch is printed. On 2026-10-04, all 63 games matched.

**How the math is defined (so you can answer people in the comments):**
- **ATS record:** wins, losses and pushes against the **closing** spread recorded by nflverse.
- **Avg cover margin:** the average number of points a team beat (+) or missed (−) the spread by.
- **O/U and avg vs. total:** the game total compared with the closing total.
- **Lines vary by book:** matchup cards show both the consensus close and DraftKings, so readers see when they differ (for example CIN −7.5 vs −7).

**Sources we chose not to use:** "public betting %" and "sharp money" numbers. No free source for them is verifiable, and most pages that post them can't show where the data came from. We'll add them only if we buy a licensed feed.

## Posting rules (keep the account safe)
- Keep the 21+ / 1-800-GAMBLER footer on every graphic. It's already in the templates.
- Use no sportsbook logos and no promo codes, and don't call anything a "lock" or "guaranteed."
- Early-season samples are small, so say so in captions.
- If someone points out an error, verify it, then correct the post or delete and repost it. Trust is the product.

## Instagram bio (copy and paste)

```
SharpCharts 📊
Verified NFL betting data, trends & matchup breakdowns
Numbers, not locks. New charts every week 🏈
21+ | Gamble responsibly · 1-800-GAMBLER
```

## Roadmap
- [ ] NBA (official stats.nba.com data + ESPN lines) when the season starts
- [ ] MLB playoffs (MLB Stats API, the official source)
- [ ] Player prop hit-rate charts (nflverse player stats)
- [ ] "Receipts" post: how last week's highlighted trends performed

## Auto-posting (GitHub Actions)

`autopost.py` + `.github/workflows/autopost.yml` build and publish posts on a schedule, in GitHub's cloud. Your laptop can be off.

| When (Pacific) | Post | Contents |
|---|---|---|
| Tue 9am | `recap` | Carousel: ATS best/worst · league splits · over/under teams |
| Thu 10am | `slate` | Carousel: every game's spread & total + up to 9 matchup cards |
| Sat 10am | `featured` | Sunday Night Football breakdown (or the closest-spread game) |

(Times shift an hour earlier after daylight saving ends, because GitHub schedules in UTC.)

**Safety checks: the bot will NOT post if:**
- any final score disagrees with ESPN
- the latest week isn't finished (stats always run through the last completed week)
- a game has no posted line (it's left out of breakdown cards)
- the caption breaks Instagram limits, or the daily publish limit is hit
- that post already went out (`posted.json` tracks every post)

**Controls (GitHub repo → Settings → Secrets and variables → Actions):**
- Variable `POSTING_ENABLED` = `true` turns posting on. Anything else is a **dry run**: images are built and committed to `media/` for review, but nothing gets posted. **This is the kill switch.**
- Secret `IG_TOKEN`: your Instagram access token (encrypted, never visible)
- Secret `GH_PAT`: lets the weekly job refresh `IG_TOKEN` before it expires

**Run one manually:** Actions tab → Auto-post → Run workflow → pick the post.
**Check what happened:** Actions tab → click a run. The summary shows the images and caption. GitHub emails you if a run fails.

Locally: `python3 autopost.py slate` does a dry run into `media/`.
