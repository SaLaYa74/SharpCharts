"""SharpCharts as a stats page (owner, Oct 31: "just raw data... like a stat page", no betting framing).

Every Reel opens on a bold claim: the #1 number in huge type ("38.4 Fantasy Points. Guess Who?"), then
counts down #5 → #1 so people stay to see who it is.

NFL: team scoring from nflverse final scores (each verified against ESPN in posts.Context); fantasy points from
     nflverse weekly player stats, where every player-week's PPR total must equal our own recount from his raw
     yards, catches and touchdowns.
NBA: team scoring from ESPN finals (quarter scores add up, records match ESPN game by game; see nba.py);
     nightly top scorers from ESPN box scores, where each team's player points must add up to its final score
     and each team's top scorer must match the leader ESPN shows on its scoreboard.
"""
from datetime import timedelta

from . import checks as C
from . import data as D
from . import light as L
from . import nba as N
from .posts import DataError, NoContent, _player_weeks
from .v2 import COOL, GREEN, RED, _post, short

NFL_DATA = "Data: nflverse, every final score verified vs. ESPN."
NBA_DATA = "Data: ESPN, final scores verified (quarters add up, records match)."
NBA_BOX = "Data: ESPN box scores; each team's player points add up to its final score."
SUMMARY = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/summary?event={}"
NFL_TAGS = "#nfl #nflstats #football #nflfootball"
NBA_TAGS = "#nba #nbastats #basketball #nbahighlights"


def _rec(w, l_, t=0):
    return f"{w}-{l_}" + (f"-{t}" if t else "")


def _countdown(out_dir, key, name, items, title, hl, sub, source, cap, rep, color=GREEN, chart=L.bars):
    """chart: L.bars (vertical) or L.hbars (horizontal, Nov 6: owner wants more variety in how posts look)."""
    return _post(out_dir, key, name, lambda r, t: chart(title, hl, sub, items, source, hl_color=color,
                                                        reveal=r, tease=t), cap, rep, countdown=len(items))


# ---------------------------------------------------------------- NFL teams

def nfl_teams(ctx, rep):
    """abbr -> games, points for/against, W-L-T, from the verified finals; must match the season records."""
    t = {}
    for g in ctx.finals:
        for k, o in (("home", "away"), ("away", "home")):
            r = t.setdefault(g[f"{k}_team"], {"g": 0, "pf": 0, "pa": 0, "w": 0, "l": 0, "t": 0})
            d = g[f"{k}_score"] - g[f"{o}_score"]
            r["g"] += 1
            r["pf"] += g[f"{k}_score"]
            r["pa"] += g[f"{o}_score"]
            r["w" if d > 0 else ("l" if d < 0 else "t")] += 1
    rep.require(len(t) == 32, "nfl: all 32 teams", f"{len(t)} teams")
    for a, r in t.items():
        R = ctx.recs[a]
        rep.require((r["g"], r["w"], r["l"], r["t"]) == (R["games"], R["su_W"], R["su_L"], R["su_T"]),
                    f"nfl: {a} games and record match", f"{r} vs {R}")
        rep.require(8 <= r["pf"] / r["g"] <= 45 and 8 <= r["pa"] / r["g"] <= 45, f"nfl: {a} scoring plausible",
                    f"{r['pf']}/{r['pa']} in {r['g']}")
        r["ppg"], r["diff"] = r["pf"] / r["g"], (r["pf"] - r["pa"]) / r["g"]
        r["record"] = _rec(r["w"], r["l"], r["t"])
    return t


