"""Post builders shared by generate.py (manual) and autopost.py (scheduled).

Each builder returns a Post: a stable `key` (for duplicate protection), a list of
rendered image paths (1 = single image, 2-10 = carousel) and a caption.
All season stats are computed through the last *fully completed* week so a
post never mixes partial weeks.
"""
import os
from dataclasses import dataclass, field
from datetime import date, timedelta

from . import checks as C
from . import data as D
from . import questions as Q
from . import templates as T
from .render import html_to_png

SRC = "nflverse (scores + lines) · ESPN (verified)"
DISCLAIMER = "21+ | Gamble responsibly · 1-800-GAMBLER"
MAX_CAROUSEL = 10  # Instagram API limit


class DataError(Exception):
    """Raised when data fails verification or isn't ready; nothing should be posted."""


class NoContent(DataError):
    """Nothing to post today (no games, off-season). Skipped quietly, not an error."""


@dataclass
class Post:
    key: str
    caption: str
    images: list = field(default_factory=list)   # list of {size: path}
    media: str = "feed"                            # "feed" (post/carousel) or "story"
    checks: C.Report = field(default_factory=C.Report)

    @property
    def size(self):
        return "story" if self.media == "story" else "feed"


def with_question(text, kind, key, **values):
    q = Q.pick(kind, key, **values)
    return f"{text}\n\n{q}" if q else text


def rec(w, l, p=0):
    return f"{w}-{l}" + (f"-{p}" if p else "")


def spread_text(home, away, line):
    if line is None:
        return "OFF"
    if line == 0:
        return "PK"
    return f"{home} -{abs(line):g}" if line > 0 else f"{away} -{abs(line):g}"


def clock(t):
    """'20:15' -> '8:15 PM'"""
    if not t:
        return "TBD"
    h, m = map(int, t.split(":"))
    return f"{(h - 1) % 12 + 1}:{m:02d} {'PM' if h >= 12 else 'AM'}"


class Context:
    def __init__(self, season, verify=True):
        self.season = season
        self.games = D.load_games(season)
        if not any(g["final"] for g in self.games):
            raise DataError("No completed games yet.")
        if verify:
            n, problems = D.verify_scores(self.games)
            if problems:
                raise DataError("Score verification failed:\n  " + "\n  ".join(problems))
            self.verified = n
        weeks = sorted({g["week"] for g in self.games if g["final"]})
        complete = [w for w in weeks if D.week_complete(self.games, w)]
        if not complete:
            raise DataError("No fully completed week yet.")
        self.thru_week = max(complete)
        self.finals = [g for g in self.games if g["final"] and g["week"] <= self.thru_week]
        self.recs = D.team_records(self.finals)
        unplayed = [g for g in self.games if not g["final"]]
        self.upcoming_week = min(g["week"] for g in unplayed) if unplayed else None
        self.thru = f"Thru Wk {self.thru_week}"
        self.thru_note = f"Through Week {self.thru_week} · {len(self.finals)} games"
        self.report = self._integrity(verify)

    def _integrity(self, verified):
        rep = C.Report("nfl data")
        if verified:
            rep.require(True, f"nfl: {self.verified} final scores match ESPN")
        # Freshness: every game played 2+ days ago must be final in the source data.
        cutoff = (date.today() - timedelta(days=2)).isoformat()
        stale = [g["game_id"] for g in self.games if g["gameday"] <= cutoff and not g["final"]]
        rep.require(not stale, "nfl: source data is up to date", f"games played but not final: {stale[:5]}")
        for g in self.finals:
            ok = (g["result"] == g["home_score"] - g["away_score"]
                  and g["total"] == g["home_score"] + g["away_score"])
            rep.require(ok, f"nfl: {g['game_id']} result/total math", "result or total doesn't match the score")
            C.line_ranges(rep, "nfl", g["game_id"], g["spread_line"], g["total_line"])
        for t, r in self.recs.items():
            n = r["games"]
            ok = (r["ats_W"] + r["ats_L"] + r["ats_P"] == n == r["su_W"] + r["su_L"] + r["su_T"]
                  == r["ou_O"] + r["ou_U"] + r["ou_P"]) and n <= self.thru_week
            rep.require(ok, f"nfl: {t} records add up", f"{t} record totals inconsistent ({n} games)")
        rep.require(sum(r["games"] for r in self.recs.values()) == 2 * len(self.finals),
                    "nfl: team-games equal 2× games", "team game count mismatch")
        rep.require(len(self.recs) == 32, "nfl: all 32 teams present", f"{len(self.recs)} teams")
        return rep

    def team(self, abbr):
        return {"abbr": abbr, "name": D.TEAMS[abbr][0], "color": D.TEAMS[abbr][1]}


