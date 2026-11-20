"""Selection Sunday and playoff game days (owner, Nov 20: "Selection Sunday, huge. We need multiple posts on Selection
Sunday"; "each playoff game day, a head-to-head card"; "cause debates, stir up comments").

  sel_field     Selection Sunday: the 12-team field on the total offense vs total defense scatter.
  sel_snub      Selection Sunday: the highest-ranked team left OUT vs the lowest-ranked team that got IN, head to head.
  sel_bracket   Selection Sunday evening: all four first-round games, each side's edge, upset alerts, the byes.
  cfp_game1..4  Each playoff game day: one head-to-head card per game (in kickoff order), before kickoff.

How the field is checked before anything posts:
  - ESPN's scoreboard lists the four first-round games (teams fill in when the bracket is announced; until then the
    jobs wait and retry) and the quarterfinal slots (the four bye teams).
  - The final CFP ranking must agree between ESPN and collegefootballplayoff.com (cfp.checked_ranking) and be newer
    than the conference title games.
  - The field must follow the published rules: every team ranked above the first team left out is in, and every team
    that got in ahead of it won a conference title game (ESPN) or is Notre Dame inside the top 12.
  - Seeds = the field in ranking order, confirmed only if ESPN's first-round pairings are exactly 5v12, 6v11, 7v10,
    8v9 and the byes are seeds 1-4. Otherwise seeds are left off and the bracket post blocks.
  - Every stat: NCAA.com's official tables, each team's games and points matched exactly against ESPN, yards within
    0.5% (box scores lag official stat corrections by a few yards).
"""
import glob
import json
import os
import re
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from . import cfp as X
from . import checks as C
from . import light as L
from .data import _get
from .logos import logo_uri
from .posts import DataError, NoContent, already_posted
from .v2 import _post

PT = ZoneInfo("America/Los_Angeles")
ET = ZoneInfo("America/New_York")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCORE = "https://site.api.espn.com/apis/site/v2/sports/football/college-football/scoreboard?dates={}&groups=80&limit=200"
CONF = re.compile(r"\b(ACC|Big Ten|Big 12|SEC|American|Conference USA|MAC|Mid-American|Mountain West|Pac-12|Sun Belt) "
                  r"Championship\b")
SOURCE = "NCAA.com · checked vs ESPN"
DATA = ("Data: final ranking from ESPN, checked against collegefootballplayoff.com; stats from NCAA.com's official FBS "
        "tables, every team's games, points and yards matched against ESPN.")
GREEN, RED, INK = "#16A34A", "#DC2626", "#1F2937"


class NotYet(DataError):
    """The bracket isn't out yet. A DataError, so the runner waits and retries, then skips quietly at the window's end."""


def th(k):
    return f"{k}{'th' if 10 <= k % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(k % 10, 'th')}"


def _season(day):
    return day.year if day.month >= 7 else day.year - 1


_EV = {}


def _events(day):
    k = day.strftime("%Y%m%d")
    if k not in _EV:
        _EV[k] = json.loads(_get(SCORE.format(k))).get("events", [])
    return _EV[k]


def _notes(e):
    return " ".join(n.get("headline", "") for n in e["competitions"][0].get("notes", []))


def _sides(e):
    return e["competitions"][0]["competitors"]


def _known(e):
    return all(not c["team"]["id"].startswith("-") and (c["team"].get("location") or "TBD") != "TBD" for c in _sides(e))


def _days(a, b):
    while a <= b:
        yield a
        a += timedelta(days=1)


def cfp_games(day, kind="College Football Playoff"):
    return [e for e in _events(day) if "College Football Playoff" in _notes(e) and kind in _notes(e)]


_TAB = {}


def _table(fn, stat):
    if (fn.__name__, stat) not in _TAB:
        _TAB[(fn.__name__, stat)] = fn(stat)
    return _TAB[(fn.__name__, stat)]