def nfl_offense(ctx, out_dir, sizes=None):
    rep = C.Report("stats nfl offense").extend(ctx.report)
    t = nfl_teams(ctx, rep)
    rows = sorted(t.items(), key=lambda kv: (-kv[1]["ppg"], kv[0]))[:5]
    top_a, top = rows[0]
    items = [{"label": D.TEAMS[a][0], "sub": r["record"], "value": r["ppg"], "icon": a, "value_label": f"{r['ppg']:.1f}",
              "color": COOL[i]} for i, (a, r) in enumerate(rows)]
    wk = ctx.thru_week
    key = f"{ctx.season}-wk{wk:02d}-st-offense"
    team = D.TEAMS[top_a][0]
    cap = (
        f"One NFL offense is putting up {top['ppg']:.1f} points a game. It's the {team} 🔥\n\n"
        + "\n".join(f"{i + 1}. {D.TEAMS[a][0]}: {r['ppg']:.1f} points per game ({r['record']})" for i, (a, r) in enumerate(rows))
        + "\n\nWhich offense would you least want to face? 👇"
        + f"\n\n📤 Send this to a {team} fan.")
    cap += f"\n\nPoints per game, every game through Week {wk}.\n{NFL_DATA}\n{NFL_TAGS}"
    return _countdown(out_dir, key, "st_offense", items, "{hl} Points a Game. Who?", f"{top['ppg']:.1f}",
                      f"Highest-scoring NFL offenses · thru Week {wk}", "nflverse · scores verified vs ESPN", cap, rep)


def nfl_dominant(ctx, out_dir, sizes=None):
    rep = C.Report("stats nfl margin").extend(ctx.report)
    t = nfl_teams(ctx, rep)
    rows = sorted(t.items(), key=lambda kv: (-kv[1]["diff"], kv[0]))[:5]
    top_a, top = rows[0]
    if top["diff"] <= 0:
        raise NoContent("No team has outscored its opponents yet.")
    items = [{"label": D.TEAMS[a][0], "sub": r["record"], "value": max(r["diff"], 0.1), "icon": a,
              "value_label": f"{r['diff']:+.1f}", "color": COOL[i]} for i, (a, r) in enumerate(rows)]
    wk = ctx.thru_week
    key = f"{ctx.season}-wk{wk:02d}-st-margin"
    team = D.TEAMS[top_a][0]
    cap = (
        f"The {team} are beating teams by {top['diff']:.1f} points a game. Nobody's been more dominant 😤\n\n"
        + "\n".join(f"{i + 1}. {D.TEAMS[a][0]}: {r['diff']:+.1f} per game ({r['record']}, {r['pf']}-{r['pa']} total)"
                    for i, (a, r) in enumerate(rows))
        + "\n\nWho's the best team in football right now? 👇"
        + f"\n\n📤 Send this to the {team} fan who won't stop talking about it.")
    cap += f"\n\nAverage point margin (points scored minus allowed, per game) through Week {wk}.\n{NFL_DATA}\n{NFL_TAGS}"
    return _countdown(out_dir, key, "st_margin", items, "Winning by {hl} a Game. Who?", f"{top['diff']:.1f}",
                      f"Biggest average margin · NFL · thru Week {wk}", "nflverse · scores verified vs ESPN", cap, rep,
                      chart=L.hbars)


def nfl_board(ctx, out_dir, sizes=None):
    """Every team on one screen by point differential. Built to be shared: everyone looks for their team."""
    rep = C.Report("stats nfl board").extend(ctx.report)
    t = nfl_teams(ctx, rep)
    rows = sorted(t.items(), key=lambda kv: (-(kv[1]["pf"] - kv[1]["pa"]), kv[0]))
    board = [{"icon": a, "label": D.TEAMS[a][0], "sub": r["record"], "value_label": f"{r['pf'] - r['pa']:+d}",
              "color": GREEN if r["pf"] >= r["pa"] else RED} for a, r in rows]
    wk = ctx.thru_week
    key = f"{ctx.season}-wk{wk:02d}-st-board"
    (ba, b), (wa, w) = rows[0], rows[-1]
    cap = (
        f"Find your team 👇 Every NFL team by point differential (points scored minus allowed).\n\n"
        f"Best: {D.TEAMS[ba][0]} {b['pf'] - b['pa']:+d}. Worst: {D.TEAMS[wa][0]} {w['pf'] - w['pa']:+d}.\n\n"
        + "\n".join(f"{i + 1}. {D.TEAMS[a][0]} ({r['record']}): {r['pf'] - r['pa']:+d}" for i, (a, r) in enumerate(rows))
        + "\n\n💬 Comment your team 👇 Better or worse than its record?"
        + f"\n\n📤 Send this to the {D.TEAMS[wa][0]} fan in your group chat 😬"
        + "\n🔁 New NFL board every Saturday. Follow to track your team all season.")
    cap += f"\n\nPoint differential, every game through Week {wk}.\n{NFL_DATA}\n{NFL_TAGS}"
    return _post(out_dir, key, "st_board", lambda p: L.board(
        "Find Your {hl}", "Team", f"Point differential · {D.TEAMS[ba][0]} lead at {b['pf'] - b['pa']:+d} · thru Week {wk}",
        board, "nflverse · scores verified vs ESPN", p=p, hl_color="#3B82F6"), cap, rep, hold=7.0)