def _render(html_fn, out_dir, name, sizes):
    paths = {}
    for s in sizes:
        p = os.path.join(out_dir, f"{name}_{s}.png")
        html_to_png(html_fn(s), p, s)
        paths[s] = p
    return paths


# ---------------------------------------------------------------- recap

def ats_ranked(ctx):
    """All teams, best to worst against the spread (win %, then avg cover margin)."""
    def row(t):
        r = ctx.recs[t]
        v = r["cover_margin_sum"] / r["games"]
        return {"abbr": t, "color": D.TEAMS[t][1], "name": D.TEAMS[t][0], "value": v,
                "value_label": f"{v:+.1f}",
                "record": f"{rec(r['ats_W'], r['ats_L'], r['ats_P'])} ATS · {rec(r['su_W'], r['su_L'], r['su_T'])} SU",
                "ats": rec(r["ats_W"], r["ats_L"], r["ats_P"]), "wins": r["ats_W"],
                "pct": r["ats_W"] / max(1, r["ats_W"] + r["ats_L"])}
    return sorted((row(t) for t in ctx.recs), key=lambda x: (x["pct"], x["value"]), reverse=True)


def ou_ranked_rows(ctx):
    """All teams, most overs to most unders."""
    def row(t):
        r = ctx.recs[t]
        v = r["ou_margin_sum"] / r["games"]
        return {"abbr": t, "color": D.TEAMS[t][1], "name": D.TEAMS[t][0], "value": v,
                "value_label": f"{v:+.1f}", "record": f"O/U {rec(r['ou_O'], r['ou_U'], r['ou_P'])}",
                "ou": rec(r["ou_O"], r["ou_U"], r["ou_P"]),
                "pct": r["ou_O"] / max(1, r["ou_O"] + r["ou_U"])}
    return sorted((row(t) for t in ctx.recs), key=lambda x: (x["pct"], x["value"]), reverse=True)


