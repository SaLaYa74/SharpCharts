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


def make_reel(out_dir, name, hook, chart_html, tag, seed):
    """hook=(line1, line2); chart_html(p) -> HTML at animation progress p. Returns (mp4, cover_jpg)."""
    os.makedirs(out_dir, exist_ok=True)
    work = tempfile.mkdtemp(prefix="reel_")
    seq = []  # (png, seconds)

    def frame(html, label, secs):
        path = os.path.join(work, f"{len(seq):03d}_{label}.png")
        html_to_png(html, path, "reel")
        seq.append((path, secs))
        return path

    def blend(a, b, steps, secs):
        ia, ib = Image.open(a).convert("RGB"), Image.open(b).convert("RGB")
        for i in range(1, steps + 1):
            path = os.path.join(work, f"{len(seq):03d}_x.png")
            Image.blend(ia, ib, i / (steps + 1)).save(path)
            seq.append((path, secs))

    for i, p in enumerate((0.0, 0.35, 0.7, 1.0)):                       # hook pops in
        last_hook = frame(T.reel_hook(*hook, tag=tag, p=p), "hook", 0.07)
    seq.append((last_hook, 1.6))                                         # hold hook
    chart0 = os.path.join(work, "chart0.png")
    html_to_png(chart_html(0.0), chart0, "reel")
    blend(last_hook, chart0, 6, 0.05)                                   # crossfade
    steps = 20
    for i in range(steps):                                              # chart builds in
        last_chart = frame(chart_html(_ease(i / (steps - 1))), "chart", 0.075)
    seq.append((last_chart, 5.0))                                       # hold so people can read
    outro = os.path.join(work, "outro.png")
    html_to_png(T.reel_outro(tag), outro, "reel")
    blend(last_chart, outro, 6, 0.05)
    seq.append((outro, 1.9))

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

def _post(key, mp4, cover, caption, rep):
    video_checks(rep, mp4)
    C.image(rep, cover, "reel")
    return P.Post(key=key, caption=caption, images=[{"reel": mp4, "cover": cover}], media="reel", checks=rep)


def reel_ats(ctx, out_dir, sizes=None):
    ranked = P.ats_ranked(ctx)
    rows = ranked[:6] + ranked[-6:]
    zero = [r for r in ranked if r["wins"] == 0]
    if zero:
        hook = (f"{len(zero)} NFL team{'s' * (len(zero) > 1)}", f"{'haven' if len(zero) > 1 else 'hasn'}'t covered once")
    else:
        hook = ("Who's actually", "cashing tickets?")
    tag = f"NFL · {ctx.thru}"
    mp4, cover = make_reel(out_dir, "reel_ats", hook, lambda p: T.bar_ranking(
        'Best &amp; worst<br><em>against the spread</em>', "Avg. cover margin per game",
        rows, tag=tag, source=P.SRC, size="reel", note=ctx.thru_note, p=p), tag, f"ats-{ctx.thru_week}")
    key = f"{ctx.season}-wk{ctx.thru_week:02d}-reel-ats"
    best, worst = rows[0], rows[-1]
    caption = P.with_question(
        f"Best and worst ATS teams through Week {ctx.thru_week} 📊\n\n"
        f"{best['name']} {best['ats']} ATS ({best['value_label']} per game). {worst['name']} {worst['ats']} ATS.",
        "recap", key, best=best["name"], best_margin=best["value_label"], worst=worst["name"])
    caption += f"\n\nFollow for daily verified betting data.\n{P.DISCLAIMER}\n#nfl #nflbetting #ats #sportsbetting #bettingdata"
    return _post(key, mp4, cover, caption, C.Report("reel ats").extend(ctx.report))


