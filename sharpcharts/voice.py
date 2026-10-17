"""Digit's voice: human openers and sign-offs wrapped around the (unchanged) data caption.

The data lines are never edited here: we only add a conversational first line and, sometimes,
a sign-off, picked deterministically from the post key so re-runs produce the same caption.
"""
import hashlib

OPENERS = {
    "recap": [
        "Some of these teams owe bettors an apology 😤",
        "Another week, another pile of bad beats. Here's who actually covered 👇",
        "If you bet on these teams this year... we need to talk 😬",
        "The spread doesn't care about your feelings. Weekly receipts 📊",
        "Week's in the books. Some teams are cashing, some are costing you money 💸",
    ],
    "slate": [
        "New week, new numbers. Here's the whole board 👀",
        "Lines are out. Grab a coffee, this is your cheat sheet ☕",
        "Every game, every line, one swipe. You're welcome 🦊",
        "Before you lock in your card, look at this first 👇",
    ],
    "matchup": [
        "Primetime. Here's what the numbers actually say 🏈",
        "Everyone's going to be watching this one. Here's the data 👀",
        "Big game tonight. Let's see who's really been covering 📊",
    ],
    "waiver": [
        "Waiver wire time. Follow the volume, not the hype 📈",
        "Some guys just got a LOT more work. Some guys... didn't 👀",
        "Before you blow your FAAB, check who's actually getting the ball 🧐",
        "Usage doesn't lie. Here are this week's risers and fallers 👇",
    ],
    "fantasy": [
        "Volume is king. Here's who's getting fed 🍽️",
        "Want to know who to trust? Follow the touches 👇",
        "Opportunity > everything. The numbers 📊",
    ],
    "ats_bad": [
        "Oof. Some of these teams can't cover to save their lives 😬",
        "If you keep betting these teams, I can't help you 🦊",
    ],
    "trend": [
        "Okay, this one surprised me 👀",
        "Stat of the day, and it's a good one 📊",
        "Here's a number you'll want to remember this weekend 🧠",
        "Not saying it'll last... but it's hard to ignore 👀",
    ],
    "overunder": [
        "Some teams just can't stop scoring (or can't score at all) 😅",
        "Over bettors, this one's for you 📈",
    ],
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

SIGNOFFS = ["— Digit 🦊", "Digit out ✌️🦊", "— Digit (the fox with the spreadsheets) 🦊", "— Digit 🦊📊"]


def _kind(key, caption):
    k = key.lower()
    for part, kind in (("waiver", "waiver"), ("reel-ats", "recap"), ("recap", "recap"), ("slate", "slate"),
                       ("gameday", "slate"), ("snf", "matchup"), ("mnf", "matchup"), ("tnf", "matchup"),
                       ("fantasy", "fantasy"), ("reel-ou", "overunder"), ("onestat", "trend"), ("trend", "trend"),
                       ("cfb", "cfb"), ("mlb", "mlb")):
        if part in k:
            if kind == "trend" and ("can't cover" in caption or "0-" in caption.split("\n")[0]):
                return "ats_bad"
            return kind
    return None


def humanize(key, caption):
    kind = _kind(key, caption)
    if not kind:
        return caption
    h = int(hashlib.sha256(key.encode()).hexdigest(), 16)
    opener = OPENERS[kind][h % len(OPENERS[kind])]
    lines = caption.split("\n")
    if kind in ("cfb", "mlb"):          # their first line is a generic title the opener already covers
        lines = lines[1:]
        while lines and not lines[0].strip():
            lines = lines[1:]
    # sign-off goes right before the source/disclaimer block, on about half of posts
    cut = next((i for i, l in enumerate(lines) if l.startswith(("Data", "Stats", "Starters", "Lines:", "Season", "Raw",
                                                                "👉", "21+"))), len(lines))
    body = lines[:cut]
    while body and not body[-1].strip():
        body.pop()
    if (h >> 8) % 2 == 0:
        body += ["", SIGNOFFS[(h >> 12) % len(SIGNOFFS)]]
    return "\n".join([opener, ""] + body + [""] + lines[cut:]).replace("\n\n\n", "\n\n")