def recap(ctx, out_dir, sizes=("feed",)):
    """Tuesday carousel: ATS best/worst, league splits, over/under teams."""
    recs, thru, note = ctx.recs, ctx.thru, ctx.thru_note

    ranked = ats_ranked(ctx)
    top, bottom = ranked[:6], ranked[-6:]

    sp = D.league_splits(ctx.finals)
    split_items = [
        {"label": "Favorites vs underdogs (ATS)", "left": ("Favs", sp["fav_W"]), "right": ("Dogs", sp["fav_L"])},
        {"label": "Home vs away (ATS)", "left": ("Home", sp["home_W"]), "right": ("Away", sp["home_L"])},
        {"label": "Totals", "left": ("Over", sp["ou_O"]), "right": ("Under", sp["ou_U"])},
        {"label": "Underdogs winning outright", "left": ("Dog wins", sp["dog_outright_W"]), "right": ("Fav wins", sp["dog_outright_L"])},
    ]

    ou_ranked = ou_ranked_rows(ctx)

    slides = [
        _render(lambda s: T.bar_ranking('Best &amp; worst<br><em>against the spread</em>',
                                        "Avg. cover margin per game (points beyond the closing spread)",
                                        top + bottom, tag=f"NFL · {thru}", source=SRC, size=s, note=note),
                out_dir, "01_ats_best_worst", sizes),
        _render(lambda s: T.splits(f'{ctx.season} NFL<br><em>betting splits</em>',
                                   "How the league is landing against the number", split_items,
                                   tag=f"NFL · {thru}", source=SRC, size=s, note=f"{note} · pushes excluded"),
                out_dir, "02_league_splits", sizes),
        _render(lambda s: T.bar_ranking('Over teams vs<br><em>under teams</em>',
                                        "Avg. points vs. the closing total per game",
                                        ou_ranked[:6] + ou_ranked[-6:], tag=f"NFL · {thru}", source=SRC,
                                        size=s, note=note),
                out_dir, "03_overs_unders", sizes),
    ]
    best, worst = top[0], bottom[-1]
    caption = (
        f"{ctx.season} NFL betting recap through Week {ctx.thru_week} 📊\n\n"
        "1️⃣ Best & worst teams against the spread\n"
        "2️⃣ League-wide splits: favs vs dogs, home vs away, overs vs unders\n"
        "3️⃣ The biggest over and under teams\n\n"
        f"Top ATS: " + ", ".join(f"{x['name']} ({x['ats']})" for x in top[:3]) + "\n"
        f"Bottom ATS: " + ", ".join(f"{x['name']} ({x['ats']})" for x in bottom[-3:]) + "\n"
        f"Favorites ATS: {sp['fav_W']}-{sp['fav_L']} · Overs: {sp['ou_O']}-{sp['ou_U']}\n\n"
        f"{best['name']} are covering by {best['value']:+.1f} a game. {worst['name']} are at {worst['value']:+.1f}.\n\n"
        + (lambda q: f"{q}\n\n" if q else "Save this for your weekly card 📌\n\n")(
            Q.pick("recap", f"{ctx.season}-wk{ctx.thru_week}-recap", best=best["name"],
                   best_margin=f"{best['value']:+.1f}", worst=worst["name"]))
        + f"Data: nflverse closing lines, scores verified vs ESPN. Pushes excluded from splits.\n{DISCLAIMER}\n"
        "#nflbetting #sportsbetting #nfl #ats #overunder #bettingdata"
    )
    return Post(key=f"{ctx.season}-wk{ctx.thru_week:02d}-recap", caption=caption,
                images=[s for s in slides], checks=C.Report("recap").extend(ctx.report))


# ---------------------------------------------------------------- matchups

def _primetime(g):
    hour = int(g["gametime"].split(":")[0]) if g["gametime"] else 13
    return g["weekday"] in ("Thursday", "Monday") or (g["weekday"] == "Sunday" and hour >= 20)