# ---------------------------------------------------------------- NFL fantasy

_n = lambda v: float(v) if v not in ("", "NA", None) else 0.0


def ppr(r):
    """Our own PPR recount from a player-week's raw stats."""
    return (0.04 * _n(r["passing_yards"]) + 4 * _n(r["passing_tds"]) - 2 * _n(r["passing_interceptions"])
            + 0.1 * _n(r["rushing_yards"]) + 6 * _n(r["rushing_tds"]) + _n(r["receptions"]) + 0.1 * _n(r["receiving_yards"])
            + 6 * _n(r["receiving_tds"]) + 2 * (_n(r["passing_2pt_conversions"]) + _n(r["rushing_2pt_conversions"])
                                                + _n(r["receiving_2pt_conversions"]))
            - 2 * (_n(r["rushing_fumbles_lost"]) + _n(r["receiving_fumbles_lost"]) + _n(r["sack_fumbles_lost"]))
            + 6 * _n(r["special_teams_tds"]))


def _statline(r):
    parts = []
    if _n(r["attempts"]) >= 10:
        parts.append(f"{_n(r['passing_yards']):.0f} pass yds, {_n(r['passing_tds']):.0f} TD")
    if _n(r["carries"]) >= 5:
        parts.append(f"{_n(r['rushing_yards']):.0f} rush yds" + (f", {_n(r['rushing_tds']):.0f} TD" if _n(r["rushing_tds"]) else ""))
    if _n(r["targets"]) >= 3:
        parts.append(f"{_n(r['receptions']):.0f} catches, {_n(r['receiving_yards']):.0f} yds"
                     + (f", {_n(r['receiving_tds']):.0f} TD" if _n(r["receiving_tds"]) else ""))
    return " · ".join(parts)


