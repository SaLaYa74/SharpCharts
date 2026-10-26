"""Caption voice: lead with the data, one call to action, nothing that reads like an ad.

The data lines are never edited here. We drop the "👉 Follow" line, add a single save/share
line, and only give an opener to posts whose first line is a generic title (CFB, MLB).
Picks are deterministic from the post key so re-runs produce the same caption.
"""
import hashlib

OPENERS = {
    "cfb": [
        "College football Saturday. Let's go 🏈",
        "Big Saturday on the board. Here's every Top 25 line 👀",
        "Saturdays hit different. Your Top 25 cheat sheet 👇",
    ],
    "mlb": [
        "October baseball. Here's tonight ⚾",
        "Playoff baseball tonight. Here's the board 👀",
    ],
}

# Save/share prompt on every post: saves and shares are what push a post to non-followers.
SAVE_SHARE = {
    "fantasy": ["📌 Save this for waivers. 📤 Send it to your league chat.",
                "📤 Send this to the person in your league who needs it. 📌 Save it for Sunday.",
                "📌 Save this before you set your lineup. 📤 Share it with your league."],
    "betting": ["📌 Save this for your weekly card. 📤 Send it to the group chat.",
                "📤 Send this to the friend who bets every game. 📌 Save it for Sunday.",
                "📌 Save this before you set your card. 📤 Share it with your betting group."],
}


def _kind(key):
    k = key.lower()
    for part, kind in (("waiver", "fantasy"), ("fantasy", "fantasy"), ("cfb", "cfb"), ("mlb", "mlb")):
        if part in k:
            return kind
    return "betting"


def humanize(key, caption):
    kind = _kind(key)
    h = int(hashlib.sha256(key.encode()).hexdigest(), 16)
    lines = [l for l in caption.split("\n") if not l.startswith("👉")]   # Instagram already shows Follow
    head = []
    if kind in OPENERS:                 # their first line is a generic title; a person-sounding line replaces it
        head = [OPENERS[kind][h % len(OPENERS[kind])], ""]
        lines = lines[1:]
        while lines and not lines[0].strip():
            lines = lines[1:]
    # save/share line goes right before the source/disclaimer block
    cut = next((i for i, l in enumerate(lines) if l.startswith(("Data", "Stats", "Starters", "Lines:", "Season", "Raw",
                                                                "21+"))), len(lines))
    body = lines[:cut]
    while body and not body[-1].strip():
        body.pop()
    if "save this" not in caption.lower() and "📤" not in caption:     # builder already wrote a team-specific one
        bank = SAVE_SHARE["fantasy" if kind == "fantasy" else "betting"]
        body += ["", bank[(h >> 16) % len(bank)]]
    return "\n".join(head + body + [""] + lines[cut:]).replace("\n\n\n", "\n\n")