def _matchup_card(ctx, g, live, out_dir, sizes):
    a, h = g["away_team"], g["home_team"]
    ra, rh = ctx.recs[a], ctx.recs[h]
    if not ra["games"] or not rh["games"] or g["spread_line"] is None or g["total_line"] is None:
        return None  # never publish a breakdown without a posted line
    dk = live.get(g["game_id"], {})
    rep = C.Report(f"{a}@{h}")
    agree = _lines_agree(g, dk)
    if agree is False:
        rep.expect(False, f"{a}@{h}: consensus vs DraftKings line",
                   f"nflverse {spread_text(h, a, g['spread_line'])}/{g['total_line']:g} vs DK {dk.get('details')}/{dk.get('over_under')}, card skipped")
        return {"skipped": rep}
    rep.require(True, f"{a}@{h}: line {'matches DraftKings' if agree else 'from nflverse (DK unavailable)'}")
    C.line_ranges(rep, "nfl", f"{a}@{h}", g["spread_line"], g["total_line"])
    line_info = [("Spread", spread_text(h, a, g["spread_line"])),
                 ("Total", f"{g['total_line']:g}" if g["total_line"] else "—")]
    if dk.get("details"):
        dk_spread = dk["details"].replace("WSH", "WAS").replace("LAR", "LA")
        line_info.append(("DraftKings", f"{dk_spread} · {dk['over_under']:g}" if dk.get("over_under") else dk_spread))
    ca, ch = ra["cover_margin_sum"] / ra["games"], rh["cover_margin_sum"] / rh["games"]
    oa, oh = ra["ou_margin_sum"] / ra["games"], rh["ou_margin_sum"] / rh["games"]
    pa = ra["ats_W"] / max(1, ra["ats_W"] + ra["ats_L"])
    ph = rh["ats_W"] / max(1, rh["ats_W"] + rh["ats_L"])
    stats = [
        ("Record", rec(ra["su_W"], ra["su_L"], ra["su_T"]), rec(rh["su_W"], rh["su_L"], rh["su_T"]),
         "away" if ra["su_W"] > rh["su_W"] else "home" if rh["su_W"] > ra["su_W"] else ""),
        ("ATS", rec(ra["ats_W"], ra["ats_L"], ra["ats_P"]), rec(rh["ats_W"], rh["ats_L"], rh["ats_P"]),
         "away" if pa > ph else "home" if ph > pa else ""),
        ("Avg cover margin", f"{ca:+.1f}", f"{ch:+.1f}", "away" if ca > ch else "home"),
        ("Over / Under", rec(ra["ou_O"], ra["ou_U"], ra["ou_P"]), rec(rh["ou_O"], rh["ou_U"], rh["ou_P"]), ""),
        ("Avg vs total", f"{oa:+.1f}", f"{oh:+.1f}", ""),
    ]
    kick = f"{g['weekday'][:3]} {g['gameday'][5:].replace('-', '/')} · {clock(g['gametime'])} ET"
    paths = _render(lambda s: T.matchup(ctx.team(a), ctx.team(h), line_info, stats, tag=f"Week {g['week']}",
                                        source=SRC, size=s, note=f"{kick} · Season stats {ctx.thru.lower()}"),
                    out_dir, f"{a}_at_{h}", sizes)
    return {"game": g, "paths": paths, "line": line_info, "stats": stats, "checks": rep}


def _lines_agree(g, dk, max_spread=1.5, max_total=2.5):
    """True if the DraftKings line is within tolerance, False if not, None if DK has no line."""
    det, ou = dk.get("details"), dk.get("over_under")
    if not det or ou is None:
        return None
    det = det.replace("WSH", "WAS").replace("LAR", "LA").strip()
    if det.upper() in ("EVEN", "PK", "PICK"):
        dk_home = 0.0
    else:
        team, _, num = det.rpartition(" ")
        try:
            num = abs(float(num))
        except ValueError:
            return None
        dk_home = num if team == g["home_team"] else -num
    return abs(dk_home - g["spread_line"]) <= max_spread and abs(float(ou) - g["total_line"]) <= max_total


def _live_lines(ctx, week):
    try:
        return D.espn_lines_for_week(ctx.games, week)
    except Exception as e:  # ESPN down → nflverse lines only
        print("  ! ESPN lines unavailable:", e)
        return {}


def _priced(games):
    return [g for g in games if g["spread_line"] is not None and g["total_line"] is not None]


def _upcoming(ctx, week):
    games = sorted((g for g in ctx.games if g["week"] == week and not g["final"]),
                   key=lambda g: (g["gameday"], g["gametime"]))
    if not games:
        raise NoContent(f"No unplayed games in week {week}.")
    return games


def _slate_rows(games):
    return [{"kick": f"{g['weekday'][:3]} {clock(g['gametime'])}",
             "away": (g["away_team"], D.TEAMS[g["away_team"]][1]),
             "home": (g["home_team"], D.TEAMS[g["home_team"]][1]),
             "spread": spread_text(g["home_team"], g["away_team"], g["spread_line"]),
             "total": f"{g['total_line']:g}" if g["total_line"] else "OFF"} for g in games]


