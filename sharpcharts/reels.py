"""Animated Reels: hook → chart builds in → hold → follow CTA, with an original beat.

Each Reel reuses the same verified data (and data checks) as the matching feed post.
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import date

from PIL import Image

from . import checks as C
from . import posts as P
from . import templates as T
from .music import make_beat
from .render import html_to_png

FPS = 30


def ffmpeg_exe():
    try:
        import imageio_ffmpeg
    except ImportError:
        exe = shutil.which("ffmpeg")
        if exe:
            return exe
        subprocess.run([sys.executable, "-m", "pip", "install", "--quiet", "imageio-ffmpeg"], check=True)
        import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def _ease(x):
    return 1 - (1 - x) ** 3  # ease-out cubic


def make_reel(out_dir, name, hook, chart_html, tag, seed, hold=5.2):
    """Motion from frame 1: the chart animates in under the hook headline, holds so it can be read,
    and ends on the full chart (loops cleanly back to the empty chart). chart_html(p) -> HTML.
    `hook` and `tag` are baked into chart_html by the caller. Returns (mp4, cover_jpg)."""
    os.makedirs(out_dir, exist_ok=True)
    work = tempfile.mkdtemp(prefix="reel_")
    seq = []  # (png, seconds)
    steps = 24
    for i in range(steps):                                   # 1.6s build-in, starting at t=0
        path = os.path.join(work, f"{i:03d}.png")
        html_to_png(chart_html(_ease(i / (steps - 1))), path, "reel")
        seq.append((path, 0.067))
    last_chart = seq[-1][0]
    seq.append((last_chart, hold))                           # hold long enough to read
    total = sum(s for _, s in seq)
    audio = os.path.join(work, "beat.wav")
    make_beat(audio, total + 0.2, seed)
    listing = os.path.join(work, "frames.txt")
    with open(listing, "w") as f:
        for path, secs in seq:
            f.write(f"file '{path}'\nduration {secs:.3f}\n")
        f.write(f"file '{seq[-1][0]}'\n")  # concat demuxer needs the last file repeated
    mp4 = os.path.join(out_dir, f"{name}.mp4")
    subprocess.run([ffmpeg_exe(), "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", listing,
                    "-i", audio, "-vf", f"fps={FPS},format=yuv420p", "-c:v", "libx264", "-preset", "medium",
                    "-crf", "20", "-profile:v", "high", "-c:a", "aac", "-b:a", "128k", "-ar", "44100",
                    "-shortest", "-movflags", "+faststart", mp4], check=True)
    cover = os.path.join(out_dir, f"{name}_cover.jpg")
    Image.open(last_chart).convert("RGB").save(cover, "JPEG", quality=90)
    shutil.rmtree(work, ignore_errors=True)
    return mp4, cover


def video_checks(rep, mp4):
    """Instagram Reels requirements + sanity: 9:16 1080x1920, 3-90s, has audio, < 20MB (CDN limit)."""
    name = os.path.basename(mp4)
    if not rep.require(os.path.exists(mp4), f"{name}: rendered", "video missing"):
        return
    size_mb = os.path.getsize(mp4) / 1e6
    rep.require(0.2 < size_mb < 20, f"{name}: file size", f"{size_mb:.1f} MB")
    info = subprocess.run([ffmpeg_exe(), "-hide_banner", "-i", mp4], capture_output=True, text=True).stderr
    dur = re.search(r"Duration: (\d+):(\d+):([\d.]+)", info)
    secs = int(dur.group(1)) * 3600 + int(dur.group(2)) * 60 + float(dur.group(3)) if dur else 0
    rep.require(3 <= secs <= 90, f"{name}: duration", f"{secs:.1f}s (needs 3-90s)")
    rep.require("1080x1920" in info, f"{name}: 1080x1920", "wrong resolution")
    rep.require("Audio: aac" in info, f"{name}: has audio", "no AAC audio track")
    rep.require("Video: h264" in info, f"{name}: H.264 video", "wrong codec")


# ---------------------------------------------------------------- builders

def _glance(rows, detail="ats"):
    """Reels show one short detail line per row (record or team), not the full stat line."""
    out = []
    for r in rows:
        d = {"ats": r.get("ats", "") and f"{r['ats']} ATS", "ou": r.get("ou", "") and f"{r['ou']} O/U",
             "team": r.get("record", "").split(" · ")[0]}[detail]
        out.append({**r, "record": d})
    return out


def _share_kit(out_dir, reddit_title, body, x_text):
    """Ready-to-paste text for Reddit/X (you post it; we never auto-post to other sites)."""
    with open(os.path.join(out_dir, "share.md"), "w") as f:
        f.write(f"## Reddit\n**Title:** {reddit_title}\n\n{body}\n\n(Source: nflverse play-by-play data. Chart by @sharp_charts)\n\n"
                f"## X / Twitter\n{x_text}\n")


def _post(key, mp4, cover, caption, rep):
    video_checks(rep, mp4)
    C.image(rep, cover, "reel")
    return P.Post(key=key, caption=caption, images=[{"reel": mp4, "cover": cover}], media="reel", checks=rep)


def reel_ats(ctx, out_dir, sizes=None):
    ranked = P.ats_ranked(ctx)
    zero = [r for r in ranked if r["wins"] == 0]
    n_bottom = min(max(4, len(zero)), 6)          # every team the hook mentions is on the chart
    rows = ranked[:8 - n_bottom] + ranked[-n_bottom:]
    if zero and len(zero) <= n_bottom:
        hook = (f"{len(zero)} NFL team{'s' * (len(zero) > 1)}", f"{'haven' if len(zero) > 1 else 'hasn'}'t covered once", "red")
    else:
        hook = ("Who's actually", "cashing tickets?")
    tag = f"NFL · {ctx.thru}"
    mp4, cover = make_reel(out_dir, "reel_ats", hook, lambda p: T.bar_ranking(
        'Best &amp; worst<br><em>against the spread</em>', "Avg. cover margin per game",
        _glance(rows), tag=tag, source=P.SRC, size="reel", note=ctx.thru_note, p=p, hook=hook, glance=True),
        tag, f"ats-{ctx.thru_week}")
    key = f"{ctx.season}-wk{ctx.thru_week:02d}-reel-ats"
    best, worst = rows[0], rows[-1]
    caption = P.with_question(
        f"Best and worst ATS teams through Week {ctx.thru_week} 📊\n\n"
        f"{best['name']} {best['ats']} ATS ({best['value_label']} per game). {worst['name']} {worst['ats']} ATS.",
        "recap", key, best=best["name"], best_margin=best["value_label"], worst=worst["name"])
    caption += f"\n\n👉 Follow @sharp_charts for daily verified betting data.\n{P.DISCLAIMER}\n#nfl #nflbetting #ats #sportsbetting #bettingdata"
    return _post(key, mp4, cover, caption, C.Report("reel ats").extend(ctx.report))


def reel_ou(ctx, out_dir, sizes=None):
    ranked = P.ou_ranked_rows(ctx)
    rows = ranked[:4] + ranked[-4:]
    top = rows[0]
    tag = f"NFL · {ctx.thru}"
    o, u = (int(x) for x in top["ou"].split("-")[:2])
    hook = (f"{top['name']} games", "keep going over") if o > u else ("The NFL's biggest", "over & under teams")
    mp4, cover = make_reel(out_dir, "reel_ou", hook, lambda p: T.bar_ranking(
        'Over teams vs<br><em>under teams</em>', "Avg. points vs. the closing total per game",
        _glance(rows, "ou"), tag=tag, source=P.SRC, size="reel", note=ctx.thru_note, p=p, hook=hook, glance=True),
        tag, f"ou-{ctx.thru_week}")
    key = f"{ctx.season}-wk{ctx.thru_week:02d}-reel-ou"
    caption = P.with_question(
        f"The NFL's biggest over and under teams through Week {ctx.thru_week} 📈📉\n\n"
        f"{top['name']} games are landing {top['value_label']} points vs. the total ({top['ou']} O/U). "
        f"{rows[-1]['name']} games: {rows[-1]['value_label']} ({rows[-1]['ou']}).",
        "trend", key)
    caption += f"\n\n👉 Follow @sharp_charts for daily verified betting data.\n{P.DISCLAIMER}\n#nfl #nflbetting #overunder #totals #sportsbetting"
    return _post(key, mp4, cover, caption, C.Report("reel ou").extend(ctx.report))


def reel_fantasy(ctx, out_dir, sizes=None, focus="wr"):
    b = P.fantasy_board(ctx, focus)
    lead = b["top"][0]
    last = lead["name"].split()[-1] if len(lead["name"]) > 14 else lead["name"]
    what = "of his team's targets" if focus == "wr" else "of his team's touches"
    tag = f"{b['tag']} · {ctx.thru}"
    hook = (f"{last}: {lead['share'] * 100:.0f}%", f"of {lead['team']}'s {'targets' if focus == 'wr' else 'touches'}")
    mp4, cover = make_reel(out_dir, f"reel_fantasy_{focus}", hook,
                           lambda p: T.bar_ranking(b["title"], b["sub"], _glance(b["bars"][:8], "team"), tag=tag, size="reel", diverging=False, glance=True,
                                                   source="nflverse player stats", note=f"Min. {b['min_games']} games", p=p,
                                                   hook=hook),
                           tag, f"fantasy-{focus}-{ctx.thru_week}")
    key = f"{ctx.season}-wk{ctx.thru_week:02d}-reel-fantasy-{focus}"
    caption = P.with_question(
        f"{'Target share' if focus == 'wr' else 'RB opportunity share'} leaders through Week {ctx.thru_week} 🎯\n\n"
        + "\n".join(f"{i + 1}. {p['name']} ({p['team']}) {p['share'] * 100:.0f}%" for i, p in enumerate(b["top"][:5])),
        "fantasy", key, top=b["top"][0]["name"], second=b["top"][1]["name"])
    top5 = "\n".join(f"{i + 1}. {p['name']} ({p['team']}) {p['share'] * 100:.0f}%" for i, p in enumerate(b["top"][:8]))
    _share_kit(out_dir, f"[OC] {'Target share' if focus == 'wr' else 'RB opportunity share'} leaders through Week {ctx.thru_week}",
               f"{b['sub'].replace('&amp;', '&')}, minimum {b['min_games']} games:\n\n{top5}",
               f"{'Target share' if focus == 'wr' else 'RB touch share'} leaders thru Week {ctx.thru_week} 🎯\n\n"
               + "\n".join(f"{p['name']} {p['share'] * 100:.0f}%" for p in b["top"][:5]) + "\n\n#FantasyFootball")
    caption += f"\n\nRaw usage data, no projections.\n👉 Follow @sharp_charts for more.\n{P.DISCLAIMER}\n{b['hashtags']}"
    return _post(key, mp4, cover, caption, C.Report("reel fantasy").extend(b["rep"]))


def reel_trend(ctx, out_dir, sizes=None, day=None):
    day = day or date.today()
    options = P._trends(ctx)
    tkey, title, sub, number, label, rows, color, sentence = options[(day.toordinal() + 1) % len(options)]
    l1, l2 = title.split("<br>")
    l2 = re.sub("</?em>", "", l2)
    tag = f"NFL · {ctx.thru}"
    hook = (re.sub("<[^>]+>", "", l1), l2)
    mp4, cover = make_reel(out_dir, f"reel_trend_{tkey}", hook, lambda p: T.big_stat(
        title, sub, number, label, rows, tag=tag, source=P.SRC, size="reel", color=color, p=p, hook=hook), tag, f"trend-{day}")
    key = f"{day.isoformat()}-reel-trend"
    team_kw = {"team": hook[0][4:]} if hook[0].startswith("The ") else {}
    caption = P.with_question(f"{sentence} 📊\n\nData {ctx.thru.lower()}, verified vs ESPN.", "trend", key, **team_kw)
    caption += f"\n\n👉 Follow @sharp_charts for daily verified betting data.\n{P.DISCLAIMER}\n#nfl #nflbetting #bettingtrends #sportsbetting"
    return _post(key, mp4, cover, caption, C.Report("reel trend").extend(ctx.report))


def reel_waiver(ctx, out_dir, sizes=None):
    """Tuesday waiver wire: biggest usage risers (green) and fallers (red) from last week."""
    risers, fallers, rep = P.usage_movers(ctx, n=4)
    top = risers[0]
    first = top["name"].split()[0]
    last = top["name"].split()[-1] if len(top["name"]) > 13 else top["name"]
    hook = (f"{last}'s role", "just exploded")
    pct = lambda x: f"{x * 100:.0f}%"
    def row(m):
        return {"abbr": m["team"], "color": P.D.TEAMS.get(m["team"], ("", "#3A4A6B"))[1], "name": m["name"],
                "value": m["delta"], "value_label": f"{m['delta'] * 100:+.0f}",
                "record": f"{m['pos']} · {pct(m['base'])} → {pct(m['now'])} of touches"}
    rows = [row(m) for m in risers] + [row(m) for m in fallers[::-1]]
    tag = f"Waiver wire · Wk {ctx.thru_week + 1}"
    mp4, cover = make_reel(out_dir, "reel_waiver", hook, lambda p: T.bar_ranking(
        "Usage risers<br><em>&amp; fallers</em>", f"Share of team carries + targets: Week {ctx.thru_week} vs. before",
        rows, tag=tag, source="nflverse player stats", size="reel", note="Change in percentage points",
        p=p, hook=hook, glance=True), tag, f"waiver-{ctx.thru_week}")
    key = f"{ctx.season}-wk{ctx.thru_week:02d}-reel-waiver"
    lines_up = "\n".join(f"🟢 {m['name']} ({m['team']} {m['pos']}): {pct(m['base'])} → {pct(m['now'])}" for m in risers)
    lines_dn = "\n".join(f"🔴 {m['name']} ({m['team']} {m['pos']}): {pct(m['base'])} → {pct(m['now'])}" for m in fallers)
    caption = P.with_question(
        f"Week {ctx.thru_week + 1} waiver wire: who's getting more of the ball? 📈📉\n\n"
        f"Share of team carries + targets, Week {ctx.thru_week} vs. their earlier average:\n\n{lines_up}\n\n{lines_dn}",
        "fantasy", key, top=risers[0]["name"], second=risers[1]["name"])
    _share_kit(out_dir, f"[OC] Week {ctx.thru_week + 1} waiver wire: biggest usage risers & fallers (share of team carries + targets)",
               f"Week {ctx.thru_week} share of team carries + targets vs. each player's earlier average:\n\n{lines_up}\n\n{lines_dn}",
               f"Week {ctx.thru_week + 1} waiver wire, by usage 📈📉\n\n" + "\n".join(
                   f"🟢 {m['name']} {pct(m['base'])} → {pct(m['now'])}" for m in risers[:3])
               + "\n" + "\n".join(f"🔴 {m['name']} {pct(m['base'])} → {pct(m['now'])}" for m in fallers[:2])
               + "\n\n#FantasyFootball #WaiverWire")
    caption += (f"\n\nRaw usage data, no projections. Source: nflverse.\n👉 Follow @sharp_charts for weekly usage data.\n"
                f"{P.DISCLAIMER}\n#fantasyfootball #waiverwire #fantasyfootballadvice #nfl #week{ctx.thru_week + 1}")
    return _post(key, mp4, cover, caption, rep)


def reel_onestat(ctx, out_dir, sizes=None, day=None):
    """One giant number. Rotates through verified facts so consecutive weeks differ."""
    day = day or date.today()
    ats = P.ats_ranked(ctx)
    facts = []
    w = ats[-1]
    facts.append(("ats_worst", (f"The {w['name']}", "can't cover", "red"), w["ats"], "against the spread", w, "red",
                  f"The {w['name']} are {w['ats']} against the spread this season.", {"team": w["name"]}))
    b = ats[0]
    facts.append(("ats_best", (f"The {b['name']}", "keep cashing"), b["ats"], "against the spread", b, "green",
                  f"The {b['name']} are {b['ats']} against the spread this season.", {"team": b["name"]}))
    try:
        rb = P.fantasy_board(ctx, "rb")["top"][0]
        facts.append(("rb_share", (f"{rb['name']}", "gets the ball"), f"{rb['share'] * 100:.0f}%", "of his team's touches",
                      {"abbr": rb["team"], "color": P.D.TEAMS.get(rb["team"], ("", "#3A4A6B"))[1], "name": P.D.TEAMS.get(rb["team"], (rb["team"],))[0]},
                      "green", f"{rb['name']} is getting {rb['share'] * 100:.0f}% of his team's carries + targets.",
                      {"top": rb["name"]}))
    except P.DataError:
        pass
    fkey, hook, number, label, who, color, sentence, qvals = facts[day.toordinal() % len(facts)]
    who = {"abbr": who["abbr"], "color": who["color"], "name": who.get("name", "")}
    tag = f"NFL · {ctx.thru}"
    mp4, cover = make_reel(out_dir, f"reel_onestat_{fkey}", hook, lambda p: T.one_stat(
        hook, number, label, who, color, tag=tag, source="nflverse player stats" if fkey.startswith("rb") else P.SRC, p=p),
        tag, f"onestat-{day}")
    key = f"{day.isoformat()}-reel-onestat"
    kind = "onestat"
    caption = P.with_question(f"{sentence} 📊\n\nData {ctx.thru.lower()}, verified.", kind, key, **qvals)
    caption += f"\n\n👉 Follow @sharp_charts for one stat a day.\n{P.DISCLAIMER}\n#nfl #nflbetting #fantasyfootball #sportsbetting"
    return _post(key, mp4, cover, caption, C.Report("reel onestat").extend(ctx.report))


BUILDERS = {"reel_onestat": reel_onestat, "reel_ats": reel_ats, "reel_ou": reel_ou, "reel_trend": reel_trend, "reel_waiver": reel_waiver,
            "reel_fantasy": reel_fantasy,
            "reel_fantasy_rb": lambda ctx, out_dir, sizes=None: reel_fantasy(ctx, out_dir, focus="rb"),
            "reel_fantasy_wr": lambda ctx, out_dir, sizes=None: reel_fantasy(ctx, out_dir, focus="wr")}