def nfl_fantasy_week(ctx, out_dir, sizes=None):
    """Last week's top PPR scorers, all positions."""
    wk = ctx.thru_week
    rep = C.Report("stats fantasy week").extend(ctx.report)
    rows = [r for r in _player_weeks(ctx.season, wk) if int(r["week"]) == wk]
    rep.require(len(rows) > 250, f"fantasy: week {wk} player stats loaded", f"only {len(rows)} player rows")
    off = [r["player_display_name"] for r in rows if abs(ppr(r) - _n(r["fantasy_points_ppr"])) > 0.011]
    rep.require(not off, "fantasy: every PPR total equals our recount from raw stats", f"differs for {off[:5]}")
    top = sorted(rows, key=lambda r: -_n(r["fantasy_points_ppr"]))[:5]
    for r in top:
        rep.require(0 < _n(r["fantasy_points_ppr"]) <= 70, f"fantasy: {r['player_display_name']} points plausible",
                    r["fantasy_points_ppr"])
    items = [{"label": short(r["player_display_name"]), "sub": f"{r['position']} · {r['team']}", "value": _n(r["fantasy_points_ppr"]),
              "icon": r["team"], "value_label": f"{_n(r['fantasy_points_ppr']):.1f}", "color": COOL[i]} for i, r in enumerate(top)]
    lead = top[0]
    key = f"{ctx.season}-wk{wk:02d}-st-fantasy"
    cap = (
        f"{lead['player_display_name']} dropped {_n(lead['fantasy_points_ppr']):.1f} fantasy points in Week {wk} 🔥\n\n"
        + "\n".join(f"{i + 1}. {r['player_display_name']} ({r['position']}, {r['team']}): {_n(r['fantasy_points_ppr']):.1f} pts. {_statline(r)}"
                    for i, r in enumerate(top))
        + "\n\nWho carried your fantasy team this week? 👇"
        + "\n\n📤 Send this to the person who benched one of them 😅")
    cap += f"\n\nPPR scoring (1 point per catch). Raw data, no projections.\nData: nflverse player stats.\n#fantasyfootball #nfl #ppr #week{wk}"
    return _countdown(out_dir, key, "st_fantasy", items, "{hl} Fantasy Points. Guess Who.", f"{_n(lead['fantasy_points_ppr']):.1f}",
                      f"Top PPR scorers · NFL Week {wk}", "nflverse player stats", cap, rep)


# ---------------------------------------------------------------- NBA teams

def nba_teams(rep):
    finals, thru = N.season(rep, lines=False)
    t = {}
    for g in finals:
        for k, o in (("home", "away"), ("away", "home")):
            r = t.setdefault(g[k], {"g": 0, "pf": 0, "pa": 0, "w": 0, "l": 0})
            r["g"] += 1
            r["pf"] += g[f"{k}_score"]
            r["pa"] += g[f"{o}_score"]
            r["w" if g[f"{k}_score"] > g[f"{o}_score"] else "l"] += 1
    rep.require(len(t) == 30, "nba: all 30 teams have played", f"{len(t)} teams")
    if min(r["g"] for r in t.values()) < N.MIN_GAMES:
        raise NoContent("Too early: some NBA teams have fewer than 3 games.")
    for a, r in t.items():
        r["ppg"], r["diff"], r["record"] = r["pf"] / r["g"], (r["pf"] - r["pa"]) / r["g"], _rec(r["w"], r["l"])
        rep.require(85 <= r["ppg"] <= 140, f"nba: {a} scoring plausible", f"{r['ppg']:.1f} ppg")
    return t, thru


def _nba_items(rows, value, label):
    return [{"label": N.name(a), "sub": r["record"], "value": value(r), "icon": f"nba:{a}", "value_label": label(r),
             "color": COOL[i]} for i, (a, r) in enumerate(rows)]


def nba_offense(out_dir):
    rep = C.Report("stats nba offense")
    t, thru = nba_teams(rep)
    rows = sorted(t.items(), key=lambda kv: (-kv[1]["ppg"], kv[0]))[:5]
    top_a, top = rows[0]
    key = N._week_key(thru, "offense")
    cap = (
        f"The {N.name(top_a)} are scoring {top['ppg']:.1f} points a game. Best offense in the NBA right now 🔥\n\n"
        + "\n".join(f"{i + 1}. {N.name(a)}: {r['ppg']:.1f} ppg ({r['record']})" for i, (a, r) in enumerate(rows))
        + "\n\nWhich offense would you least want to guard? 👇"
        + f"\n\n📤 Send this to a {N.name(top_a)} fan.")
    cap += f"\n\nPoints per game, every game through {thru:%b} {thru.day}.\n{NBA_DATA}\n{NBA_TAGS}"
    return _countdown(out_dir, key, "nba_offense", _nba_items(rows, lambda r: r["ppg"], lambda r: f"{r['ppg']:.1f}"),
                      "{hl} Points a Game. Who?", f"{top['ppg']:.1f}", f"Highest-scoring NBA offenses · {N._thru(thru)}",
                      "ESPN · scores verified", cap, rep, chart=L.hbars)


