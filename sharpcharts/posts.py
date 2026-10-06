"""Post builders shared by generate.py (manual) and autopost.py (scheduled).

Each builder returns a Post: a stable `key` (for duplicate protection), a list of
rendered image paths (1 = single image, 2-10 = carousel) and a caption.
All season stats are computed through the last *fully completed* week so a
post never mixes partial weeks.
"""
import os
from dataclasses import dataclass, field

from . import data as D
from . import templates as T
from .render import html_to_png

SRC = "nflverse (scores + lines) · ESPN (verified)"
DISCLAIMER = "21+ | Gamble responsibly · 1-800-GAMBLER"
MAX_CAROUSEL = 10  # Instagram API limit


class DataError(Exception):
    """Raised when data fails verification or isn't ready; nothing should be posted."""


@dataclass
class Post:
    key: str
    caption: str
    images: list = field(default_factory=list)


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

def recap(ctx, out_dir, sizes=("feed",)):
    """Tuesday carousel: ATS best/worst, league splits, over/under teams."""
    recs, thru, note = ctx.recs, ctx.thru, ctx.thru_note

    def ats_row(t):
        r = recs[t]
        v = r["cover_margin_sum"] / r["games"]
        return {"abbr": t, "color": D.TEAMS[t][1], "name": D.TEAMS[t][0], "value": v,
                "value_label": f"{v:+.1f}",
                "record": f"{rec(r['ats_W'], r['ats_L'], r['ats_P'])} ATS · {rec(r['su_W'], r['su_L'], r['su_T'])} SU",
                "ats": rec(r["ats_W"], r["ats_L"], r["ats_P"]),
                "pct": r["ats_W"] / max(1, r["ats_W"] + r["ats_L"])}
    ranked = sorted((ats_row(t) for t in recs), key=lambda x: (x["pct"], x["value"]), reverse=True)
    top, bottom = ranked[:6], ranked[-6:]

    sp = D.league_splits(ctx.finals)
    split_items = [
        {"label": "Favorites vs underdogs (ATS)", "left": ("Favs", sp["fav_W"]), "right": ("Dogs", sp["fav_L"])},
        {"label": "Home vs away (ATS)", "left": ("Home", sp["home_W"]), "right": ("Away", sp["home_L"])},
        {"label": "Totals", "left": ("Over", sp["ou_O"]), "right": ("Under", sp["ou_U"])},
        {"label": "Underdogs winning outright", "left": ("Dog wins", sp["dog_outright_W"]), "right": ("Fav wins", sp["dog_outright_L"])},
    ]

    def ou_row(t):
        r = recs[t]
        v = r["ou_margin_sum"] / r["games"]
        return {"abbr": t, "color": D.TEAMS[t][1], "name": D.TEAMS[t][0], "value": v,
                "value_label": f"{v:+.1f}", "record": f"O/U {rec(r['ou_O'], r['ou_U'], r['ou_P'])}",
                "ou": rec(r["ou_O"], r["ou_U"], r["ou_P"]),
                "pct": r["ou_O"] / max(1, r["ou_O"] + r["ou_U"])}
    ou_ranked = sorted((ou_row(t) for t in recs), key=lambda x: (x["pct"], x["value"]), reverse=True)

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
        "Save this for your weekly card 📌\n\n"
        f"Data: nflverse closing lines, scores verified vs ESPN. Pushes excluded from splits.\n{DISCLAIMER}\n"
        "#nflbetting #sportsbetting #nfl #ats #overunder #bettingdata"
    )
    return Post(key=f"{ctx.season}-wk{ctx.thru_week:02d}-recap", caption=caption,
                images=[s for s in slides])


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
    return {"game": g, "paths": paths, "line": line_info, "stats": stats}


def _live_lines(ctx, week):
    try:
        return D.espn_lines_for_week(ctx.games, week)
    except Exception as e:  # ESPN down → nflverse lines only
        print("  ! ESPN lines unavailable:", e)
        return {}