def reel_ou(ctx, out_dir, sizes=None):
    ranked = P.ou_ranked_rows(ctx)
    rows = ranked[:6] + ranked[-6:]
    top = rows[0]
    tag = f"NFL · {ctx.thru}"
    o, u = (int(x) for x in top["ou"].split("-")[:2])
    hook = (f"{top['name']} games", "keep going over") if o > u else ("The NFL's biggest", "over & under teams")
    mp4, cover = make_reel(out_dir, "reel_ou", hook, lambda p: T.bar_ranking(
        'Over teams vs<br><em>under teams</em>', "Avg. points vs. the closing total per game",
        rows, tag=tag, source=P.SRC, size="reel", note=ctx.thru_note, p=p), tag, f"ou-{ctx.thru_week}")
    key = f"{ctx.season}-wk{ctx.thru_week:02d}-reel-ou"
    caption = P.with_question(
        f"The NFL's biggest over and under teams through Week {ctx.thru_week} 📈📉\n\n"
        f"{top['name']} games are landing {top['value_label']} points vs. the total ({top['ou']} O/U). "
        f"{rows[-1]['name']} games: {rows[-1]['value_label']} ({rows[-1]['ou']}).",
        "trend", key)
    caption += f"\n\nFollow for daily verified betting data.\n{P.DISCLAIMER}\n#nfl #nflbetting #overunder #totals #sportsbetting"
    return _post(key, mp4, cover, caption, C.Report("reel ou").extend(ctx.report))


def reel_fantasy(ctx, out_dir, sizes=None, focus="wr"):
    b = P.fantasy_board(ctx, focus)
    lead = b["top"][0]
    last = lead["name"].split()[-1] if len(lead["name"]) > 14 else lead["name"]
    what = "of his team's targets" if focus == "wr" else "of his team's touches"
    tag = f"{b['tag']} · {ctx.thru}"
    mp4, cover = make_reel(out_dir, f"reel_fantasy_{focus}", (f"{last} sees {lead['share'] * 100:.0f}%", what),
                           lambda p: T.bar_ranking(b["title"], b["sub"], b["bars"], tag=tag, size="reel", diverging=False,
                                                   source="nflverse player stats", note=f"Min. {b['min_games']} games", p=p),
                           tag, f"fantasy-{focus}-{ctx.thru_week}")
    key = f"{ctx.season}-wk{ctx.thru_week:02d}-reel-fantasy-{focus}"
    caption = P.with_question(
        f"{'Target share' if focus == 'wr' else 'RB opportunity share'} leaders through Week {ctx.thru_week} 🎯\n\n"
        + "\n".join(f"{i + 1}. {p['name']} ({p['team']}) {p['share'] * 100:.0f}%" for i, p in enumerate(b["top"][:5])),
        "fantasy", key)
    caption += f"\n\nRaw usage data, no projections. Follow for more.\n{P.DISCLAIMER}\n{b['hashtags']}"
    return _post(key, mp4, cover, caption, C.Report("reel fantasy").extend(b["rep"]))


def reel_trend(ctx, out_dir, sizes=None, day=None):
    day = day or date.today()
    options = P._trends(ctx)
    tkey, title, sub, number, label, rows, color, sentence = options[(day.toordinal() + 1) % len(options)]
    l1, l2 = title.split("<br>")
    l2 = re.sub("</?em>", "", l2)
    tag = f"NFL · {ctx.thru}"
    mp4, cover = make_reel(out_dir, f"reel_trend_{tkey}", (l1, l2), lambda p: T.big_stat(
        title, sub, number, label, rows, tag=tag, source=P.SRC, size="reel", color=color, p=p), tag, f"trend-{day}")
    key = f"{day.isoformat()}-reel-trend"
    caption = P.with_question(f"{sentence} 📊\n\nData {ctx.thru.lower()}, verified vs ESPN.", "trend", key)
    caption += f"\n\nFollow for daily verified betting data.\n{P.DISCLAIMER}\n#nfl #nflbetting #bettingtrends #sportsbetting"
    return _post(key, mp4, cover, caption, C.Report("reel trend").extend(ctx.report))


BUILDERS = {"reel_ats": reel_ats, "reel_ou": reel_ou, "reel_fantasy": reel_fantasy, "reel_trend": reel_trend}
