"""SharpCharts v2 Reels: plain English, one idea per graphic, big bright bars with team badges.

Money framing: "bet $100 on every game" profit, computed from each game's actual closing odds
(nflverse; -110 when odds are missing). Every number is derived from the verified Context data.
"""
from . import checks as C
from . import data as D
from . import light as L
from .posts import DISCLAIMER, NoContent, Post, fantasy_board, usage_movers, with_question
from .reels import make_reel, video_checks

GREEN, RED = "#16A34A", "#EF4444"
COOL = ["#16A34A", "#22C55E", "#14B8A6", "#3B82F6", "#6366F1"]      # winners: greens → blues
WARM = ["#DC2626", "#EF4444", "#F97316", "#FB923C", "#F59E0B"]      # losers: reds → oranges
SUFFIX = {"Jr.", "Jr", "Sr.", "Sr", "II", "III", "IV", "V"}


def short(name, limit=12):
    """Last name for long names, skipping suffixes (Kenneth Walker III → Walker)."""
    if len(name) <= limit:
        return name
    parts = [w for w in name.split() if w not in SUFFIX]
    return parts[-1] if parts else name


def _odds(v):
    try:
        o = float(v)
        return o if o != 0 and abs(o) >= 100 else -110.0
    except (TypeError, ValueError):
        return -110.0


def _win(odds):
    """Profit on a $100 winning bet at American odds."""
    return 100 * 100 / abs(odds) if odds < 0 else odds


def _bet(result, odds):
    return _win(odds) if result == "W" else (-100.0 if result == "L" else 0.0)


def profits(ctx, rep):
    """Per-team and per-angle profit of $100 flat bets on every game this season (against the spread / totals)."""
    team, angle, n = {}, {}, {}
    for g in ctx.finals:
        ho, ao = _odds(g.get("home_spread_odds")), _odds(g.get("away_spread_odds"))
        oo, uo = _odds(g.get("over_odds")), _odds(g.get("under_odds"))
        for o in (ho, ao, oo, uo):
            rep.require(-250 <= o <= 250 and abs(o) >= 100, f"odds plausible {g['game_id']}", f"odds {o}")
        h, a = g["home_team"], g["away_team"]
        rh, ra = D.ats_side(g, h), D.ats_side(g, a)
        team.setdefault(h, {"ats": 0.0, "over": 0.0})["ats"] += _bet(rh, ho)
        team.setdefault(a, {"ats": 0.0, "over": 0.0})["ats"] += _bet(ra, ao)
        ou = D.ou_side(g)
        over = _bet("W" if ou == "O" else ("L" if ou == "U" else "P"), oo)
        under = _bet("W" if ou == "U" else ("L" if ou == "O" else "P"), uo)
        team[h]["over"] += over
        team[a]["over"] += over
        add = lambda k, v: angle.__setitem__(k, angle.get(k, 0.0) + v)
        add("Home teams", _bet(rh, ho)); add("Road teams", _bet(ra, ao))
        if g["spread_line"]:
            fav_home = g["spread_line"] > 0
            add("Favorites", _bet(rh if fav_home else ra, ho if fav_home else ao))
            add("Underdogs", _bet(ra if fav_home else rh, ao if fav_home else ho))
        add("Overs", over); add("Unders", under)
        for t in (h, a):
            n[t] = n.get(t, 0) + 1
    for t, v in team.items():
        g_ = n[t]
        rep.require(abs(v["ats"]) <= g_ * 260, f"{t} profit plausible", f"{v['ats']:.0f} over {g_} games")
        rep.require(n[t] == ctx.recs[t]["games"], f"{t} game count matches records", f"{n[t]} vs {ctx.recs[t]['games']}")
    return team, angle


def money(v):
    return f"{'+' if v >= 0 else '-'}${abs(v):,.0f}"


def _reel(key, name, hook, html_fn, caption, rep, seed):
    out = f"/tmp/sc_v2_{name}"
    import os
    os.makedirs(out, exist_ok=True)
    return out


def _post(out_dir, key, name, html_fn, caption, rep):
    mp4, cover = make_reel(out_dir, name, ("", ""), html_fn, "", key)
    video_checks(rep, mp4)
    C.image(rep, cover, "reel")
    return Post(key=key, caption=caption, images=[{"reel": mp4, "cover": cover}], media="reel", checks=rep)


def _team_items(rows, value_key, sub_fn, palette=COOL):
    return [{"label": D.TEAMS[t][0], "sub": sub_fn(t), "value": abs(v[value_key]), "icon": t,
             "value_label": money(v[value_key]), "color": palette[i % len(palette)]} for i, (t, v) in enumerate(rows)]


def _record(ctx, t):
    r = ctx.recs[t]
    return f"won {r['ats_W']} of {r['ats_W'] + r['ats_L'] + r['ats_P']} bets"