def nba_dominant(out_dir):
    rep = C.Report("stats nba margin")
    t, thru = nba_teams(rep)
    rows = sorted(t.items(), key=lambda kv: (-kv[1]["diff"], kv[0]))[:5]
    top_a, top = rows[0]
    key = N._week_key(thru, "margin")
    cap = (
        f"The {N.name(top_a)} are winning by {top['diff']:.1f} points a game. Nobody's close 😤\n\n"
        + "\n".join(f"{i + 1}. {N.name(a)}: {r['diff']:+.1f} per game ({r['record']})" for i, (a, r) in enumerate(rows))
        + "\n\nWho's the real best team in the league? 👇"
        + f"\n\n📤 Send this to a {N.name(top_a)} fan.")
    cap += f"\n\nAverage point margin (scored minus allowed, per game) through {thru:%b} {thru.day}.\n{NBA_DATA}\n{NBA_TAGS}"
    return _countdown(out_dir, key, "nba_margin", _nba_items(rows, lambda r: max(r["diff"], 0.1), lambda r: f"{r['diff']:+.1f}"),
                      "Winning by {hl} a Game. Who?", f"{top['diff']:.1f}", f"Biggest average margin · NBA · {N._thru(thru)}",
                      "ESPN · scores verified", cap, rep)


def nba_board(out_dir):
    rep = C.Report("stats nba board")
    t, thru = nba_teams(rep)
    rows = sorted(t.items(), key=lambda kv: (-(kv[1]["pf"] - kv[1]["pa"]), kv[0]))
    board = [{"icon": f"nba:{a}", "label": N.name(a), "sub": r["record"], "value_label": f"{r['pf'] - r['pa']:+d}",
              "color": GREEN if r["pf"] >= r["pa"] else RED} for a, r in rows]
    (ba, b), (wa, w) = rows[0], rows[-1]
    key = N._week_key(thru, "board")
    cap = (
        f"Find your team 👇 All 30 NBA teams by point differential (points scored minus allowed).\n\n"
        f"Best: {N.name(ba)} {b['pf'] - b['pa']:+d}. Worst: {N.name(wa)} {w['pf'] - w['pa']:+d}.\n\n"
        + "\n".join(f"{i + 1}. {N.name(a)} ({r['record']}): {r['pf'] - r['pa']:+d}" for i, (a, r) in enumerate(rows))
        + "\n\n💬 Comment your team 👇 Is it for real?"
        + f"\n\n📤 Send this to the {N.name(wa)} fan in your group chat 😬"
        + "\n🔁 New NBA board every Monday. Follow to track your team all season.")
    cap += f"\n\nPoint differential, every game through {thru:%b} {thru.day}.\n{NBA_DATA}\n{NBA_TAGS}"
    return _post(out_dir, key, "nba_board", lambda p: L.board(
        "Find Your {hl}", "Team", f"Point differential · {N.name(ba)} lead at {b['pf'] - b['pa']:+d} · {N._thru(thru)}",
        board, "ESPN · scores verified", p=p, hl_color="#3B82F6"), cap, rep, hold=7.0)


# ---------------------------------------------------------------- NBA nightly top scorers

