#!/usr/bin/env python3
"""Build one SharpCharts post and (optionally) publish it to Instagram.

    python3 autopost.py slate              # dry run: build + save to media/, nothing posted
    python3 autopost.py auto               # pick by day of week (Tue recap, Thu slate, Sat featured)
    python3 autopost.py recap --live       # actually publish (needs IG_TOKEN + a pushed git repo)

In GitHub Actions, posting is live only when the repo variable POSTING_ENABLED is "true".
Safety: nothing is posted if score verification fails, the week isn't complete,
the caption breaks Instagram limits, or the same post key was already published.
"""
import argparse
import json
import os
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from PIL import Image

from sharpcharts import posts as P

ROOT = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(ROOT, "posted.json")
SCHEDULE = {1: "recap", 3: "slate", 5: "featured"}  # Mon=0 … Tue=1, Thu=3, Sat=5 (Pacific time)


def sh(*cmd):
    return subprocess.run(cmd, cwd=ROOT, check=True, capture_output=True, text=True).stdout.strip()


def summary(text):
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    if path:
        with open(path, "a") as f:
            f.write(text + "\n")
    print(text)


def load_log():
    return json.load(open(LOG)) if os.path.exists(LOG) else {}


def to_jpeg(png):
    jpg = png[:-4] + ".jpg"
    Image.open(png).convert("RGB").save(jpg, "JPEG", quality=92, optimize=True)  # API requires JPEG
    os.remove(png)
    return jpg


def check_caption(caption):
    if len(caption) > 2200:
        raise P.DataError(f"Caption too long ({len(caption)} > 2200)")
    if caption.count("#") > 30:
        raise P.DataError("More than 30 hashtags")


def git_push(message, paths):
    sh("git", "add", *paths)
    if not sh("git", "status", "--porcelain", *paths):
        return sh("git", "rev-parse", "HEAD")
    sh("git", "commit", "-m", message)
    sh("git", "pull", "--rebase", "--quiet")
    sh("git", "push", "--quiet")
    return sh("git", "rev-parse", "HEAD")


def wait_public(url, tries=24):
    for _ in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, method="HEAD"), timeout=20) as r:
                if r.status == 200:
                    return
        except Exception:
            pass
        time.sleep(5)
    raise RuntimeError(f"Image never became public: {url}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("kind", choices=["auto", *P.BUILDERS])
    ap.add_argument("--season", type=int, default=2026)
    ap.add_argument("--week", type=int, help="override the week for slate/featured")
    ap.add_argument("--live", action="store_true", help="publish to Instagram (default: dry run)")
    ap.add_argument("--force", action="store_true", help="rebuild/post even if this key was already posted")
    args = ap.parse_args()

    in_ci = os.environ.get("GITHUB_ACTIONS") == "true"
    live = args.live or (in_ci and os.environ.get("POSTING_ENABLED", "").lower() == "true")

    kind = args.kind
    if kind == "auto":
        today = datetime.now(ZoneInfo("America/Los_Angeles")).weekday()
        kind = SCHEDULE.get(today)
        if not kind:
            summary("No post scheduled today.")
            return

    try:
        ctx = P.Context(args.season)
        print(f"✔ Verified {ctx.verified} final scores against ESPN · stats thru week {ctx.thru_week}")
        builder = P.BUILDERS[kind]
        # Key first, so we don't render a post that's already out.
        week = ctx.thru_week if kind == "recap" else (args.week or ctx.upcoming_week)
        key = f"{args.season}-wk{week:02d}-{kind}"
        log = load_log()
        if key in log and not args.force:
            summary(f"⏭️ `{key}` already posted ({log[key].get('permalink')}). Skipping.")
            return
        out_dir = os.path.join(ROOT, "media", key)
        kwargs = {} if kind == "recap" else {"week": week}
        post = builder(ctx, out_dir, sizes=("feed",), **kwargs)
        check_caption(post.caption)
    except P.DataError as e:
        summary(f"⚠️ **Not posting ({kind})**: {e}")
        sys.exit(1)

    images = [to_jpeg(img["feed"]) for img in post.images][:P.MAX_CAROUSEL]
    with open(os.path.join(out_dir, "caption.txt"), "w") as f:
        f.write(post.caption)
    rel = [os.path.relpath(p, ROOT) for p in images]

    summary(f"## {'🚀 LIVE' if live else '🧪 DRY RUN'}: `{post.key}` ({len(images)} image{'s' if len(images) > 1 else ''})\n")
    summary("```\n" + post.caption + "\n```")

    if not in_ci and not live:
        print("\nDry run saved to", out_dir)
        return

    sha = git_push(f"{'Post' if live else 'Preview'} {post.key}", [os.path.relpath(out_dir, ROOT)])
    repo = os.environ.get("GITHUB_REPOSITORY") or sh("gh", "repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner")
    urls = [f"https://raw.githubusercontent.com/{repo}/{sha}/{r}" for r in rel]
    summary("\n" + "\n".join(f"![slide {i+1}]({u})" for i, u in enumerate(urls)))

    if not live:
        summary("\nDry run: nothing was posted. Set POSTING_ENABLED=true to go live.")
        return

    from sharpcharts.instagram import Instagram
    ig = Instagram()
    limit = ig.publishing_limit()
    if limit.get("quota_usage", 0) >= limit.get("config", {}).get("quota_total", 50):
        summary("⚠️ Instagram daily publishing limit reached. Not posting.")
        sys.exit(1)
    for u in urls:
        wait_public(u)
    media_id = ig.publish(urls, post.caption)
    link = ig.permalink(media_id)
    log = load_log()
    log[post.key] = {"media_id": media_id, "permalink": link, "images": len(urls),
                     "posted_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    with open(LOG, "w") as f:
        json.dump(log, f, indent=2)
    git_push(f"Log {post.key}", ["posted.json"])
    summary(f"\n✅ Posted: {link}")


if __name__ == "__main__":
    main()