def best_bets(ctx, out_dir, sizes=None):
    rep = C.Report("v2 best").extend(ctx.report)
    team, _ = profits(ctx, rep)
    rows = sorted(team.items(), key=lambda kv: -kv[1]["ats"])[:5]
    if rows[0][1]["ats"] <= 0:
        raise NoContent("No team is profitable yet.")
    items = _team_items(rows, "ats", lambda t: _record(ctx, t))
    key = f"{ctx.season}-wk{ctx.thru_week:02d}-v2-best"
    top = rows[0]
    cap = with_question(
        f"If you bet $100 on the {D.TEAMS[top[0]][0]} every week this season, you'd be up ${top[1]['ats']:,.0f} 💰\n\n"
        + "\n".join(f"🟢 {D.TEAMS[t][0]}: {money(v['ats'])} ({_record(ctx, t)})" for t, v in rows),
        "recap", key, best=D.TEAMS[top[0]][0], best_margin=money(top[1]["ats"]), worst=D.TEAMS[rows[-1][0]][0])
    cap += (f"\n\n$100 on every game against the spread, at closing odds, through Week {ctx.thru_week}.\n"
            f"Data: nflverse, scores verified vs ESPN.\n{DISCLAIMER}\n#nfl #nflbetting #sportsbetting #nflpicks")
    return _post(out_dir, key, "v2_best", lambda p: L.bars(
        "Best Teams to {hl}", "Bet On", f"$100 on every game this season, against the spread · thru Week {ctx.thru_week}",
        items, "nflverse closing lines", p=p, hl_color=GREEN), cap, rep)


def worst_bets(ctx, out_dir, sizes=None):
    rep = C.Report("v2 worst").extend(ctx.report)
    team, _ = profits(ctx, rep)
    rows = sorted(team.items(), key=lambda kv: kv[1]["ats"])[:5]
    if rows[0][1]["ats"] >= 0:
        raise NoContent("No team is losing money yet.")
    items = _team_items(rows, "ats", lambda t: _record(ctx, t), WARM)
    key = f"{ctx.season}-wk{ctx.thru_week:02d}-v2-worst"
    w = rows[0]
    cap = with_question(
        f"Bet $100 on the {D.TEAMS[w[0]][0]} every week? You'd be down {money(w[1]['ats'])[1:]} 😬\n\n"
        + "\n".join(f"🔴 {D.TEAMS[t][0]}: {money(v['ats'])} ({_record(ctx, t)})" for t, v in rows),
        "recap", key, best=D.TEAMS[rows[-1][0]][0], best_margin="", worst=D.TEAMS[w[0]][0])
    cap += (f"\n\n$100 on every game against the spread, at closing odds, through Week {ctx.thru_week}.\n"
            f"Data: nflverse, scores verified vs ESPN.\n{DISCLAIMER}\n#nfl #nflbetting #sportsbetting")
    return _post(out_dir, key, "v2_worst", lambda p: L.bars(
        "Worst Teams to {hl}", "Bet On", f"$100 on every game this season, against the spread · thru Week {ctx.thru_week}",
        items, "nflverse closing lines", p=p, hl_color=RED), cap, rep)


def which_bet_pays(ctx, out_dir, sizes=None):
    rep = C.Report("v2 angles").extend(ctx.report)
    _, angle = profits(ctx, rep)
    order = ["Favorites", "Underdogs", "Home teams", "Road teams", "Overs", "Unders"]
    icons = {"Favorites": "crown", "Underdogs": "dog", "Home teams": "home", "Road teams": "plane", "Overs": "up", "Unders": "down"}
    items = [{"label": k, "sub": "every game", "value": abs(angle[k]), "icon": icons[k], "value_label": money(angle[k]),
              "color": GREEN if angle[k] >= 0 else RED} for k in order if k in angle]
    best = max(order, key=lambda k: angle.get(k, -1e9))
    key = f"{ctx.season}-wk{ctx.thru_week:02d}-v2-angles"
    cap = with_question(
        f"$100 on every {best.lower().rstrip('s') if best.endswith('s') else best} this NFL season? You'd be {money(angle[best])} 📊\n\n"
        + "\n".join(f"{'🟢' if angle[k] >= 0 else '🔴'} Every {k.lower()}: {money(angle[k])}" for k in order if k in angle),
        "trend", key)
    cap += (f"\n\n$100 per game, all season, at closing odds, through Week {ctx.thru_week}. Green = profit, red = loss.\n"
            f"Data: nflverse, scores verified vs ESPN.\n{DISCLAIMER}\n#nfl #nflbetting #sportsbetting")
    return _post(out_dir, key, "v2_angles", lambda p: L.bars(
        "Which Bet {hl}", "Pays?", f"$100 on every game this NFL season · green = profit, red = loss · thru Week {ctx.thru_week}",
        items, "nflverse closing lines", p=p, hl_color="#3B82F6"), cap, rep)