def profiles(teams, rep):
    """teams: [(id, name)] -> {id: stats}. Ranks and per-game numbers are NCAA.com's; games, record and points must
    match ESPN's game-by-game scores exactly, yards within 0.5% of ESPN's box scores."""
    off, dfn = _table(X._ncaa_yards, 21), _table(X._ncaa_yards, 22)
    so, sd = _table(X._ncaa_table, 27), _table(X._ncaa_table, 28)
    rep.require(len(off) >= 120 and len(off) == len(dfn) == len(so) == len(sd), "ncaa: four full FBS tables",
                f"{len(off)}/{len(dfn)}/{len(so)}/{len(sd)} rows")
    X._rank_check(rep, off, "total offense", lambda a, b: a > b)
    X._rank_check(rep, dfn, "total defense", lambda a, b: a < b)
    out = {}
    for tid, name in teams:
        k = X._ncaa_norm(name)
        if not rep.require(all(k in t for t in (off, dfn, so, sd)), f"ncaa: {name} found on NCAA.com", repr(k)):
            continue
        events, team = X._team_events(tid)
        g = w = l_ = pf = pa = yf = ya = 0
        last = None
        for e in events:
            c = e["competitions"][0]
            if not c["status"]["type"].get("completed"):
                continue
            us = next(x for x in c["competitors"] if x["team"]["id"] == str(tid))
            them = next(x for x in c["competitors"] if x["team"]["id"] != str(tid))
            a, b = int(us["score"]["value"]), int(them["score"]["value"])
            g, pf, pa, w, l_ = g + 1, pf + a, pa + b, w + (a > b), l_ + (a < b)
            tot = X.box_yards(e["id"])
            yf, ya = yf + tot.pop(str(tid)), ya + next(iter(tot.values()))
            last = max(last or e["date"], e["date"])
        o, d, (gs, ps), (ga, pas) = off[k], dfn[k], so[k], sd[k]
        rep.require(g == o["g"] == d["g"] == gs == ga and pf == ps and pa == pas and w + l_ == g,
                    f"{name}: games and points match (ESPN vs NCAA.com)",
                    f"ESPN {g} g {pf}-{pa}, NCAA.com {o['g']}/{d['g']}/{gs}/{ga} g {ps}-{pas}")
        diff = f"ESPN {yf} gained, {ya} allowed vs NCAA.com {o['yds']}, {d['yds']}"
        rep.require(abs(yf - o["yds"]) <= .005 * o["yds"] and abs(ya - d["yds"]) <= .005 * d["yds"],
                    f"{name}: yards agree within 0.5% (ESPN box scores vs NCAA.com)", diff)
        rep.expect(yf == o["yds"] and ya == d["yds"], f"{name}: yards match exactly", diff)
        if not g:
            continue
        out[tid] = {"name": name, "short": team.get("shortDisplayName") or name, "g": g, "w": w, "l": l_,
                    "record": f"{w}-{l_}", "orank": o["rank"], "drank": d["rank"], "oypg": o["yds"] / o["g"],
                    "dypg": d["yds"] / d["g"], "ppg": ps / gs, "papg": pas / ga, "logo": logo_uri(tid, "ncaa"),
                    "color": "#" + (team.get("color") or "3A4A6B"), "last": last}
    return out


# (label, value, higher is better, shown, small print). Compared at the precision shown, so a "tie" on screen is a tie.
CATS = [
    ("Record", lambda t: round(t["w"] / t["g"], 4), True, lambda t: t["record"], lambda t: ""),
    ("Total offense", lambda t: t["orank"], False, lambda t: th(t["orank"]), lambda t: f"{t['oypg']:.0f} yds/g"),
    ("Total defense", lambda t: t["drank"], False, lambda t: th(t["drank"]), lambda t: f"{t['dypg']:.0f} allowed"),
    ("Points per game", lambda t: round(t["ppg"], 1), True, lambda t: f"{t['ppg']:.1f}", lambda t: ""),
    ("Points allowed", lambda t: round(t["papg"], 1), False, lambda t: f"{t['papg']:.1f}", lambda t: ""),
]


def edge(a, b):
    """Card rows for a (left) vs b (right), and how many categories each side wins."""
    rows, wa, wb = [], 0, 0
    for label, val, high, shown, small in CATS:
        x, y = val(a), val(b)
        win = None if x == y else ("l" if (x > y) == high else "r")
        wa, wb = wa + (win == "l"), wb + (win == "r")
        rows.append({"label": label, "l": shown(a), "r": shown(b), "lsub": small(a), "rsub": small(b), "win": win})
    return rows, wa, wb


