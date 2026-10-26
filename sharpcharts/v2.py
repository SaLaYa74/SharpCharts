"""SharpCharts v2 Reels: plain English, one idea per graphic, big bright bars with team badges.

Money framing: "bet $100 on every game" profit, computed from each game's actual closing odds
(nflverse; -110 when odds are missing). Every number is derived from the verified Context data.
"""
from . import checks as C
from . import data as D
from . import light as L
from .posts import DISCLAIMER, DataError, NoContent, Post, fantasy_board, usage_movers, with_question
from .reels import make_countdown, make_reel, video_checks

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


def _post(out_dir, key, name, html_fn, caption, rep, hold=4.0, countdown=0):
    """countdown=n: html_fn takes (reveal, tease) and the Reel reveals #n → #1; otherwise html_fn(p) builds in."""
    if countdown:
        mp4, cover = make_countdown(out_dir, name, html_fn, countdown, key)
    else:
        mp4, cover = make_reel(out_dir, name, ("", ""), html_fn, "", key, hold=hold)
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
        f"The {D.TEAMS[top[0]][0]} have been an ATM for bettors 💰 $100 on them every week = up ${top[1]['ats']:,.0f}.\n\n"
        + "\n".join(f"🟢 {D.TEAMS[t][0]}: {money(v['ats'])} ({_record(ctx, t)})" for t, v in rows),
        "recap", key, best=D.TEAMS[top[0]][0], best_margin=money(top[1]["ats"]), worst=D.TEAMS[rows[-1][0]][0])
    cap += (f"\n\n$100 on every game against the spread, at closing odds, through Week {ctx.thru_week}.\n"
            f"Data: nflverse, scores verified vs ESPN.\n{DISCLAIMER}\n#nfl #nflbetting #sportsbetting #nflpicks")
    cap = cap.replace("\n\n$100 on every game", f"\n\n📤 Send this to a {D.TEAMS[top[0]][0]} fan. They've earned it.\n\n$100 on every game", 1)
    return _post(out_dir, key, "v2_best", lambda r, t: L.bars(
        "Which Team {hl} Bettors Most?", "Paid", f"$100 on every game, against the spread · thru Week\u00a0{ctx.thru_week}",
        items, "nflverse closing lines", hl_color=GREEN, reveal=r, tease=t), cap, rep, countdown=len(items))


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
        f"The {D.TEAMS[w[0]][0]} have cost bettors {money(w[1]['ats'])[1:]} this season. Nobody's been worse 😬\n\n"
        + "\n".join(f"🔴 {D.TEAMS[t][0]}: {money(v['ats'])} ({_record(ctx, t)})" for t, v in rows),
        "recap", key, best=D.TEAMS[rows[-1][0]][0], best_margin="", worst=D.TEAMS[w[0]][0])
    cap += (f"\n\n$100 on every game against the spread, at closing odds, through Week {ctx.thru_week}.\n"
            f"Data: nflverse, scores verified vs ESPN.\n{DISCLAIMER}\n#nfl #nflbetting #sportsbetting")
    cap = cap.replace("\n\n$100 on every game", f"\n\n📤 Send this to the {D.TEAMS[w[0]][0]} fan in your group chat 😬\n\n$100 on every game", 1)
    return _post(out_dir, key, "v2_worst", lambda r, t: L.bars(
        "Which Team {hl} Bettors Most?", "Burned", f"$100 on every game, against the spread · thru Week\u00a0{ctx.thru_week}",
        items, "nflverse closing lines", hl_color=RED, reveal=r, tease=t), cap, rep, countdown=len(items))


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
        "Which Bet {hl}", "Pays?", f"$100 on every game this NFL season · green = profit, red = loss · thru Week\u00a0{ctx.thru_week}",
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
        f"{D.TEAMS[top[0]][0]} games keep blowing past the total 🔥 $100 on the over every week = up ${top[1]['over']:,.0f}.\n\n"
        + "\n".join(f"🟢 {D.TEAMS[t][0]} games: {money(v['over'])}" for t, v in rows), "trend", key)
    cap += (f"\n\n$100 on the over in every game, at closing odds, through Week {ctx.thru_week}.\n"
            f"Data: nflverse, scores verified vs ESPN.\n{DISCLAIMER}\n#nfl #nflbetting #overunder")
    return _post(out_dir, key, "v2_overs", lambda r, t: L.bars(
        "Whose Games Hit the {hl}?", "Over", f"$100 on the over, every game · thru Week\u00a0{ctx.thru_week}",
        items, "nflverse closing lines", hl_color="#F97316", reveal=r, tease=t), cap, rep, countdown=len(items))


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
    title, hl = ("Who Gets the {hl} Most?", "Ball") if focus == "rb" else ("Who Gets {hl} Most?", "Targeted")
    return _post(out_dir, key, f"v2_{focus}", lambda r, t: L.bars(
        title, hl, f"Share of team {what} · season to date · thru Week\u00a0{ctx.thru_week}", items,
        "nflverse player stats", hl_color="#3B82F6", reveal=r, tease=t), cap, rep, countdown=len(items))


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
        f"🚨 Waiver alert: {top['name']} just jumped from {pct(top['base'])} to {pct(top['now'])} of his team's touches. Grab him before your league does 📈\n\n"
        + "\n".join(f"🟢 {m['name']} ({m['team']} {m['pos']}): {pct(m['base'])} → {pct(m['now'])}" for m in risers),
        "fantasy", key, top=top["name"], second=risers[1]["name"])
    cap += (f"\n\nShare of team carries + targets, Week {ctx.thru_week} vs. earlier weeks. Raw data, no projections. "
            f"Data: nflverse.\n{DISCLAIMER}\n#fantasyfootball #waiverwire #week{ctx.thru_week + 1}")
    return _post(out_dir, key, "v2_waiver", lambda r, t: L.bars(
        "Who's {hl} on Waivers?", "Rising", f"Biggest jump in share of team touches · Week {ctx.thru_week} vs. before",
        items, "nflverse player stats", hl_color=GREEN, reveal=r, tease=t), cap, rep, countdown=len(items))



