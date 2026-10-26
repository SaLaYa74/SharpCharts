"""Official team logos (NFL), fetched from ESPN's public logo CDN at render time and cached locally
(data/logos/, not committed). Only used when settings.USE_TEAM_LOGOS is on."""
import base64
import os

from .data import CACHE, _get
from .settings import USE_TEAM_LOGOS

ESPN_ABBR = {"LA": "lar", "WAS": "wsh"}
URL = "https://a.espncdn.com/i/teamlogos/nfl/500/{}.png"
_uri = {}


def logo_uri(abbr):
    """data: URI for the team's logo, or None (switch off, unknown team, or download failed)."""
    if not USE_TEAM_LOGOS:
        return None
    if abbr in _uri:
        return _uri[abbr]
    path = os.path.join(CACHE, "logos", f"{abbr}.png")
    try:
        if not os.path.exists(path):
            os.makedirs(os.path.dirname(path), exist_ok=True)
            data = _get(URL.format(ESPN_ABBR.get(abbr, abbr.lower())))
            if not data.startswith(b"\x89PNG"):
                raise ValueError("not a PNG")
            with open(path, "wb") as f:
                f.write(data)
        _uri[abbr] = "data:image/png;base64," + base64.b64encode(open(path, "rb").read()).decode()
    except Exception as e:
        print(f"  ! logo unavailable for {abbr}: {e}")
        _uri[abbr] = None
    return _uri[abbr]