def over_teams(ctx, out_dir, sizes=None):
    rep = C.Report("v2 overs").extend(ctx.report)
    team, _ = profits(ctx, rep)
    rows = sorted(team.items(), key=lambda kv: -kv[1]["over"])[:5]
    if rows[0][1]["over"] <= 0:
        raise NoContent("No profitable over teams yet.")
    items = [{"label": D.TEAMS[t][0], "sub": f"O/U {ctx.recs[t]['ou_O']}-{ctx.recs[t]['ou_U']}", "value": abs(v["over"]),
              "icon": t, "value_label": money(v["over"]), "color": COOL[i]} for i, (t, v) in enumerate(rows)]
    key = f"{ctx.season}-wk{ctx.thru_week:02d}-v2-overs"
    top = rows[0]
    cap = with_question(
        f"$100 on the OVER in every {D.TEAMS[top[0]][0]} game? You'd be up ${top[1]['over']:,.0f} 🔥\n\n"
        + "\n".join(f"🟢 {D.TEAMS[t][0]} games: {money(v['over'])}" for t, v in rows), "trend", key)
    cap += (f"\n\n$100 on the over in every game, at closing odds, through Week {ctx.thru_week}.\n"
            f"Data: nflverse, scores verified vs ESPN.\n{DISCLAIMER}\n#nfl #nflbetting #overunder")
    return _post(out_dir, key, "v2_overs", lambda p: L.bars(
        "Best Teams for the {hl}", "Over", f"$100 on the over in every game this season · thru Week {ctx.thru_week}",
        items, "nflverse closing lines", p=p, hl_color="#F97316"), cap, rep)


def _usage(ctx, out_dir, focus):
    b = fantasy_board(ctx, focus)
    rep = b["rep"]
    top = b["top"][:5]
    items = [{"label": short(p_["name"]), "sub": p_["team"],
              "value": p_["share"] * 100, "icon": p_["team"], "value_label": f"{p_['share'] * 100:.0f}%"} for p_ in top]
    key = f"{ctx.season}-wk{ctx.thru_week:02d}-v2-{focus}"
    lead = top[0]
    what = "carries + targets" if focus == "rb" else "targets"
    cap = with_question(
        f"{lead['name']} is getting {lead['share'] * 100:.0f}% of his team's {what}. Nobody's busier 🏈\n\n"
        + "\n".join(f"{i + 1}. {p_['name']} ({p_['team']}): {p_['share'] * 100:.0f}%" for i, p_ in enumerate(top)),
        "fantasy", key, top=lead["name"], second=top[1]["name"])
    cap += (f"\n\nShare of team {what}, season to date (min. {b['min_games']} games). Raw data, no projections. "
            f"Data: nflverse.\n{DISCLAIMER}\n{b['hashtags']}")
    title, hl = ("Who Gets the {hl}", "Ball") if focus == "rb" else ("Who Gets {hl}", "Targeted")
    return _post(out_dir, key, f"v2_{focus}", lambda p: L.bars(
        title, hl, f"Share of team {what} · season to date · thru Week {ctx.thru_week}", items,
        "nflverse player stats", p=p, hl_color="#3B82F6"), cap, rep)


def touches(ctx, out_dir, sizes=None):
    return _usage(ctx, out_dir, "rb")


def targets(ctx, out_dir, sizes=None):
    return _usage(ctx, out_dir, "wr")


def waiver(ctx, out_dir, sizes=None):
    risers, _, rep = usage_movers(ctx, n=5)
    pct = lambda x: f"{x * 100:.0f}%"
    items = [{"label": short(m["name"]), "sub": f"{pct(m['base'])} → {pct(m['now'])}",
              "value": m["delta"] * 100, "icon": m["team"], "value_label": f"+{m['delta'] * 100:.0f}"} for m in risers]
    key = f"{ctx.season}-wk{ctx.thru_week:02d}-v2-waiver"
    top = risers[0]
    cap = with_question(
        f"Waiver wire alert: {top['name']} went from {pct(top['base'])} to {pct(top['now'])} of his team's touches 📈\n\n"
        + "\n".join(f"🟢 {m['name']} ({m['team']} {m['pos']}): {pct(m['base'])} → {pct(m['now'])}" for m in risers),
        "fantasy", key, top=top["name"], second=risers[1]["name"])
    cap += (f"\n\nShare of team carries + targets, Week {ctx.thru_week} vs. earlier weeks. Raw data, no projections. "
            f"Data: nflverse.\n{DISCLAIMER}\n#fantasyfootball #waiverwire #week{ctx.thru_week + 1}")
    return _post(out_dir, key, "v2_waiver", lambda p: L.bars(
        "Waiver Wire {hl}", "Risers", f"Biggest jump in share of team touches · Week {ctx.thru_week} vs. before",
        items, "nflverse player stats", p=p, hl_color=GREEN), cap, rep)


BUILDERS = {"v2_best": best_bets, "v2_worst": worst_bets, "v2_angles": which_bet_pays, "v2_overs": over_teams,
            "v2_rb": touches, "v2_wr": targets, "v2_waiver": waiver}
