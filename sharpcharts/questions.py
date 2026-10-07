"""Rotating debate questions for captions.

Most posts end with one; roughly 1 in 4 deliberately skip it so it never feels canned.
Questions are about sports takes, never people's identities, and never "comment YES"
style bait (Instagram demotes that).
"""
import hashlib

BANK = {
    "recap": [
        "Which of these teams is the biggest fraud ATS? 👇",
        "{best} are covering by {best_margin} a game. Real or regression coming?",
        "{worst} haven't been covering. Buy-low spot or stay away?",
        "Favorites or dogs the rest of the way? Pick a side 👇",
    ],
    "slate": [
        "Which line looks off to you this week? 👇",
        "Biggest upset of the week. Go 👇",
        "One game you're not touching this week, and why?",
        "Which spread would you bet if you could only pick one?",
    ],
    "matchup": [
        "{away} or {home}? Drop your side 👇",
        "Who covers: {away} or {home}?",
        "Over or under {total}? Make your case 👇",
    ],
    "trend": [
        "Does this trend hold up all season? 👇",
        "Real trend or small-sample noise? Make your case.",
        "Are you riding this or fading it?",
    ],
    "fantasy": [
        "Who's the most underrated name on this list? 👇",
        "Who on here are you selling high? 👇",
        "Volume is king. Who's missing from this list?",
        "Rank your top 3 from this chart 👇",
    ],
    "cfb": [
        "Which ranked team is going down this week? 👇",
        "Best game on the board today? 👇",
        "Which spread is the trap this week?",
    ],
    "mlb": [
        "Who's winning tonight's series games? 👇",
        "Which pitching matchup are you most excited for?",
        "Over or under in the biggest game tonight? 👇",
    ],
}


def pick(kind, key, skip_rate=4, **values):
    """Deterministic per post key, so a re-run produces the same caption."""
    bank = BANK.get(kind)
    if not bank:
        return ""
    h = int(hashlib.sha256(key.encode()).hexdigest(), 16)
    if h % skip_rate == 0:
        return ""
    q = bank[(h // skip_rate) % len(bank)]
    try:
        return q.format(**values)
    except (KeyError, IndexError):
        return bank[-1] if "{" not in bank[-1] else ""