def edge_text(a, b):
    """'Total offense: Oregon 3rd, James Madison 45th' lines for captions."""
    rows, _, _ = edge(a, b)
    return "\n".join(f"• {r['label']}: {a['short']} {r['l']}, {b['short']} {r['r']}" for r in rows)


def playoff_field(rep, today):
    y = _season(today)
    fr = [e for d in _days(date(y, 12, 10), date(y, 12, 26)) for e in cfp_games(d, "First Round")]
    if not rep.require(len(fr) == 4, "espn: four first-round games listed", f"{len(fr)} found"):
        raise DataError("ESPN doesn't list four first-round games.")
    if not all(_known(e) for e in fr):
        raise NotYet("The bracket isn't out yet (ESPN's first-round games are still TBD).")
    titles, last_title = {}, None
    for d in _days(date(y, 11, 27), date(y, 12, 9)):
        for e in _events(d):
            m = CONF.search(_notes(e))
            if m and e["competitions"][0]["status"]["type"].get("completed"):
                win = next((c["team"]["id"] for c in _sides(e) if c.get("winner")), None)
                if win:
                    titles[win] = m.group(1).replace("Mid-American", "MAC")
                    last_title = max(last_title or e["date"][:10], e["date"][:10])
    released, rows = X.checked_ranking(rep, today)
    if not last_title or released < date.fromisoformat(last_title):
        raise NotYet(f"The final ranking isn't out yet (latest is {released}, title games ended {last_title}).")
    rank = {r["id"]: r for r in rows}
    names = {c["team"]["id"]: c["team"].get("location") or c["team"]["name"] for e in fr for c in _sides(e)}
    names.update({r["id"]: r["name"] for r in rows})
    pairs = [tuple(c["team"]["id"] for c in _sides(e)) for e in sorted(fr, key=lambda e: e["date"])]
    in8 = {t for p in pairs for t in p}
    rep.require(len(in8) == 8, "espn: eight different first-round teams", f"{len(in8)}")
    qf = [e for d in _days(date(y, 12, 26), date(y + 1, 1, 4)) for e in cfp_games(d, "Quarterfinal")]
    qf_known = {c["team"]["id"] for e in qf for c in _sides(e) if not c["team"]["id"].startswith("-")} - in8
    top4 = [r["id"] for r in rows[:4]]
    if len(qf_known) == 4:
        byes = sorted(qf_known, key=lambda i: rank[i]["rank"] if i in rank else 99)
        for i in byes:
            names.setdefault(i, i)
    else:
        byes = top4
        rep.require(not set(byes) & in8, "bracket: the top 4 aren't playing in the first round", "a top-4 team is")
        rep.expect(False, "espn: quarterfinal slots not filled in yet", "byes taken as the top 4 of the final ranking")
    field = sorted(set(byes) | in8, key=lambda i: (rank[i]["rank"] if i in rank else 99))
    rep.require(len(field) == 12, "bracket: 12 teams in the field", f"{len(field)}")
    seeds = {i: k + 1 for k, i in enumerate(field)}
    want = {frozenset((field[4 + j], field[11 - j])) for j in range(4)}
    seeds_ok = {frozenset(p) for p in pairs} == want and set(field[:4]) == set(byes)
    rep.expect(seeds_ok, "bracket: seeds follow the ranking (byes 1-4; 5v12, 6v11, 7v10, 8v9)",
               "pairings differ from straight seeding: seeds left off")
    first_out = next(r for r in rows if r["id"] not in field)
    benef = [i for i in field if i not in rank or rank[i]["rank"] > first_out["rank"]]
    for i in benef:
        nd = X._norm(names[i]) == "notre dame" and i in rank and rank[i]["rank"] <= 12
        rep.require(i in titles or nd, f"rules: {names[i]} got in ahead of #{first_out['rank']} {first_out['name']} "
                    "as a conference champion", "not a conference title game winner per ESPN")
    if not rep.ok:
        raise DataError("The playoff field doesn't add up; see checks.")
    return {"season": y, "released": released.isoformat(), "field": field, "byes": byes, "pairs": pairs,
            "seeds": seeds if seeds_ok else None, "names": {i: names[i] for i in field + [first_out["id"]]},
            "rank": {i: (rank[i]["rank"] if i in rank else None) for i in field},
            "records": {r["id"]: r["record"] for r in rows}, "titles": titles, "first_out": first_out, "benef": benef}


