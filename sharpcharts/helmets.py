"""Original helmet artwork in each team's colors (no team logos: the abbreviation sits where a
logo would). Shell / stripe / stripe-edge / facemask / decal colors approximate each team's
current helmet look."""
from html import escape

H = {  # shell, stripe, stripe edge, facemask, decal
    "ARI": ("#F4F4F4", "#97233F", "#000000", "#9A9A9A", "#97233F"),
    "ATL": ("#141414", "#A71930", "#FFFFFF", "#141414", "#A71930"),
    "BAL": ("#241773", "#241773", "#9E7C0C", "#141414", "#FFFFFF"),
    "BUF": ("#F4F4F4", "#C60C30", "#00338D", "#00338D", "#00338D"),
    "CAR": ("#BFC0BF", "#0085CA", "#101820", "#101820", "#0085CA"),
    "CHI": ("#0B162A", "#C83803", "#FFFFFF", "#0B162A", "#FFFFFF"),
    "CIN": ("#FB4F14", "#141414", "#141414", "#141414", "#141414"),
    "CLE": ("#FF3C00", "#311D00", "#FFFFFF", "#311D00", "#FFFFFF"),
    "DAL": ("#8A98A6", "#003594", "#FFFFFF", "#8A98A6", "#003594"),
    "DEN": ("#002244", "#FB4F14", "#FFFFFF", "#002244", "#FB4F14"),
    "DET": ("#B0B7BC", "#0076B6", "#FFFFFF", "#0076B6", "#0076B6"),
    "GB":  ("#FFB612", "#203731", "#FFFFFF", "#203731", "#203731"),
    "HOU": ("#03202F", "#A71930", "#FFFFFF", "#03202F", "#FFFFFF"),
    "IND": ("#F4F4F4", "#002C5F", "#002C5F", "#002C5F", "#002C5F"),
    "JAX": ("#141414", "#006778", "#D7A22A", "#141414", "#D7A22A"),
    "KC":  ("#E31837", "#FFFFFF", "#E31837", "#9A9A9A", "#FFFFFF"),
    "LV":  ("#A5ACAF", "#141414", "#141414", "#141414", "#141414"),
    "LAC": ("#0080C6", "#FFC20E", "#FFFFFF", "#0080C6", "#FFC20E"),
    "LA":  ("#003594", "#FFA300", "#FFA300", "#003594", "#FFA300"),
    "MIA": ("#F4F4F4", "#008E97", "#FC4C02", "#008E97", "#008E97"),
    "MIN": ("#4F2683", "#FFC62F", "#FFFFFF", "#4F2683", "#FFC62F"),
    "NE":  ("#B0B7BC", "#002244", "#C60C30", "#002244", "#002244"),
    "NO":  ("#D3BC8D", "#101820", "#101820", "#101820", "#101820"),
    "NYG": ("#0B2265", "#A71930", "#FFFFFF", "#9A9A9A", "#FFFFFF"),
    "NYJ": ("#125740", "#FFFFFF", "#125740", "#FFFFFF", "#FFFFFF"),
    "PHI": ("#004C54", "#A5ACAF", "#FFFFFF", "#141414", "#A5ACAF"),
    "PIT": ("#141414", "#FFB612", "#FFB612", "#141414", "#FFB612"),
    "SF":  ("#B3995D", "#AA0000", "#FFFFFF", "#AA0000", "#AA0000"),
    "SEA": ("#002244", "#69BE28", "#A5ACAF", "#002244", "#69BE28"),
    "TB":  ("#34302B", "#D50A0A", "#FFFFFF", "#9A9A9A", "#D50A0A"),
    "TEN": ("#0C2340", "#4B92DB", "#C8102E", "#0C2340", "#4B92DB"),
    "WAS": ("#5A1414", "#FFB612", "#FFB612", "#141414", "#FFB612"),
}


SHELL = ("M24 96 C14 52 48 10 102 8 C150 6 180 38 180 78 C180 88 176 96 170 98 L156 99 L152 118 "
         "C148 128 136 132 124 130 L92 126 C78 124 70 116 68 106 C56 112 32 110 24 96 Z")