def _ats(ctx, t):
    r = ctx.recs[t]
    return f"{r['ats_W']}-{r['ats_L']}" + (f"-{r['ats_P']}" if r["ats_P"] else "") + " ATS"


def all_teams(ctx, out_dir, sizes=None):
    """Every team's $100-a-game profit on one screen. Built to be shared: everyone looks for their team."""
    rep = C.Report("v2 all32").extend(ctx.report)
    team, _ = profits(ctx, rep)
    rep.require(len(team) == 32, "all 32 teams on the board", f"{len(team)} teams")
    rows = sorted(team.items(), key=lambda kv: -kv[1]["ats"])
    board = [{"icon": t, "label": D.TEAMS[t][0], "sub": _ats(ctx, t), "value_label": money(v["ats"]),
              "color": GREEN if v["ats"] >= 0 else RED} for t, v in rows]
    key = f"{ctx.season}-wk{ctx.thru_week:02d}-v2-all32"
    best, worst = rows[0], rows[-1]
    up = sum(1 for _, v in rows if v["ats"] > 0)
    cap = with_question(
        f"Find your team 👇 $100 on every game this NFL season, all 32 teams.\n\n"
        f"Best: {D.TEAMS[best[0]][0]} {money(best[1]['ats'])}. Worst: {D.TEAMS[worst[0]][0]} {money(worst[1]['ats'])}. "
        f"Only {up} of 32 teams made you money.\n\n"
        + "\n".join(f"{i + 1}. {D.TEAMS[t][0]}: {money(v['ats'])}" for i, (t, v) in enumerate(rows))
        + f"\n\n📤 Send this to the {D.TEAMS[worst[0]][0]} fan in your group chat 😬 📌 Save it to check next week.",
        "recap", key, best=D.TEAMS[best[0]][0], best_margin=money(best[1]["ats"]), worst=D.TEAMS[worst[0]][0])
    cap += (f"\n\n$100 on every game against the spread, at closing odds, through Week {ctx.thru_week}.\n"
            f"Data: nflverse, scores verified vs ESPN.\n{DISCLAIMER}\n#nfl #nflbetting #sportsbetting #nflfans")
    return _post(out_dir, key, "v2_all32", lambda p: L.board(
        "Find Your {hl}", "Team", f"$100 on every game, against the spread · thru Week\u00a0{ctx.thru_week}",
        board, "nflverse closing lines", p=p, hl_color="#3B82F6"), cap, rep, hold=7.0)