def _save(out_dir, F):
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "field.json"), "w") as fh:
        json.dump(F, fh, indent=1, default=str)


def saved_field(season):
    """The field saved by the latest Selection Sunday post (media/<date>_sel_field/field.json), or None."""
    for path in sorted(glob.glob(os.path.join(ROOT, "media", "*_sel_*", "field.json")), reverse=True):
        F = json.load(open(path))
        if F.get("season") == season:
            return F
    return None


def _today():
    return datetime.now(PT).date()


def _thru(P):
    last = max(t["last"] for t in P.values())
    d = datetime.fromisoformat(last.replace("Z", "+00:00")).astimezone(ET).date()
    return f"{d:%b} {d.day}"


def sel_field(out_dir):
    rep = C.Report("selection field")
    today = _today()
    key = f"cfp-sel-field-{_season(today)}"
    already_posted(key)
    F = playoff_field(rep, today)
    _save(out_dir, F)
    seeds = F["seeds"]
    rows = [{"id": i, "name": F["names"][i], "rank": seeds[i] if seeds else k + 1} for k, i in enumerate(F["field"])]
    label = (lambda r: f"{r['rank']}-seed {r['name']}") if seeds else (lambda r: r["name"])
    rel = date.fromisoformat(F["released"])
    return X.top25_yards_scatter(out_dir, rows, rel, "The 12-team College Football Playoff field, selected", rep,
                                 group="12 playoff teams", key=key, reel_name="sel_field", label=label,
                                 tags_extra=" #selectionsunday")


def sel_snub(out_dir):
    rep = C.Report("selection snub")
    today = _today()
    key = f"cfp-sel-snub-{_season(today)}"
    already_posted(key)
    F = playoff_field(rep, today)
    _save(out_dir, F)
    fo = F["first_out"]
    pool = F["benef"] or F["field"]
    inn = max(pool, key=lambda i: F["rank"][i] or 99)
    P = profiles([(inn, F["names"][inn]), (fo["id"], fo["name"])], rep)
    if not rep.ok or len(P) != 2:
        raise DataError("Snub card: stats don't check out; see checks.")
    a, b = P[inn], P[fo["id"]]
    rows, wa, wb = edge(a, b)
    rin = F["rank"][inn]
    rin_txt = f"#{rin}" if rin else "Unranked"
    how = f"the {F['titles'][inn]} champion" if inn in F["titles"] else "an at-large pick"
    if wb > wa:
        tally, verdict = f"{b['short']} wins {wb} of 5 😬", f"On paper, {b['short']} wins {wb} of 5 categories."
    elif wa > wb:
        tally, verdict = f"{a['short']} wins {wa} of 5", f"On paper, {a['short']} still wins {wa} of 5 categories."
    else:
        tally, verdict = f"Dead even: {wa}-{wb}", f"On paper it's dead even, {wa}-{wb}."
    others = [i for i in F["benef"] if i != inn]
    also = ("\n\nAlso in ahead of them: " + ", ".join(
        f"{F['names'][i]} ({'#' + str(F['rank'][i]) if F['rank'][i] else 'unranked'}, {F['titles'].get(i, 'at-large')}"
        f"{' champ' if i in F['titles'] else ''})" for i in others)) if others else ""
    cap = (f"#{fo['rank']} {fo['name']} ({b['record']}) is OUT of the College Football Playoff. {F['names'][inn]} "
           f"({a['record']}, {rin_txt}) is IN as {how}. 😳{also}\n\nHead to head:\n{edge_text(a, b)}\n\n{verdict}\n\n"
           f"Did the committee get it right, or did {b['short']} get robbed? 👇\n\n📤 Send this to a {b['short']} fan."
           f"\n\nFinal College Football Playoff ranking ({date.fromisoformat(F['released']):%b %-d}). National ranks "
           f"among all FBS teams; per-game stats through {_thru(P)}.\n{DATA}\n{X.TAGS} #selectionsunday")
    C.caption(rep, cap)
    left = {"logo": a["logo"], "name": a["short"], "sub": f"CFP {rin_txt} · {a['record']}", "tag": "IN",
            "tag_bg": GREEN, "tag_fg": "#fff"}
    right = {"logo": b["logo"], "name": b["short"], "sub": f"CFP #{fo['rank']} · {b['record']}", "tag": "OUT",
             "tag_bg": RED, "tag_fg": "#fff"}
    title = "{hl} Is OUT.\n" + f"{'#' + str(rin) + ' ' if rin else ''}{a['short']} Is IN."
    return _post(out_dir, key, "sel_snub", lambda p: L.h2h(
        title, f"#{fo['rank']} {b['short']}", f"{a['short']} got in as {how}. Who deserved it?", left, right, rows,
        tally, SOURCE, p=p, hl_color=RED, tally_bg=RED if wb > wa else INK), cap, rep, hold=6.0)