def helmet(abbr, size=120, facing="right", uid=None):
    shell, stripe, edge, mask, decal = H.get(abbr, ("#3A4A6B", "#FFFFFF", "#FFFFFF", "#9A9A9A", "#FFFFFF"))
    u = uid or f"h{abbr}{facing}{size}"
    flip = ' transform="translate(204 0) scale(-1 1)"' if facing == "left" else ""
    fs = 40 if len(abbr) <= 2 else 33
    return f'''<svg width="{size}" height="{int(size * .7)}" viewBox="0 0 204 144" xmlns="http://www.w3.org/2000/svg">
 <defs>
  <radialGradient id="{u}g" cx="36%" cy="24%" r="80%"><stop offset="0" stop-color="#fff" stop-opacity=".6"/>
   <stop offset=".3" stop-color="#fff" stop-opacity=".1"/><stop offset=".75" stop-color="#000" stop-opacity=".18"/>
   <stop offset="1" stop-color="#000" stop-opacity=".5"/></radialGradient>
  <clipPath id="{u}c"><path d="{SHELL}"/></clipPath>
 </defs>
 <g{flip}>
  <ellipse cx="108" cy="138" rx="80" ry="5" fill="#000" opacity=".4"/>
  <path d="{SHELL}" fill="{shell}"/>
  <g clip-path="url(#{u}c)">
   <path d="M30 40 C62 6 132 -2 186 44" fill="none" stroke="{edge}" stroke-width="22"/>
   <path d="M30 40 C62 6 132 -2 186 44" fill="none" stroke="{stripe}" stroke-width="13"/>
   <path d="M150 99 L182 96 L182 104 L150 106 Z" fill="#000" opacity=".25"/>
   <path d="{SHELL}" fill="url(#{u}g)"/>
  </g>
  <path d="{SHELL}" fill="none" stroke="#000" stroke-opacity=".45" stroke-width="2.5"/>
  <path d="M40 34 C60 18 92 12 120 14" fill="none" stroke="#fff" stroke-opacity=".55" stroke-width="4" stroke-linecap="round"/>
  <circle cx="104" cy="90" r="7.5" fill="#000" opacity=".6"/><circle cx="104" cy="90" r="3.5" fill="#fff" opacity=".25"/>
  <g fill="none" stroke-linecap="round" stroke-linejoin="round">
   <g stroke="#000" stroke-opacity=".55" stroke-width="10">
    <path d="M174 70 L198 72 L198 116 L152 120"/><path d="M174 90 L198 92"/><path d="M186 71 L186 118"/><path d="M152 120 L150 106"/></g>
   <g stroke="{mask}" stroke-width="6">
    <path d="M174 70 L198 72 L198 116 L152 120"/><path d="M174 90 L198 92"/><path d="M186 71 L186 118"/><path d="M152 120 L150 106"/></g>
   <g stroke="#fff" stroke-opacity=".35" stroke-width="1.6">
    <path d="M175 68.5 L197 70.5"/><path d="M175 88.5 L197 90.5"/></g>
  </g>
  <path d="M112 118 Q132 132 156 124" stroke="#000" stroke-opacity=".55" stroke-width="4" fill="none"/>
 </g>
 <text x="{92 if facing == 'right' else 112}" y="70" text-anchor="middle" font-family="Barlow Condensed, Arial Narrow, sans-serif"
   font-weight="800" font-size="{fs}" fill="{decal}" stroke="#000" stroke-opacity=".5" stroke-width="2.5"
   paint-order="stroke" letter-spacing="1">{escape(abbr)}</text>
</svg>'''


def badge(abbr, size=120, fallback_color="#3A4A6B"):
    """Clean broadcast-style team badge: main color disc, second-color ring, crisp abbreviation."""
    shell, stripe, edge, mask, decal = H.get(abbr, (fallback_color, "#FFFFFF", "#FFFFFF", "#FFFFFF", "#FFFFFF"))
    # pick the darker/more saturated of shell vs stripe as the disc so the text pops
    lum = lambda c: sum(int(c[i:i + 2], 16) * w for i, w in ((1, .299), (3, .587), (5, .114)))
    disc, ring = (shell, stripe) if lum(shell) < lum(stripe) else (stripe, shell)
    if ring.lower() == disc.lower():
        ring = edge                       # e.g. Baltimore: purple disc gets its gold accent ring
    text = "#FFFFFF" if lum(disc) < 150 else "#111111"
    rgb = [int(ring[i:i + 2], 16) for i in (1, 3, 5)]
    grey = max(rgb) - min(rgb) < 40
    if text == "#FFFFFF" and lum(ring) > 140 and not grey:
        text = ring                       # e.g. gold on green, orange on navy; never grey/silver text
    fs = 46 if len(abbr) <= 2 else 38
    return f'''<svg width="{size}" height="{size}" viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg">
 <circle cx="60" cy="60" r="56" fill="{ring}"/><circle cx="60" cy="60" r="47" fill="{disc}"/>
 <circle cx="60" cy="60" r="47" fill="none" stroke="#000" stroke-opacity=".25" stroke-width="2"/>
 <text x="60" y="{60 + fs * .36:.0f}" text-anchor="middle" font-family="Barlow Condensed, Arial Narrow, sans-serif"
   font-weight="800" font-size="{fs}" fill="{text}" letter-spacing="1">{escape(abbr)}</text></svg>'''
