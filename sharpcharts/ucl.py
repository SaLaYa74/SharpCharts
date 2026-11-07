"""UEFA Champions League, big clubs only (owner, Nov 6: "Real Madrid, Man City, Barcelona, Bayern, Chelsea, PSG...").

Two independent sources must agree before anything posts: ESPN's soccer feeds and UEFA's own stats feeds (the
ones uefa.com runs on). Table: every giant's position, points and W-D-L must match UEFA's table, and all 36
clubs must have played the same number of games (a matchday still in progress never posts). Scorers: every
player's goals and games must match between ESPN's leaders and UEFA's player ranking.

Zones (top 8 / playoffs / danger) are where clubs would finish if the league phase ended today. The zone rules
come from ESPN's own table notes and are checked every run; captions always say "if it ended today".
"""
import json
import re
import unicodedata

from . import checks as C
from . import light as L
from .data import _get
from .logos import logo_uri
from .posts import DataError, NoContent, already_posted
from .v2 import COOL, _post

ESPN_TABLE = "https://site.api.espn.com/apis/v2/sports/soccer/uefa.champions/standings"
ESPN_STATS = "https://site.api.espn.com/apis/site/v2/sports/soccer/uefa.champions/statistics"
UEFA_TABLE = "https://standings.uefa.com/v1/standings?competitionId=1&seasonYear={}"
UEFA_GOALS = ("https://compstats.uefa.com/v1/player-ranking?competitionId=1&limit=100&offset=0&optionalFields=PLAYER%2CTEAM"
              "&order=DESC&phase=TOURNAMENT&seasonYear={}&stats=goals%2Cmatches_appearance%2Cminutes_played_official")
# The giants, most famous first: (how we write it, ESPN team id, UEFA's international name). Up to MAX_SHOWN of
# them appear, picked by fame, then ordered by table position.
GIANTS = [("Real Madrid", "86", "Real Madrid"), ("Barcelona", "83", "Barcelona"), ("Man City", "382", "Man City"),
          ("Bayern", "132", "Bayern München"), ("PSG", "160", "Paris"), ("Liverpool", "364", "Liverpool"),
          ("Chelsea", "363", "Chelsea"), ("Man United", "360", "Man Utd"), ("Arsenal", "359", "Arsenal"),
          ("Inter", "110", "Inter"), ("Juventus", "111", "Juventus"), ("Atlético", "1068", "Atleti"),
          ("AC Milan", "103", "Milan"), ("Dortmund", "124", "B. Dortmund"), ("Napoli", "114", "Napoli"),
          ("Tottenham", "367", "Tottenham")]
MAX_SHOWN = 10
TAGS = "#championsleague #ucl #football #soccer"
ZONE = {"top": ("TOP 8", "#DCFCE7", "#166534"), "playoff": ("PLAYOFFS", "#DBEAFE", "#1E40AF"),
        "danger": ("DANGER", "#FEE2E2", "#B91C1C"), "perfect": ("PERFECT", "#FDE047", "#1F2937")}


def _plain(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z ]", "", s).strip()


def _season(d):
    return int(d["season"]["year"]) + 1              # ESPN's 2026 season = UEFA's seasonYear 2027 (2026-27)


def _zone(rank):
    return "top" if rank <= 8 else ("playoff" if rank <= 24 else "danger")