def _game_side(P, i, seed):
    t = P[i]
    return {"seed": seed, "logo": t["logo"], "name": t["short"], "line": f"Off {th(t['orank'])} · Def {th(t['drank'])}"}


def sel_bracket(out_dir):
    rep = C.Report("selection bracket")
    today = _today()
    key = f"cfp-sel-bracket-{_season(today)}"
    already_posted(key)
    F = playoff_field(rep, today)
    _save(out_dir, F)
    S = F["seeds"]
    if not rep.require(S is not None, "bracket: seeds confirmed by ESPN's pairings", "seeds unconfirmed"):
        raise DataError("Seeds unconfirmed; no bracket card.")
    P = profiles([(i, F["names"][i]) for i in F["field"]], rep)
    if not rep.ok or len(P) != 12:
        raise DataError("Bracket card: stats don't check out; see checks.")
    games, lines, ups = [], [], 0
    for pair in sorted(F["pairs"], key=lambda p: min(S[i] for i in p)):
        hi, lo = sorted(pair, key=lambda i: S[i])
        _, wh, wl = edge(P[hi], P[lo])
        if wl > wh:
            ups += 1
            tag, bg, fg = f"UPSET ALERT: {P[lo]['short']} wins {wl} of 5", RED, "#fff"
        elif wh > wl:
            tag, bg, fg = f"{P[hi]['short']} wins {wh} of 5", "#F3F4F6", INK
        else:
            tag, bg, fg = f"DEAD EVEN {wh}-{wl}", "#FDE047", INK
        games.append({"l": _game_side(P, hi, S[hi]), "r": _game_side(P, lo, S[lo]), "tag": tag, "tag_bg": bg, "tag_fg": fg})
        lines.append(f"({S[hi]}) {P[hi]['short']} vs ({S[lo]}) {P[lo]['short']}: "
                     + (f"🚨 UPSET ALERT, {P[lo]['short']} wins {wl} of 5" if wl > wh else
                        f"{P[hi]['short']} wins {wh} of 5" if wh > wl else f"dead even, {wh}-{wl}"))
    byes = [{"seed": S[i], "logo": P[i]["logo"], "name": P[i]["short"]} for i in F["field"][:4]]
    if ups:
        title, hl = ("{hl} First-Round\nUpset Alerts" if ups > 1 else "{hl} First-Round\nUpset Alert"), str(ups)
    else:
        title, hl = "Higher Seeds Win\nthe Numbers in {hl}", "All 4"
    cap = (f"{'🚨 ' + str(ups) + ' first-round upset alert' + ('s' if ups > 1 else '') if ups else 'No upset alerts'}: "
           "here's every College Football Playoff first-round game on paper.\n\n" + "\n".join(lines)
           + "\n\nByes: " + ", ".join(f"({S[i]}) {P[i]['short']}" for i in F["field"][:4])
           + "\n\nWhich lower seed pulls it off? Drop your upset pick 👇\n\n📤 Send this to the group chat."
           "\n\n5 categories: record, total offense rank, total defense rank, points per game, points allowed. "
           f"Upset alert = the lower seed wins more of them. Stats through {_thru(P)}.\n{DATA}\n{X.TAGS} #selectionsunday")
    C.caption(rep, cap)
    return _post(out_dir, key, "sel_bracket", lambda p: L.matchups(
        title, hl, "Each first-round game on paper: record, total offense and defense, points for and against",
        games, byes, SOURCE, p=p, hl_color=RED if ups else GREEN), cap, rep, hold=7.0)