def _box(g, rep, leaders):
    """[(player, team, opp, pts, line)] from a final's ESPN box score, cross-checked as described above."""
    d = N._cached(SUMMARY.format(g["id"]), f"summary_{g['id']}.json", lambda d: bool((d.get("boxscore") or {}).get("players")))
    out = []
    label = f"{g['away']}@{g['home']} {g['day']}"
    blocks = (d.get("boxscore") or {}).get("players") or []
    rep.require(len(blocks) == 2, f"{label}: box score for both teams", f"{len(blocks)} teams")
    for b in blocks:
        abbr = b["team"]["abbreviation"]
        opp = g["away"] if abbr == g["home"] else g["home"]
        st = b["statistics"][0]
        keys = st.get("keys") or []
        if not rep.require("points" in keys, f"{label}: {abbr} box score has points", str(keys[:5])):
            continue
        ix = {k: keys.index(k) for k in keys}
        rows = []
        for a in st["athletes"]:
            s = a.get("stats") or []
            if a.get("didNotPlay") or len(s) != len(keys):
                continue
            pts = int(s[ix["points"]])
            rows.append((a["athlete"]["displayName"], a["athlete"]["id"], abbr, opp, pts,
                         f"{pts} PTS, {s[ix['rebounds']]} REB, {s[ix['assists']]} AST, {s[ix['fieldGoalsMade-fieldGoalsAttempted']]} FG"))
        team_pts = g["home_score"] if abbr == g["home"] else g["away_score"]
        rep.require(sum(r[4] for r in rows) == team_pts, f"{label}: {abbr} player points add up to {team_pts}",
                    f"box score sums to {sum(r[4] for r in rows)}")
        best = max(r[4] for r in rows) if rows else None
        if abbr in leaders:
            rep.require(best == leaders[abbr], f"{label}: {abbr} top scorer matches ESPN's scoreboard",
                        f"box {best} vs scoreboard {leaders[abbr]}")
        out += rows
    return out


def nba_scorers(out_dir, day=None):
    """Last night's top 5 scorers across the league."""
    day = day or N._today() - timedelta(days=1)
    rep = C.Report("stats nba scorers")
    finals, _, games = N.load_finals([day], rep, lines=False)
    if len(games) < 4:
        raise NoContent(f"Only {len(games)} NBA games on {day}.")
    pending = [g for g in games if not g["final"] and g["status"] not in ("STATUS_POSTPONED", "STATUS_CANCELED")]
    if pending:
        raise DataError(f"Waiting on {len(pending)} game(s) from {day} to go final")
    leaders = {}
    for _, e in N._events(day):
        for c in e["competitions"][0]["competitors"]:
            for ld in c.get("leaders") or []:
                if ld.get("name") == "points" and ld.get("leaders"):
                    leaders[(e["id"], c["team"]["abbreviation"])] = int(ld["leaders"][0]["value"])
    players = []
    for g in finals:
        players += _box(g, rep, {a: v for (eid, a), v in leaders.items() if eid == g["id"]})
    rep.require(len(players) >= 8 * len(finals), "box scores loaded for every final", f"{len(players)} player lines")
    top = sorted(players, key=lambda p: (-p[4], p[0]))[:5]
    items = [{"label": short(p[0]), "sub": f"{p[2]} vs {p[3]}", "value": p[4], "icon": f"nba:{p[2]}",
              "value_label": f"{p[4]}", "color": COOL[i]} for i, p in enumerate(top)]
    lead = top[0]
    key = f"nba-{day.isoformat()}-scorers"
    cap = (
        f"{lead[0]} dropped {lead[4]} points last night 🔥\n\n"
        + "\n".join(f"{i + 1}. {p[0]} ({p[2]} vs {p[3]}): {p[5]}" for i, p in enumerate(top))
        + "\n\nBest performance of the night? 👇"
        + f"\n\n📤 Send this to a {N.name(lead[2])} fan.")
    cap += f"\n\n{len(finals)} NBA games on {day:%a %b} {day.day}.\n{NBA_BOX}\n{NBA_TAGS}"
    return _countdown(out_dir, key, "nba_scorers", items, "{hl} Points Last Night. Guess Who.", f"{lead[4]}",
                      f"Top scorers · {len(finals)} NBA games · {day:%b} {day.day}", "ESPN box scores", cap, rep)



# ---------------------------------------------------------------- offense vs defense scatter (Nov 6, owner's idea)

QUADS = ("GOOD AT BOTH", "DEFENSE FIRST", "ALL OFFENSE", "STRUGGLING")


