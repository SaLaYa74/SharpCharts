"""Official team logos (NFL, NBA), fetched from ESPN's public logo CDN at render time and cached locally
(data/logos/, not committed). Only used when settings.USE_TEAM_LOGOS is on."""
import base64
import os

from .data import CACHE, _get
from .settings import USE_TEAM_LOGOS

ESPN_ABBR = {"LA": "lar", "WAS": "wsh"}
URL = "https://a.espncdn.com/i/teamlogos/{}/500/{}.png"
_uri = {}


def logo_uri(abbr, league="nfl"):
    """data: URI for the team's logo, or None (switch off, unknown team, or download failed)."""
    if not USE_TEAM_LOGOS:
        return None
    key = abbr if league == "nfl" else f"{league}/{abbr}"
    if key in _uri:
        return _uri[key]
    path = os.path.join(CACHE, "logos", f"{key}.png")
    try:
        if not os.path.exists(path):
            os.makedirs(os.path.dirname(path), exist_ok=True)
            data = _get(URL.format(league, (ESPN_ABBR.get(abbr, abbr) if league == "nfl" else abbr).lower()))
            if not data.startswith(b"\x89PNG"):
                raise ValueError("not a PNG")
            with open(path, "wb") as f:
                f.write(data)
        _uri[key] = "data:image/png;base64," + base64.b64encode(open(path, "rb").read()).decode()
    except Exception as e:
        print(f"  ! logo unavailable for {key}: {e}")
        _uri[key] = None
    return _uri[key]