def checked_table(rep):
    """({espn_id: row}, matchday, season) with every giant matched against UEFA's table."""
    d = json.loads(_get(ESPN_TABLE))
    season = _season(d)
    rows = {}
    for e in d["children"][0]["standings"]["entries"]:
        st = {s["name"]: s.get("value") for s in e["stats"]}
        rows[e["team"]["id"]] = {"rank": int(st["rank"]), "pts": int(st["points"]), "w": int(st["wins"]),
                                 "d": int(st["ties"]), "l": int(st["losses"]), "gp": int(st["gamesPlayed"]),
                                 "note": (e.get("note") or {}).get("description", ""), "name": e["team"]["displayName"]}
    u = {it["team"]["internationalName"]: it for it in json.loads(_get(UEFA_TABLE.format(season)))[0]["items"]}
    rep.require(len(rows) == 36 and len(u) == 36, "ucl: 36 clubs in both tables", f"ESPN {len(rows)}, UEFA {len(u)}")
    gps = {r["gp"] for r in rows.values()}
    if len(gps) != 1:
        raise DataError(f"Champions League matchday still in progress (games played: {sorted(gps)}).")
    md = gps.pop()
    if md == 0:
        raise NoContent("Champions League league phase hasn't started.")
    rep.require(sorted(r["rank"] for r in rows.values()) == list(range(1, 37)), "ucl: ranks 1-36", "ranks missing")
    rep.require(sum(r["pts"] for r in rows.values()) == sum(3 * r["w"] + r["d"] for r in rows.values()),
                "ucl: points = 3 per win + 1 per draw", "points don't add up")
    for r in rows.values():
        note = r["note"].lower()
        want = {"top": "round of 16", "playoff": "playoff", "danger": "eliminated"}[_zone(r["rank"])]
        rep.require(want in note, f"ucl: #{r['rank']} zone note says '{want}'", f"ESPN note '{r['note']}'")
    for name, eid, uname in GIANTS:
        if eid not in rows:
            continue
        r, it = rows[eid], u.get(uname)
        ok = it is not None and (it["rank"], it["points"], it["won"], it["drawn"], it["lost"], it["played"]) == \
            (r["rank"], r["pts"], r["w"], r["d"], r["l"], r["gp"])
        rep.require(ok, f"ucl: {name} matches UEFA's table",
                    f"ESPN #{r['rank']} {r['pts']} pts vs UEFA {it and (it['rank'], it['points'])}")
    if not rep.ok:
        raise DataError("Champions League: ESPN and UEFA tables disagree; see checks.")
    return rows, md, season


def ucl_giants(out_dir):
    rep = C.Report("ucl giants table")
    rows, md, season = checked_table(rep)
    present = [(n, eid) for n, eid, _ in GIANTS if eid in rows][:MAX_SHOWN]
    shown = sorted(present, key=lambda ne: rows[ne[1]]["rank"])
    if len(shown) < 5:
        raise NoContent("Fewer than 5 giants in this season's Champions League.")
    perfect = [n for n, eid in shown if rows[eid]["d"] == rows[eid]["l"] == 0]
    danger = [(n, eid) for n, eid in shown if rows[eid]["rank"] >= 25]
    lad = []
    for n, eid in shown:
        r = rows[eid]
        z = ZONE["perfect" if n in perfect else _zone(r["rank"])]
        lad.append({"rank": r["rank"], "logo": logo_uri(eid, "soccer"), "name": n, "record": f"{r['pts']} pts",
                    "tag": z[0], "tag_bg": z[1], "tag_fg": z[2]})
    worst_n, worst_id = max(shown, key=lambda ne: rows[ne[1]]["rank"])
    if danger:
        title, hl = "{hl} Would Be Out Today", worst_n
        lead = f"If the Champions League league phase ended today, {worst_n} would be OUT 😳 ({rows[worst_id]['rank']}th of 36)."
    elif len(perfect) > 1:
        title, hl = "Only {hl} Giants Are Still Perfect", str(len(perfect))
        lead = f"Only {len(perfect)} of Europe's giants are still perfect in the Champions League: {' and '.join(perfect)} 🔥"
    elif perfect:
        title, hl = "{hl} Is the Only Perfect Giant", perfect[0]
        lead = f"{perfect[0]} is the only one of Europe's giants still perfect in the Champions League 🔥"
    else:
        title, hl = "Where the {hl} Stand", "Giants"
        lead = f"Where Europe's biggest clubs stand in the Champions League after Matchday {md} 👇"

    def line(n, eid):
        r = rows[eid]
        where = {"top": "top 8", "playoff": "playoff spot", "danger": "OUT"}[_zone(r["rank"])]
        return f"{r['rank']}. {n}: {r['pts']} pts ({r['w']}W {r['d']}D {r['l']}L), {where}"

    cap = (f"{lead}\n\nThe big clubs after Matchday {md} (position out of 36):\n"
           + "\n".join(line(n, eid) for n, eid in shown)
           + "\n\nTop 8 go straight to the round of 16, 9th-24th go to the playoffs, 25th-36th go home. "
           "That's where they'd land if the league phase ended today."
           + "\n\nWho's in trouble? 👇"
           + f"\n\n📤 Send this to the {worst_n} fan in your group chat."
           + "\n\nData: ESPN, every position, point and result matched against UEFA's official table."
           + f"\n{TAGS}")
    C.caption(rep, cap)
    key = f"ucl-giants-{season}-md{md}"
    already_posted(key)
    return _post(out_dir, key, "ucl_giants", lambda r, t: L.ladder(
        title, hl, f"Champions League · biggest clubs · after Matchday {md}", lad,
        "ESPN · checked vs UEFA's table", hl_color="#2563EB", reveal=r, tease=t), cap, rep, countdown=len(lad))