def upsets(ctx, out_dir, sizes=None):
    """Last week's underdogs that won outright, and what $100 on their moneyline paid."""
    rep = C.Report("v2 upsets").extend(ctx.report)
    wk = ctx.thru_week
    games = [g for g in ctx.finals if g["week"] == wk]
    rep.require(len(games) >= 10, f"week {wk}: full slate", f"only {len(games)} games")
    from datetime import date, timedelta
    last = max(g["gameday"] for g in games)
    if last < (date.today() - timedelta(days=4)).isoformat():    # last week's games aren't final in the data yet
        raise DataError(f"Week {wk} ended {last}; waiting for the newest week to be final.")
    wins, net, dogs = [], 0.0, 0
    for g in games:
        h, a, hml, aml = g["home_team"], g["away_team"], g["home_moneyline"], g["away_moneyline"]
        if hml is None or aml is None:
            rep.expect(False, f"{g['game_id']}: moneylines present", "missing moneyline, game left out")
            continue
        C.line_ranges(rep, "nfl", g["game_id"], moneylines=(hml, aml))
        if hml == aml or max(hml, aml) < 100:
            continue                                          # pick'em: no real underdog
        dog, fav, dml = (h, a, hml) if hml > aml else (a, h, aml)
        sl = g["spread_line"]                                 # > 0 means the home team is favored
        if sl:
            spread_dog = a if sl > 0 else h
            if not rep.expect(spread_dog == dog, f"{g['game_id']}: moneyline and spread agree on the underdog",
                              f"spread says {spread_dog}, moneyline says {dog}; game left out"):
                continue
        ds, fs = (g["home_score"], g["away_score"]) if dog == h else (g["away_score"], g["home_score"])
        rep.require(ds is not None and fs is not None, f"{g['game_id']}: final score", "score missing")
        dogs += 1
        if ds > fs:
            net += dml
            wins.append({"dog": dog, "fav": fav, "ml": dml, "score": f"{ds}-{fs}"})
        elif ds < fs:
            net -= 100
    if not wins:
        raise NoContent(f"No underdog won outright in Week {wk}.")
    wins.sort(key=lambda w: -w["ml"])
    top = wins[:5]
    pal = COOL
    items = [{"label": D.TEAMS[w["dog"]][0], "sub": f"{w['score'].replace('-', chr(8209))} vs {D.TEAMS[w['fav']][0]}", "value": w["ml"],
              "icon": w["dog"], "value_label": money(w["ml"]), "color": pal[i % len(pal)]} for i, w in enumerate(top)]
    key = f"{ctx.season}-wk{wk:02d}-v2-upsets"
    w0 = top[0]
    cap = (
        f"The {D.TEAMS[w0['dog']][0]} were +{w0['ml']:.0f} underdogs against the {D.TEAMS[w0['fav']][0]}. "
        f"$100 on them paid ${w0['ml']:,.0f} 🐶\n\n"
        + "\n".join(f"🟢 {D.TEAMS[w['dog']][0]} (+{w['ml']:.0f}) beat the {D.TEAMS[w['fav']][0]} {w['score']}: +${w['ml']:,.0f}"
                    for w in top)
        + f"\n\n$100 on every underdog's moneyline in Week {wk} ({dogs} games): {money(net)} overall."
        + f"\n\nWhich underdog are you riding in Week {wk + 1}? 👇"
        + f"\n\n📤 Send this to the friend who bet the {D.TEAMS[w0['fav']][0]} 😅 📌 Save it for next week's card.")
    cap += (f"\n\nProfit on a $100 moneyline bet at closing odds, Week {wk} underdogs that won outright.\n"
            f"Data: nflverse, scores verified vs ESPN.\n{DISCLAIMER}\n#nfl #nflbetting #underdog #week{wk}")
    return _post(out_dir, key, "v2_upsets", lambda r, t: L.bars(
        "Which Underdog {hl} Most?", "Paid", f"$100 on the moneyline · Week {wk} upsets · profit shown", items,
        "nflverse closing lines", hl_color=GREEN, reveal=r, tease=t), cap, rep, countdown=len(items))