def _scatter(out_dir, key, name, t, team_name, logo, color, league, thru_label, source, data_line, tags, rep):
    """Every team as a logo: points scored (x) vs points allowed (y, flipped so better defense is higher)."""
    games = sum(r["g"] for r in t.values())
    avg = sum(r["pf"] for r in t.values()) / games
    rep.require(sum(r["pf"] for r in t.values()) == sum(r["pa"] for r in t.values()),
                f"{league}: league-wide points scored equal points allowed", "totals differ: a game is counted wrong")
    for r in t.values():
        r["papg"] = r["pa"] / r["g"]
    both = sorted((a for a, r in t.items() if r["ppg"] > avg and r["papg"] < avg), key=lambda a: -t[a]["diff"])
    worst = sorted((a for a, r in t.items() if r["ppg"] < avg and r["papg"] > avg), key=lambda a: t[a]["diff"])
    if not both:
        raise NoContent("No team is above average on both sides yet.")
    off = max(t, key=lambda a: (t[a]["ppg"], a))
    dfn = min(t, key=lambda a: (t[a]["papg"], a))
    pts = [{"x": r["ppg"], "y": r["papg"], "abbr": a, "logo": logo(a), "color": color(a)} for a, r in t.items()]
    n = len(both)
    title = ("Only {hl} Teams Are Good at Both" if n <= len(t) // 3 else "{hl} Teams Are Good at Both")
    cap = (
        f"{'Only ' if n <= len(t) // 3 else ''}{n} {league.upper()} teams score more AND allow less than the league average "
        f"({avg:.1f} points a game) 👀\n\n"
        f"🟢 Good at both: {', '.join(team_name(a) for a in both)}\n"
        + (f"🔴 Below average at both: {', '.join(team_name(a) for a in worst)}\n" if worst else "")
        + f"\nBest offense: {team_name(off)}, {t[off]['ppg']:.1f} points a game. "
        f"Best defense: {team_name(dfn)}, {t[dfn]['papg']:.1f} allowed.\n\n"
        "Where's your team? 👇\n\n📤 Send this to a fan whose team is stuck in the red corner."
        f"\n\nPoints scored and allowed per game, {thru_label}.\n{data_line}\n{tags}")
    return _post(out_dir, key, name, lambda p: L.scatter(
        title, str(n), f"Above the {league.upper()} average on offense and defense · {thru_label}", pts,
        "Points scored per game →", "Points allowed per game (fewer = higher) →", source, (avg, avg), QUADS, p=p),
        cap, rep, hold=5.0)


def nfl_scatter(ctx, out_dir, sizes=None):
    from .helmets import H as SHELL
    from .logos import logo_uri
    rep = C.Report("stats nfl scatter").extend(ctx.report)
    t = nfl_teams(ctx, rep)
    wk = ctx.thru_week
    return _scatter(out_dir, f"{ctx.season}-wk{wk:02d}-st-scatter", "st_scatter", t, lambda a: D.TEAMS[a][0], logo_uri,
                    lambda a: D.TEAMS[a][1] if a in D.TEAMS else SHELL[a][0], "nfl", f"thru Week {wk}",
                    "nflverse · scores verified vs ESPN", NFL_DATA, NFL_TAGS, rep)


def nba_scatter(out_dir):
    from .logos import logo_uri
    rep = C.Report("stats nba scatter")
    t, thru = nba_teams(rep)
    return _scatter(out_dir, N._week_key(thru, "scatter"), "nba_scatter", t, N.name, lambda a: logo_uri(a, "nba"),
                    lambda a: N.teams().get(a, {}).get("color", "#3A4A6B"), "nba", N._thru(thru),
                    "ESPN · scores verified", NBA_DATA, NBA_TAGS, rep)


BUILDERS_CTX = {"st_scatter": nfl_scatter, "st_offense": nfl_offense, "st_margin": nfl_dominant, "st_board": nfl_board, "st_fantasy": nfl_fantasy_week}
BUILDERS = {"nba_scatter": nba_scatter, "nba_scorers": nba_scorers, "nba_offense": nba_offense, "nba_margin": nba_dominant, "nba_board": nba_board}