def slate(ctx, out_dir, sizes=("feed",), week=None):
    """Thursday carousel: slate cover (every game) + up to 9 matchup cards."""
    week = week or ctx.upcoming_week
    games = _upcoming(ctx, week)
    live = _live_lines(ctx, week)
    rep = C.Report("slate").extend(ctx.report)
    for g in _priced(games):
        C.line_ranges(rep, "nfl", g["game_id"], g["spread_line"], g["total_line"])
    cover = _render(lambda s: T.slate(week, _slate_rows(games), tag=f"NFL · Week {week}", source=SRC, size=s,
                                      note="Consensus lines · check your book, lines move"),
                    out_dir, "00_slate", sizes)
    # Feature primetime games first, then the closest spreads; show in kickoff order.
    picks = sorted(_priced(games), key=lambda g: (not _primetime(g), abs(g["spread_line"])))
    cards = []
    for g in picks:
        if len(cards) == MAX_CAROUSEL - 1:
            break
        c = _matchup_card(ctx, g, live, out_dir, sizes)
        if c is None:
            continue
        rep.extend(c.get("checks") or c.get("skipped"))
        if "paths" in c:
            cards.append(c)
    cards.sort(key=lambda c: (c["game"]["gameday"], c["game"]["gametime"]))
    rep.require(len(cards) >= 3, "slate: enough verified matchup cards", f"only {len(cards)} cards passed checks")
    lines = "\n".join(f"{D.TEAMS[c['game']['away_team']][0]} @ {D.TEAMS[c['game']['home_team']][0]}: "
                      f"{c['line'][0][1]}, O/U {c['line'][1][1]}" for c in cards)
    key = f"{ctx.season}-wk{week:02d}-slate"
    caption = with_question(
        f"Week {week} NFL betting slate 🏈\n\n"
        f"Slide 1: every game's spread & total. Swipe for {len(cards)} matchup breakdowns ➡️\n\n"
        f"{lines}\n\n"
        f"Season ATS & O/U records {ctx.thru.lower()}. Lines move, so check your book before betting.",
        "slate", key)
    caption += f"\n\n{DISCLAIMER}\n#nfl #nflbetting #sportsbetting #week{week} #nflpicks #bettingdata"
    return Post(key=key, caption=caption, images=[cover] + [c["paths"] for c in cards], checks=rep)


def _primetime_game(ctx, week, slot):
    games = _priced(_upcoming(ctx, week))
    day = {"tnf": "Thursday", "snf": "Sunday", "mnf": "Monday"}[slot]
    found = [g for g in games if g["weekday"] == day and _primetime(g)]
    if not found:
        if not [g for g in _upcoming(ctx, week) if g["weekday"] == day and _primetime(g)]:
            raise NoContent(f"No {slot.upper()} game in week {week}.")
        raise DataError(f"{slot.upper()} game has no posted line yet.")
    return found[0]


def primetime(ctx, out_dir, sizes=("feed",), week=None, slot="snf", media="feed"):
    """Thursday/Sunday/Monday night breakdown, as a feed post or a Story."""
    week = week or ctx.upcoming_week
    g = _primetime_game(ctx, week, slot)
    size = "story" if media == "story" else "feed"
    card = _matchup_card(ctx, g, _live_lines(ctx, week), out_dir, (size,))
    if card is None or "skipped" in card:
        rep = card["skipped"] if card else C.Report()
        raise DataError(f"{slot.upper()} card failed checks: " + "; ".join(i["detail"] for i in rep.warnings))
    a, h = D.TEAMS[g["away_team"]][0], D.TEAMS[g["home_team"]][0]
    st = card["stats"]
    label = {"tnf": "Thursday Night Football", "snf": "Sunday Night Football", "mnf": "Monday Night Football"}[slot]
    key = f"{ctx.season}-wk{week:02d}-{slot}-{media}"
    body = (f"{label}: {a} @ {h} 🏈\n\n"
            f"Line: {card['line'][0][1]} · O/U {card['line'][1][1]}\n"
            f"{a} ATS: {st[1][1]} (avg cover {st[2][1]})\n"
            f"{h} ATS: {st[1][2]} (avg cover {st[2][2]})\n"
            f"O/U: {a} {st[3][1]} · {h} {st[3][2]}\n\n"
            f"Stats {ctx.thru.lower()}. Lines move, so check your book.")
    caption = with_question(body, "matchup", key, away=a, home=h, total=card["line"][1][1])
    caption += f"\n\n{DISCLAIMER}\n#nfl #nflbetting #{a.lower()} #{h.lower()} #sportsbetting #{slot}"
    rep = C.Report(slot).extend(ctx.report).extend(card["checks"])
    return Post(key=key, caption=caption, images=[card["paths"]], media=media, checks=rep)