def sunday(ctx, out_dir, sizes=None, day=None):
    """Same-day 'Sunday in $': what $100 on every favorite / underdog / over / under paid on today's slate.
    Posted Sunday evening while people are still talking about the games. Final scores come straight from
    ESPN (nflverse can lag on game day) and must match nflverse wherever nflverse already has them;
    lines come from nflverse."""
    from datetime import datetime
    from zoneinfo import ZoneInfo
    day = day or datetime.now(ZoneInfo("America/Los_Angeles")).date()
    rep = C.Report("v2 sunday").extend(ctx.report)
    slate = [g for g in ctx.games if g["gameday"] == day.isoformat()]
    if len(slate) < 8:
        raise NoContent(f"No full NFL slate on {day}.")
    espn = {(e["away"], e["home"]): e for e in D.espn_scoreboard(day)}
    early = [g for g in slate if (g["gametime"] or "99") < "19:00"]          # everything before Sunday night (ET)
    games, missing = [], []
    for g in slate:
        e = espn.get((g["away_team"], g["home_team"]))
        rep.require(e is not None, f"{g['game_id']}: on ESPN scoreboard", "game missing from ESPN")
        if not e or not e["final"]:
            if g in early:
                missing.append(g["game_id"])
            continue
        if g["final"]:
            rep.require((g["away_score"], g["home_score"]) == (e["away_score"], e["home_score"]),
                        f"{g['game_id']}: ESPN and nflverse scores agree",
                        f"ESPN {e['away_score']}-{e['home_score']} vs nflverse {g['away_score']}-{g['home_score']}")
        if g["spread_line"] is None or g["total_line"] is None:
            rep.expect(False, f"{g['game_id']}: lines present", "no spread/total in nflverse; game left out")
            continue
        C.line_ranges(rep, "nfl", g["game_id"], g["spread_line"], g["total_line"],
                      moneylines=(g["home_moneyline"], g["away_moneyline"]))
        h, a = e["home_score"], e["away_score"]
        games.append(dict(g, home_score=h, away_score=a, result=h - a, total=h + a))
    if missing:
        raise DataError(f"Waiting on {len(missing)} afternoon game(s) to finish: {missing[:4]}")
    rep.require(len(games) >= 8, "enough final games for a Sunday recap", f"only {len(games)} games")
    wk = slate[0]["week"]
    angle = {k: 0.0 for k in ("Favorites", "Underdogs", "Home teams", "Road teams", "Overs", "Unders")}
    upsets = []
    for g in games:
        ho, ao = _odds(g.get("home_spread_odds")), _odds(g.get("away_spread_odds"))
        oo, uo = _odds(g.get("over_odds")), _odds(g.get("under_odds"))
        rh, ra = D.ats_side(g, g["home_team"]), D.ats_side(g, g["away_team"])
        angle["Home teams"] += _bet(rh, ho)
        angle["Road teams"] += _bet(ra, ao)
        if g["spread_line"]:
            fh = g["spread_line"] > 0
            angle["Favorites"] += _bet(rh if fh else ra, ho if fh else ao)
            angle["Underdogs"] += _bet(ra if fh else rh, ao if fh else ho)
        ou = D.ou_side(g)
        angle["Overs"] += _bet("W" if ou == "O" else ("L" if ou == "U" else "P"), oo)
        angle["Unders"] += _bet("W" if ou == "U" else ("L" if ou == "O" else "P"), uo)
        hml, aml = g["home_moneyline"], g["away_moneyline"]
        if hml and aml and max(hml, aml) >= 100:
            dog_home = hml > aml
            dog, fav, ml = (g["home_team"], g["away_team"], hml) if dog_home else (g["away_team"], g["home_team"], aml)
            ds, fs = (g["home_score"], g["away_score"]) if dog_home else (g["away_score"], g["home_score"])
            if ds > fs:
                upsets.append((ml, dog, fav, f"{ds}-{fs}"))
    for k, v in angle.items():
        rep.require(abs(v) <= len(games) * 260, f"{k} total plausible", f"{v:.0f} over {len(games)} games")
    icons = {"Favorites": "crown", "Underdogs": "dog", "Home teams": "home", "Road teams": "plane", "Overs": "up", "Unders": "down"}
    order = sorted(angle, key=lambda k: -angle[k])
    items = [{"label": k, "sub": "today", "value": abs(angle[k]), "icon": icons[k], "value_label": money(angle[k]),
              "color": GREEN if angle[k] >= 0 else RED} for k in order]
    key = f"{ctx.season}-wk{wk:02d}-v2-sunday"
    best, worst = order[0], order[-1]
    one = {"Favorites": "favorite", "Underdogs": "underdog", "Home teams": "home team", "Road teams": "road team",
           "Overs": "over", "Unders": "under"}
    lines = [f"Sunday in $ 💸 $100 on every {one[best]} today: {money(angle[best])}. "
             f"Every {one[worst]}: {money(angle[worst])}."]
    if upsets:
        ml, dog, fav, sc = max(upsets)
        lines.append(f"Biggest upset: the {D.TEAMS[dog][0]} (+{ml:.0f}) beat the {D.TEAMS[fav][0]} {sc}. "
                     f"$100 on them paid ${ml:,.0f} 🐶")
    lines.append("\n".join(f"{'🟢' if angle[k] >= 0 else '🔴'} Every {one[k]}: {money(angle[k])}" for k in order))
    lines.append("Which way did you go today? 👇")
    lines.append(f"📤 Send this to the friend who rode the {worst.lower()} today 😅")
    cap = "\n\n".join(lines)
    cap += (f"\n\n$100 per game at game-day lines, {len(games)} Sunday games, Week {wk}"
            f"{'' if len(games) == len(slate) else ' (Sunday night game not included)'}.\n"
            f"Data: final scores from ESPN, lines from nflverse.\n{DISCLAIMER}\n#nfl #nflbetting #sportsbetting #nflsunday")
    return _post(out_dir, key, "v2_sunday", lambda r, t: L.bars(
        "Who Got {hl} Today?", "Paid", f"$100 on every bet type · {len(games)} Sunday games · Week\u00a0{wk}", items,
        "ESPN scores · nflverse lines", hl_color=GREEN, reveal=r, tease=t), cap, rep, countdown=len(items))

BUILDERS = {"v2_best": best_bets, "v2_worst": worst_bets, "v2_angles": which_bet_pays, "v2_overs": over_teams,
            "v2_rb": touches, "v2_wr": targets, "v2_waiver": waiver,
            "v2_all32": all_teams, "v2_upsets": upsets,
            "v2_sunday": sunday}
