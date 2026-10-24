"""Rotating debate questions for captions.

Most posts end with one; roughly 1 in 4 deliberately skip it so it never feels canned.
Questions are about sports takes, never people's identities, and never "comment YES"
style bait (Instagram demotes that).
"""
import hashlib

BANK = {
    "recap": [
        "{worst} or {best}: who flips the script first? 👇",
        "Which of these teams is the biggest fraud ATS? 👇",
        "{best} are covering by {best_margin} a game. Real or regression coming?",
        "{worst} haven't been covering. Buy-low spot or stay away?",
        "Favorites or dogs the rest of the way? Pick a side 👇",
    ],
    "week": [
        "Favorites or dogs the rest of the way? Pick a side 👇",
        "Which Week {week} result surprised you most? 👇",
        "Overs or unders next week? Make your case 👇",
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
        "{team} the rest of the way: ride them or fade them? 👇",
        "Does this trend hold up all season? 👇",
        "Real trend or small-sample noise? Make your case.",
        "Are you riding this or fading it?",
    ],
    "fantasy": [
        "Sell {top} now or hold? 👇",
        "Is {top}'s role real or a one-week fluke? 👇",
        "{top} or {second}: who finishes higher this year? 👇",
        "Who's the most underrated name on this list? 👇",
        "Who on here are you selling high? 👇",
        "Volume is king. Who's missing from this list?",
        "Rank your top 3 from this chart 👇",
    ],
    "onestat": [
        "Sell {top} now or hold? 👇",
        "{team}: ride them or fade them? 👇",
        "Real or small-sample fluke? 👇",
        "Does this last all season? 👇",
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
    """Deterministic per post key, so a re-run produces the same caption.
    Only questions whose {names} we have values for are eligible; named questions are preferred."""
    bank = BANK.get(kind)
    if not bank:
        return ""
    h = int(hashlib.sha256(key.encode()).hexdigest(), 16)
    if h % skip_rate == 0:
        return ""
    usable = []
    for q in bank:
        try:
            usable.append(q.format(**values))
        except (KeyError, IndexError):
            pass
    named = [q for q, raw in zip(usable, [b for b in bank if _fits(b, values)]) if "{" in raw]
    pool = named if named and (h // skip_rate) % 3 else usable   # ~2/3 of the time, use a name
    return pool[(h // (skip_rate * 3)) % len(pool)] if pool else ""


def _fits(q, values):
    try:
        q.format(**values)
        return True
    except (KeyError, IndexError):
        return False