def gameday_story(ctx, out_dir, sizes=("story",), week=None):
    """Sunday-morning Story: the full NFL slate."""
    week = week or ctx.upcoming_week
    games = [g for g in _upcoming(ctx, week)]
    rep = C.Report("gameday").extend(ctx.report)
    for g in _priced(games):
        C.line_ranges(rep, "nfl", g["game_id"], g["spread_line"], g["total_line"])
    img = _render(lambda s: T.slate(week, _slate_rows(games), tag="NFL · Game day", source=SRC, size=s,
                                    title_html="NFL Sunday<br><em>every line</em>",
                                    subtitle=f"Week {week} · spreads &amp; totals"),
                  out_dir, "gameday", ("story",))
    key = f"{ctx.season}-wk{week:02d}-gameday-story"
    return Post(key=key, caption=f"NFL Week {week} game day\n{DISCLAIMER}", images=[img], media="story", checks=rep)


# ---------------------------------------------------------------- trend of the day

def _trends(ctx):
    """Candidate single-stat trends, each fully derived from verified ctx data."""
    out, recs = [], ctx.recs
    sp = D.league_splits(ctx.finals)

    def team_rows(t):
        r = recs[t]
        return [("ATS", rec(r["ats_W"], r["ats_L"], r["ats_P"])),
                ("Straight up", rec(r["su_W"], r["su_L"], r["su_T"])),
                ("Avg cover margin", f"{r['cover_margin_sum'] / r['games']:+.1f}"),
                ("Over / Under", rec(r["ou_O"], r["ou_U"], r["ou_P"]))]
    by_ats = sorted(recs, key=lambda t: (recs[t]["ats_W"] - recs[t]["ats_L"], recs[t]["cover_margin_sum"]))
    best, worst = by_ats[-1], by_ats[0]
    rb, rw = recs[best], recs[worst]
    out.append(("best_ats", f"The {D.TEAMS[best][0]}<br><em>keep cashing</em>", "Best record against the spread this season",
                rec(rb["ats_W"], rb["ats_L"], rb["ats_P"]), "against the spread", team_rows(best), "var(--green)",
                f"The {D.TEAMS[best][0]} are {rec(rb['ats_W'], rb['ats_L'], rb['ats_P'])} ATS this season."))
    out.append(("worst_ats", f"The {D.TEAMS[worst][0]}<br><em>can't cover</em>", "Worst record against the spread this season",
                rec(rw["ats_W"], rw["ats_L"], rw["ats_P"]), "against the spread", team_rows(worst), "var(--red)",
                f"The {D.TEAMS[worst][0]} are {rec(rw['ats_W'], rw['ats_L'], rw['ats_P'])} ATS this season."))
    if sp["homedog_W"] + sp["homedog_L"] >= 8:
        out.append(("home_dogs", "Home underdogs<br><em>against the spread</em>", "Every home underdog this season, pushes excluded",
                    f"{sp['homedog_W']}-{sp['homedog_L']}", "home dogs ATS",
                    [("Favorites ATS", f"{sp['fav_W']}-{sp['fav_L']}"), ("Home teams ATS", f"{sp['home_W']}-{sp['home_L']}"),
                     ("Dogs winning outright", str(sp["dog_outright_W"]))], "var(--green)",
                    f"Home underdogs are {sp['homedog_W']}-{sp['homedog_L']} ATS this season."))
    by_ou = sorted(recs, key=lambda t: recs[t]["ou_margin_sum"] / recs[t]["games"])
    for t, word, color in ((by_ou[-1], "over", "var(--green)"), (by_ou[0], "under", "var(--red)")):
        r = recs[t]
        out.append((f"{word}_team", f"The {D.TEAMS[t][0]}<br><em>{word} machine</em>",
                    f"Average points vs. the closing total in {D.TEAMS[t][0]} games",
                    f"{r['ou_margin_sum'] / r['games']:+.1f}", "points per game vs. the total",
                    [("Over / Under", rec(r["ou_O"], r["ou_U"], r["ou_P"])), ("ATS", rec(r["ats_W"], r["ats_L"], r["ats_P"])),
                     ("Games", str(r["games"]))], color,
                    f"{D.TEAMS[t][0]} games are landing {r['ou_margin_sum'] / r['games']:+.1f} points vs. the total on average."))
    return out