def slate(ctx, out_dir, sizes=("feed",), week=None):
    """Thursday carousel: slate cover (every game) + up to 9 matchup cards."""
    week = week or ctx.upcoming_week
    games = sorted((g for g in ctx.games if g["week"] == week and not g["final"]),
                   key=lambda g: (g["gameday"], g["gametime"]))
    if not games:
        raise DataError(f"No unplayed games in week {week}.")
    live = _live_lines(ctx, week)
    rows = [{"kick": f"{g['weekday'][:3]} {clock(g['gametime'])}",
             "away": (g["away_team"], D.TEAMS[g["away_team"]][1]),
             "home": (g["home_team"], D.TEAMS[g["home_team"]][1]),
             "spread": spread_text(g["home_team"], g["away_team"], g["spread_line"]),
             "total": f"{g['total_line']:g}" if g["total_line"] else "OFF"} for g in games]
    cover = _render(lambda s: T.slate(week, rows, tag=f"NFL · Week {week}", source=SRC, size=s,
                                      note="Consensus lines · check your book, lines move"),
                    out_dir, "00_slate", sizes)
    # Feature primetime games first, then the closest spreads; show in kickoff order.
    priced = [g for g in games if g["spread_line"] is not None and g["total_line"] is not None]
    picks = sorted(priced, key=lambda g: (not _primetime(g), abs(g["spread_line"])))[:MAX_CAROUSEL - 1]
    picks = sorted(picks, key=lambda g: (g["gameday"], g["gametime"]))
    cards = [c for c in (_matchup_card(ctx, g, live, out_dir, sizes) for g in picks) if c]
    lines = "\n".join(f"{D.TEAMS[c['game']['away_team']][0]} @ {D.TEAMS[c['game']['home_team']][0]}: "
                      f"{c['line'][0][1]}, O/U {c['line'][1][1]}" for c in cards)
    caption = (
        f"Week {week} NFL betting slate 🏈\n\n"
        f"Slide 1: every game's spread & total. Swipe for {len(cards)} matchup breakdowns ➡️\n\n"
        f"{lines}\n\n"
        f"Season ATS & O/U records {ctx.thru.lower()}. Lines move, so check your book before betting.\n\n"
        "Which side are you on? 👇\n\n"
        f"{DISCLAIMER}\n#nfl #nflbetting #sportsbetting #week{week} #nflpicks #bettingdata"
    )
    return Post(key=f"{ctx.season}-wk{week:02d}-slate", caption=caption,
                images=[cover] + [c["paths"] for c in cards])


def featured(ctx, out_dir, sizes=("feed",), week=None):
    """Saturday single: the Sunday night game (or the closest-spread game if none)."""
    week = week or ctx.upcoming_week
    games = [g for g in ctx.games if g["week"] == week and not g["final"]]
    if not games:
        raise DataError(f"No unplayed games in week {week}.")
    games = [g for g in games if g["spread_line"] is not None and g["total_line"] is not None]
    if not games:
        raise DataError(f"No week {week} games have lines posted yet.")
    snf = [g for g in games if g["weekday"] == "Sunday" and _primetime(g)]
    g = snf[0] if snf else min(games, key=lambda x: abs(x["spread_line"]))
    card = _matchup_card(ctx, g, _live_lines(ctx, week), out_dir, sizes)
    if card is None:
        raise DataError("Not enough data for the featured game.")
    a, h = D.TEAMS[g["away_team"]][0], D.TEAMS[g["home_team"]][0]
    st = card["stats"]
    label = "Sunday Night Football" if snf else "Game of the week"
    caption = (
        f"{label}: {a} @ {h} 🏈\n\n"
        f"Line: {card['line'][0][1]} · O/U {card['line'][1][1]}\n"
        f"{a} ATS: {st[1][1]} (avg cover {st[2][1]})\n"
        f"{h} ATS: {st[1][2]} (avg cover {st[2][2]})\n"
        f"O/U: {a} {st[3][1]} · {h} {st[3][2]}\n\n"
        f"Who's covering? Drop your side 👇\n\n"
        f"Stats {ctx.thru.lower()}. Lines move, so check your book.\n{DISCLAIMER}\n"
        f"#nfl #nflbetting #{a.lower()} #{h.lower()} #sportsbetting #snf"
    )
    return Post(key=f"{ctx.season}-wk{week:02d}-featured", caption=caption, images=[card["paths"]])


BUILDERS = {"recap": recap, "slate": slate, "featured": featured}