def _round(e):
    n = _notes(e)
    m = re.search(r"College Football Playoff (.*?)(?: Presented by.*| Game)?$", n)
    r = (m.group(1) if m else "Playoff").strip()
    return re.sub(r"^(Quarterfinal|Semifinal) at the ", r"\1, ", r)


def cfp_gameday(out_dir, idx=0, today=None):
    """Head-to-head card for today's idx-th playoff game (kickoff order), posted before kickoff."""
    rep = C.Report(f"cfp game {idx + 1}")
    today = today or _today()
    games = sorted((e for e in cfp_games(today) if _known(e)), key=lambda e: e["date"])
    if idx >= len(games):
        raise NoContent(f"No playoff game #{idx + 1} today.")
    e = games[idx]
    key = f"cfp-game-{e['id']}"
    already_posted(key)
    if e["competitions"][0]["status"]["type"].get("state") != "pre":
        raise NoContent("That game has already started.")
    side = {c["team"]["id"]: c for c in _sides(e)}
    F = saved_field(_season(today)) or {}
    seeds = F.get("seeds") or {}
    order = sorted(side, key=lambda i: seeds.get(i, 99))
    P = profiles([(i, side[i]["team"].get("location") or side[i]["team"]["name"]) for i in order], rep)
    if not rep.ok or len(P) != 2:
        raise DataError("Game card: stats don't check out; see checks.")
    hi, lo = order
    a, b = P[hi], P[lo]
    rows, wa, wb = edge(a, b)
    kick = datetime.fromisoformat(e["date"].replace("Z", "+00:00")).astimezone(ET)
    when = f"{kick:%-I:%M %p} ET".replace(":00 ", " ")
    tv = ", ".join(n for b_ in e["competitions"][0].get("broadcasts", []) for n in b_.get("names", []))
    rnd = _round(e)
    sd = lambda i: f"({seeds[i]}) " if i in seeds else ""
    if wb > wa:
        title, hl, col = "Upset Alert?\n{hl} Wins " + f"{wb} of 5", b["short"], RED
        tally, verdict = f"Edge: {b['short']} {wb}-{wa}", f"The lower seed, {b['short']}, wins {wb} of 5 categories."
    elif wa > wb:
        title, hl, col = "{hl} Has the Edge\n" + f"in {wa} of 5", a["short"], GREEN
        tally, verdict = f"Edge: {a['short']} {wa}-{wb}", f"{a['short']} wins {wa} of 5 categories."
    else:
        title, hl, col = "Dead Even:\n{hl}", f"{wa}-{wb}", "#CA8A04"
        tally, verdict = f"Dead even {wa}-{wb}", f"Dead even: {wa}-{wb}."
    left = {"logo": a["logo"], "name": a["short"], "sub": a["record"], "tag": f"{seeds[hi]} SEED" if hi in seeds else ""}
    right = {"logo": b["logo"], "name": b["short"], "sub": b["record"], "tag": f"{seeds[lo]} SEED" if lo in seeds else ""}
    cap = (f"{sd(hi)}{a['short']} vs {sd(lo)}{b['short']}, College Football Playoff {rnd}. Kickoff {when}"
           f"{' on ' + tv if tv else ''}. 🏈\n\nOn paper:\n{edge_text(a, b)}\n\n{verdict}\n\n"
           "Who wins, and what's the score? Drop your prediction 👇\n\n📤 Send this to a fan of either team."
           f"\n\nStats through {_thru(P)}.\nData: NCAA.com's official FBS tables, both teams' games, points and yards "
           f"matched against ESPN.\n{X.TAGS}")
    C.caption(rep, cap)
    return _post(out_dir, key, f"cfp_game{idx + 1}", lambda p: L.h2h(
        title, hl, f"Playoff {rnd} · {when}", left, right, rows, tally, SOURCE, p=p, hl_color=col,
        tally_bg=RED if wb > wa else INK), cap, rep, hold=6.0)


X.BUILDERS.update({"sel_field": sel_field, "sel_snub": sel_snub, "sel_bracket": sel_bracket})
for _k in range(4):
    X.BUILDERS[f"cfp_game{_k + 1}"] = (lambda k: lambda out_dir: cfp_gameday(out_dir, k))(_k)