def trend(ctx, out_dir, sizes=("feed",), day=None):
    """Single bold stat card. Rotates by date so consecutive trend posts differ."""
    day = day or date.today()
    options = _trends(ctx)
    tkey, title, sub, number, label, rows, color, sentence = options[day.toordinal() % len(options)]
    img = _render(lambda s: T.big_stat(title, sub, number, label, rows, tag=f"NFL · {ctx.thru}", source=SRC,
                                       size=s, color=color), out_dir, f"trend_{tkey}", sizes)
    key = f"{day.isoformat()}-trend"
    caption = with_question(f"{sentence} 📊\n\nData {ctx.thru.lower()}, verified vs ESPN.", "trend", key)
    caption += f"\n\n{DISCLAIMER}\n#nfl #nflbetting #sportsbetting #bettingtrends #ats"
    return Post(key=key, caption=caption, images=[img], checks=C.Report("trend").extend(ctx.report))


# ---------------------------------------------------------------- fantasy (raw usage data)

FANTASY_URL = "https://github.com/nflverse/nflverse-data/releases/download/stats_player/stats_player_week_{}.csv"


def _player_weeks(season, thru_week):
    import csv, io
    path = os.path.join(D.CACHE, f"stats_player_week_{season}.csv")
    with open(path, "wb") as f:
        f.write(D._get(FANTASY_URL.format(season)))
    rows = [r for r in csv.DictReader(open(path)) if r["season_type"] == "REG" and int(r["week"]) <= thru_week]
    return rows


def fantasy_board(ctx, focus):
    """Verified usage leaderboard (focus 'rb' or 'wr'). Returns a dict used by posts and Reels."""
    rows = _player_weeks(ctx.season, ctx.thru_week)
    rep = C.Report(f"fantasy {focus}").extend(ctx.report)
    rep.require(len(rows) > 500, "fantasy: player data loaded", f"only {len(rows)} player-weeks")
    weeks = {int(r["week"]) for r in rows}
    rep.require(max(weeks) == ctx.thru_week, "fantasy: player data current",
                f"player stats thru week {max(weeks)} but scores thru week {ctx.thru_week}")
    num = lambda v: float(v) if v not in ("", "NA", None) else 0.0
    team_carries, team_targets = {}, {}
    for r in rows:
        k = (r["team"], r["week"])
        team_carries[k] = team_carries.get(k, 0) + num(r["carries"])
        team_targets[k] = team_targets.get(k, 0) + num(r["targets"])
    for (t, w), c in team_carries.items():
        rep.require(c <= 60, f"fantasy: {t} wk{w} carries plausible", f"{c:.0f} team carries")
    players = {}
    for r in rows:
        p = players.setdefault(r["player_id"], {"name": r["player_display_name"], "pos": r["position"], "team": r["team"],
                                                "games": 0, "carries": 0, "targets": 0, "team_opps": 0, "team_tgts": 0})
        k = (r["team"], r["week"])
        p["games"] += 1
        p["team"] = r["team"]
        p["carries"] += num(r["carries"])
        p["targets"] += num(r["targets"])
        p["team_opps"] += team_carries[k] + team_targets[k]
        p["team_tgts"] += team_targets[k]
    min_games = max(2, ctx.thru_week - 1)
    if focus == "rb":
        pool = [p for p in players.values() if p["pos"] == "RB" and p["games"] >= min_games and p["team_opps"]]
        for p in pool:
            p["share"] = (p["carries"] + p["targets"]) / p["team_opps"]
        title, sub, tag = "RB opportunity<br><em>share leaders</em>", "Share of team carries + targets, season to date", "Fantasy · RB"
        detail = lambda p: f"{p['team']} · {p['carries']:.0f} car · {p['targets']:.0f} tgt"
        hashtags = "#fantasyfootball #fantasyrb #nfl #rbs #fantasyadvice"
    else:
        pool = [p for p in players.values() if p["pos"] in ("WR", "TE") and p["games"] >= min_games and p["team_tgts"]]
        for p in pool:
            p["share"] = p["targets"] / p["team_tgts"]
        title, sub, tag = "Target share<br><em>leaders</em>", "Share of team targets (WR/TE), season to date", "Fantasy · WR/TE"
        detail = lambda p: f"{p['team']} · {p['pos']} · {p['targets']:.0f} targets"
        hashtags = "#fantasyfootball #fantasywr #nfl #targetshare #fantasyadvice"
    for p in pool:
        rep.require(0 <= p["share"] <= 1, f"fantasy: {p['name']} share valid", f"share {p['share']:.2f}")
    top = sorted(pool, key=lambda p: -p["share"])[:12]
    rep.require(len(top) == 12, "fantasy: full leaderboard", f"only {len(top)} qualified players")
    bars = [{"abbr": p["team"], "color": D.TEAMS.get(p["team"], ("", "#3A4A6B"))[1], "name": p["name"],
             "value": p["share"], "value_label": f"{p['share'] * 100:.0f}%", "record": detail(p)} for p in top]
    return dict(title=title, sub=sub, tag=tag, bars=bars, rep=rep, top=top, min_games=min_games, hashtags=hashtags)