def ucl_scorers(out_dir):
    rep = C.Report("ucl scorers")
    rows, md, season = checked_table(rep)
    giants = {uname: (n, eid) for n, eid, uname in GIANTS}
    uefa = []
    for r in json.loads(_get(UEFA_GOALS.format(season))):
        s = {x["name"]: int(float(x["value"])) for x in r["statistics"]}
        uefa.append({"name": r["player"]["internationalName"], "team": r["team"]["internationalName"], **s})
    espn = {}
    for l in json.loads(_get(ESPN_STATS))["stats"][0]["leaders"]:
        m = re.search(r"Matches: (\d+), Goals: (\d+)", l.get("displayValue", ""))
        a = l["athlete"]
        if m:
            espn[_plain(a["displayName"])] = {"team": str((a.get("team") or {}).get("id", "")),
                                              "gp": int(m.group(1)), "goals": int(m.group(2))}
    lead = max(uefa, key=lambda p: (p["goals"], -p["matches_appearance"]))
    ranked = sorted((p for p in uefa if p["team"] in giants and p["goals"] > 0),
                    key=lambda p: (-p["goals"], p["matches_appearance"], p["minutes_played_official"]))
    # top 5, plus anyone level with #5 on goals and games (a tie shouldn't cut Kane for Guirassy); 6 rows max
    cut = ranked[4:5]
    stars = (ranked[:5] + [p for p in ranked[5:] if cut and (p["goals"], p["matches_appearance"]) ==
                           (cut[0]["goals"], cut[0]["matches_appearance"])])[:6]
    if len(stars) < 3:
        raise NoContent("Not enough goals from the giants yet.")
    for p in [lead] + stars:
        e = espn.get(_plain(p["name"]))
        rep.require(e is not None and (e["goals"], e["gp"]) == (p["goals"], p["matches_appearance"]),
                    f"ucl: {p['name']} goals and games match ESPN",
                    f"UEFA {p['goals']} in {p['matches_appearance']} vs ESPN {e and (e['goals'], e['gp'])}")
        rep.require(0 < p["minutes_played_official"] <= 120 * p["matches_appearance"],
                    f"ucl: {p['name']} minutes plausible", f"{p['minutes_played_official']} min in {p['matches_appearance']}")
    for p in stars:
        rep.require(espn[_plain(p["name"])]["team"] == giants[p["team"]][1], f"ucl: {p['name']} club matches ESPN",
                    f"{p['team']} vs ESPN team {espn[_plain(p['name'])]['team']}")
    if not rep.ok:
        raise DataError("Champions League scorers: ESPN and UEFA disagree; see checks.")
    top = stars[0]
    mpg = round(top["minutes_played_official"] / top["goals"])
    short = lambda n: n.split()[-1]
    items = [{"label": short(p["name"]), "sub": giants[p["team"]][0],
              "value": p["goals"], "value_label": str(p["goals"]), "icon": logo_uri(giants[p["team"]][1], "soccer"),
              "color": COOL[i % len(COOL)]} for i, p in enumerate(stars)]
    g = top["matches_appearance"]
    cap = (f"{top['name']} has {top['goals']} Champions League goals in {g} game{'s' * (g != 1)}. "
           f"That's a goal every {mpg} minutes 🤯\n\nTop scorers at Europe's biggest clubs after Matchday {md}:\n"
           + "\n".join(f"{i + 1}. {p['name']} ({giants[p['team']][0]}): {p['goals']} goals in {p['matches_appearance']} games"
                       for i, p in enumerate(stars))
           + (f"\n\nThe overall leader isn't at a giant: {lead['name']} ({lead['team']}) has {lead['goals']}."
              if lead["team"] not in giants else "")
           + "\n\nWho finishes as top scorer? 👇"
           + f"\n\n📤 Send this to a {giants[top['team']][0]} fan."
           + "\n\nData: UEFA's official player stats, goals and games matched against ESPN."
           + f"\n{TAGS}")
    C.caption(rep, cap)
    key = f"ucl-scorers-{season}-md{md}"
    already_posted(key)
    return _post(out_dir, key, "ucl_scorers", lambda r, t: L.hbars(
        "{hl} Goals in " + f"{g} Game{'s' * (g != 1)}. Who?", str(top["goals"]),
        f"Champions League goals · biggest clubs · after Matchday {md}", items, "UEFA · checked vs ESPN",
        hl_color="#2563EB", reveal=r, tease=t), cap, rep, countdown=len(items))


BUILDERS = {"ucl_giants": ucl_giants, "ucl_scorers": ucl_scorers}
