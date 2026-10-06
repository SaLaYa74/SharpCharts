#!/usr/bin/env python3
"""SharpCharts post generator.

    python3 generate.py                 # current season, latest data, feed + story PNGs
    python3 generate.py --season 2026 --next-week 5
    python3 generate.py --skip-verify   # NOT recommended: skips the ESPN score cross-check

Output: out/<date>/*.png plus captions.md with ready-to-paste captions.
"""
import argparse
import os
import sys
from datetime import date

from sharpcharts import data as D
from sharpcharts import templates as T
from sharpcharts.render import html_to_png

SRC = "nflverse (scores + lines) · ESPN (verified)"


def rec(w, l, p=0):
    return f"{w}-{l}" + (f"-{p}" if p else "")


def spread_text(g, home_abbr, away_abbr, line):
    if line is None:
        return "—"
    if line == 0:
        return "PK"
    return f"{home_abbr} -{abs(line):g}" if line > 0 else f"{away_abbr} -{abs(line):g}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--season", type=int, default=2026)
    ap.add_argument("--next-week", type=int, help="week to build matchup cards for (default: first unplayed week)")
    ap.add_argument("--skip-verify", action="store_true")
    ap.add_argument("--sizes", default="feed,story")
    args = ap.parse_args()
    sizes = args.sizes.split(",")

    games = D.load_games(args.season)
    finals = [g for g in games if g["final"]]
    if not finals:
        sys.exit("No completed games yet.")

    # ---- verification gate ----
    if not args.skip_verify:
        n, problems = D.verify_scores(games)
        if problems:
            print("VERIFICATION FAILED — nothing exported:\n  " + "\n  ".join(problems))
            sys.exit(1)
        print(f"✔ Verified {n} final scores against ESPN")

    last_wk = D.last_final_week(games)
    complete = D.week_complete(games, last_wk)
    pending = [f"{g['away_team']}-{g['home_team']}" for g in games if g["week"] == last_wk and not g["final"]]
    thru = f"Thru Wk {last_wk}"
    thru_note = (f"Through Week {last_wk} · {len(finals)} games" if complete else
                 f"Through Week {last_wk} Sunday · {', '.join(pending)} pending")

    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", date.today().isoformat())
    os.makedirs(out, exist_ok=True)
    captions = []

    def emit(name, html_fn, caption):
        for s in sizes:
            html_to_png(html_fn(s), os.path.join(out, f"{name}_{s}.png"), s)
        captions.append((name, caption))
        print("  ✔", name)

    # ---- brand assets ----
    html_to_png(T.profile_pic(), os.path.join(out, "profile_pic.png"), "square")
    html_to_png(T.wordmark(), os.path.join(out, "logo_wordmark.png"), "square")
    emit("00_welcome", lambda s: T.intro_post(s),
         "Welcome to SharpCharts 📊\n\nVerified betting data & trends: ATS records, over/under splits, "
         "line context and matchup breakdowns. Numbers first, always cross-checked before we post.\n\n"
         "Follow + turn on notifications for weekly NFL charts.\n\n21+ | Gamble responsibly. 1-800-GAMBLER\n"
         "#sportsbetting #nfl #nflbetting #bettingtips #sportsdata #ats")

    recs = D.team_records(finals)

    # ---- 1. ATS best & worst ----
    def ats_row(t):
        r = recs[t]
        return {"abbr": t, "color": D.TEAMS[t][1], "name": D.TEAMS[t][0],
                "value": r["cover_margin_sum"] / r["games"],
                "value_label": f"{r['cover_margin_sum']/r['games']:+.1f}",
                "record": f"{rec(r['ats_W'], r['ats_L'], r['ats_P'])} ATS · {rec(r['su_W'], r['su_L'], r['su_T'])} SU",
                "pct": r["ats_W"] / max(1, r["ats_W"] + r["ats_L"])}
    ranked = sorted((ats_row(t) for t in recs), key=lambda x: (x["pct"], x["value"]), reverse=True)
    top, bottom = ranked[:6], ranked[-6:]
    leaders = top + bottom
    emit("01_ats_best_worst", lambda s: T.bar_ranking(
        'Best &amp; worst<br><em>against the spread</em>',
        "Avg. cover margin per game (points beyond the closing spread)",
        leaders, tag=f"NFL · {thru}", source=SRC, size=s, note=thru_note),
        f"Who's cashing tickets and who's burning them 🔥🧊\n\n"
        "Top ATS: " + ", ".join(x["name"] + " (" + x["record"].split(" ATS")[0] + ")" for x in top[:3]) + "\n"
        "Bottom ATS: " + ", ".join(x["name"] + " (" + x["record"].split(" ATS")[0] + ")" for x in bottom[-3:]) + "\n\n"
        f"Bar = average points a team beat (or missed) the closing spread by. {thru_note}.\n\n"
        "Small samples early in the season, so use as context, not gospel.\n\n21+ | Gamble responsibly\n"
        "#nflbetting #ats #sportsbetting #nfl #bettingdata")

    # ---- 2. League-wide splits ----
    sp = D.league_splits(finals)
    items = [
        {"label": "Favorites vs underdogs (ATS)", "left": ("Favs", sp["fav_W"]), "right": ("Dogs", sp["fav_L"])},
        {"label": "Home vs away (ATS)", "left": ("Home", sp["home_W"]), "right": ("Away", sp["home_L"])},
        {"label": "Totals", "left": ("Over", sp["ou_O"]), "right": ("Under", sp["ou_U"])},
        {"label": "Underdogs winning outright", "left": ("Dog wins", sp["dog_outright_W"]), "right": ("Fav wins", sp["dog_outright_L"])},
    ]
    emit("02_league_splits", lambda s: T.splits(
        f'{args.season} NFL<br><em>betting splits</em>', "How the league is landing against the number",
        items, tag=f"NFL · {thru}", source=SRC, size=s,
        note=f"{thru_note} · pushes excluded"),
        f"The {args.season} NFL season by the numbers 📊\n\n"
        f"Favorites ATS: {sp['fav_W']}-{sp['fav_L']}\nHome ATS: {sp['home_W']}-{sp['home_L']}\n"
        f"Overs: {sp['ou_O']}-{sp['ou_U']}\nDogs outright: {sp['dog_outright_W']} wins\n\n"
        f"{thru_note}. Pushes excluded.\n\n21+ | Gamble responsibly\n#nflbetting #overunder #sportsbetting #nfl")

    # ---- 3. Over/Under teams ----
    def ou_row(t):
        r = recs[t]
        v = r["ou_margin_sum"] / r["games"]
        return {"abbr": t, "color": D.TEAMS[t][1], "name": D.TEAMS[t][0], "value": v,
                "value_label": f"{v:+.1f}", "record": f"O/U {rec(r['ou_O'], r['ou_U'], r['ou_P'])}",
                "pct": r["ou_O"] / max(1, r["ou_O"] + r["ou_U"])}
    ou_ranked = sorted((ou_row(t) for t in recs), key=lambda x: (x["pct"], x["value"]), reverse=True)
    ou_list = ou_ranked[:6] + ou_ranked[-6:]
    emit("03_overs_unders", lambda s: T.bar_ranking(
        'Over teams vs<br><em>under teams</em>', "Avg. points vs. the closing total per game",
        ou_list, tag=f"NFL · {thru}", source=SRC, size=s, note=thru_note),
        f"Overs and unders, team by team 📈📉\n\n"
        "Most overs: " + ", ".join(x["name"] + " (" + x["record"][4:] + ")" for x in ou_ranked[:3]) + "\n"
        "Most unders: " + ", ".join(x["name"] + " (" + x["record"][4:] + ")" for x in ou_ranked[-3:]) + "\n\n"
        f"Bar = how many points over/under the closing total their games land on average. {thru_note}.\n\n"
        "21+ | Gamble responsibly\n#nflbetting #overunder #totals #sportsbetting")

    # ---- 4. Matchup cards for next week ----
    nxt = args.next_week or min(g["week"] for g in games if not g["final"] and g["week"] > last_wk)
    upcoming = [g for g in games if g["week"] == nxt and not g["final"]]
    try:
        live = D.espn_lines_for_week(games, nxt)
    except Exception as e:  # ESPN down → still render with nflverse lines
        print("  ! ESPN lines unavailable:", e)
        live = {}
    mdir = os.path.join(out, f"week{nxt}_matchups")
    for g in upcoming:
        a, h = g["away_team"], g["home_team"]
        ra, rh = recs[a], recs[h]
        dk = live.get(g["game_id"], {})
        line_info = [("Spread", spread_text(g, h, a, g["spread_line"])),
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
        A = {"abbr": a, "name": D.TEAMS[a][0], "color": D.TEAMS[a][1]}
        H = {"abbr": h, "name": D.TEAMS[h][0], "color": D.TEAMS[h][1]}
        kick = f"{g['weekday'][:3]} {g['gameday'][5:].replace('-', '/')} · {g['gametime']} ET"
        name = f"{a}_at_{h}"
        for s in sizes:
            html_to_png(T.matchup(A, H, line_info, stats, tag=f"Week {nxt}", source=SRC, size=s,
                                  note=f"{kick} · Season stats {thru.lower()}"),
                        os.path.join(mdir, f"{name}_{s}.png"), s)
        captions.append((f"week{nxt}_matchups/{name}",
                         f"{D.TEAMS[a][0]} @ {D.TEAMS[h][0]} | Week {nxt} breakdown 🏈\n\n"
                         f"Line: {line_info[0][1]}, O/U {line_info[1][1]}\n"
                         f"{D.TEAMS[a][0]} ATS: {stats[1][1]} · {D.TEAMS[h][0]} ATS: {stats[1][2]}\n\n"
                         f"Lines move. Check your book before betting.\n\n21+ | Gamble responsibly\n"
                         f"#nfl #nflbetting #{D.TEAMS[a][0].lower()} #{D.TEAMS[h][0].lower()} #sportsbetting"))
    print(f"  ✔ {len(upcoming)} Week {nxt} matchup cards")

    with open(os.path.join(out, "captions.md"), "w") as f:
        f.write(f"# SharpCharts captions · generated {date.today()}\n\n")
        for name, cap in captions:
            f.write(f"## {name}\n\n```\n{cap}\n```\n\n")
    print("Output:", out)


if __name__ == "__main__":
    main()