def fantasy(ctx, out_dir, sizes=("feed",), focus=None, day=None):
    """RB opportunity share or WR/TE target share leaders, season to date."""
    day = day or date.today()
    focus = focus or ("rb" if day.weekday() == 2 else "wr")   # Wed RBs, Sun WR/TE
    b = fantasy_board(ctx, focus)
    title, sub, tag, bars, rep, top, min_games, hashtags = (b[k] for k in
        ("title", "sub", "tag", "bars", "rep", "top", "min_games", "hashtags"))
    img = _render(lambda s: T.bar_ranking(title, sub, bars, tag=f"{tag} · {ctx.thru}", size=s, diverging=False,
                                          source="nflverse player stats", note=f"Min. {min_games} games · {ctx.thru_note}"),
                  out_dir, f"fantasy_{focus}", sizes)
    key = f"{ctx.season}-wk{ctx.thru_week:02d}-fantasy-{focus}"
    lead = top[0]
    caption = with_question(
        f"{'RB opportunity share' if focus == 'rb' else 'Target share'} leaders through Week {ctx.thru_week} 📈\n\n"
        f"{lead['name']} leads at {lead['share'] * 100:.0f}%. Opportunity is what drives fantasy points.\n\n"
        + "\n".join(f"{i + 1}. {p['name']} ({p['team']}) {p['share'] * 100:.0f}%" for i, p in enumerate(top[:5])),
        "fantasy", key)
    caption += f"\n\nRaw data, no projections. Source: nflverse.\n{DISCLAIMER}\n{hashtags}"
    return Post(key=key, caption=caption, images=[img], checks=rep)


def _wrap(fn, **fixed):
    return lambda ctx, out_dir, sizes=("feed",), **kw: fn(ctx, out_dir, sizes, **{**fixed, **kw})


BUILDERS = {
    "recap": recap,
    "slate": slate,
    "trend": trend,
    "fantasy_rb": _wrap(fantasy, focus="rb"),
    "fantasy_wr": _wrap(fantasy, focus="wr"),
    "mnf": _wrap(primetime, slot="mnf", media="feed"),
    "tnf_story": _wrap(primetime, slot="tnf", media="story"),
    "snf_story": _wrap(primetime, slot="snf", media="story"),
    "mnf_story": _wrap(primetime, slot="mnf", media="story"),
    "gameday_story": gameday_story,
    "featured": _wrap(primetime, slot="snf", media="feed"),
}
