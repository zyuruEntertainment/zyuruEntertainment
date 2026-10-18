
import json
import urllib.request
from datetime import date, timedelta
from pathlib import Path
from xml.sax.saxutils import escape

USERNAME = "zyuruEntertainment"
YEAR = date.today().year
TODAY = date.today()

OUTPUT = Path("Assets/svg/activity.svg")
API_URL = (
    f"https://github-contributions-api.jogruber.de/v4/"
    f"{USERNAME}?y={YEAR}"
)

COLORS = [
    "#161b22",
    "#0e4429",
    "#006d32",
    "#26a641",
    "#39d353",
]

# Fetch real contribution data.
request = urllib.request.Request(
    API_URL,
    headers={"User-Agent": "ZyuruActivitySVG/1.0"}
)

try:
    with urllib.request.urlopen(request, timeout=30) as response:
        data = json.loads(response.read().decode("utf-8"))
except Exception as exc:
    raise SystemExit(f"Failed to fetch GitHub data: {exc}")

if "contributions" not in data:
    raise SystemExit(f"Unexpected API response: {data}")

contributions = {
    item["date"]: item
    for item in data["contributions"]
}

# Build a Sunday-first calendar, matching GitHub's layout.
jan_first = date(YEAR, 1, 1)
first_sunday = jan_first - timedelta(
    days=(jan_first.weekday() + 1) % 7
)

weeks = ((TODAY - first_sunday).days // 7) + 1
width = 52 + weeks * 13
height = 190

cells = []
particles = []

for day_offset in range((TODAY - first_sunday).days + 1):
    day = first_sunday + timedelta(days=day_offset)

    # Leave days before January 1 blank.
    if day < jan_first:
        continue

    column = (day - first_sunday).days // 7
    weekday = (day.weekday() + 1) % 7

    x = 26 + column * 13
    y = 48 + weekday * 13

    item = contributions.get(day.isoformat(), {})
    count = int(item.get("count", 0))
    level = max(0, min(4, int(item.get("level", 0))))
    color = COLORS[level]

    # Stagger each cell's entrance.
    delay = day_offset * 0.012

    cells.append(f"""
      <g>
        <rect x="{x}" y="{y}" width="10" height="10"
              rx="2" fill="{color}" opacity="0">
          <title>{day.isoformat()}: {count} contributions</title>
          <animate attributeName="opacity"
            values="0;1;1;0;0"
            keyTimes="0;.12;.60;.72;1"
            dur="8s" begin="{delay:.3f}s"
            repeatCount="indefinite"/>
        </rect>
      </g>
    """)

    # Add a small burst around active contribution cells.
    if count > 0:
        for j, (dx, dy) in enumerate([
            (-12, -10), (13, -8), (-9, 13), (12, 12)
        ]):
            particles.append(f"""
              <circle cx="{x + 5}" cy="{y + 5}"
                      r="1.6" fill="{color}" opacity="0">
                <animate attributeName="opacity"
                  values="0;0;1;0"
                  keyTimes="0;.60;.65;1"
                  dur="8s" begin="{delay:.3f}s"
                  repeatCount="indefinite"/>
                <animate attributeName="cx"
                  values="{x + 5};{x + 5};{x + 5 + dx};{x + 5 + dx * 1.5}"
                  keyTimes="0;.60;.65;1"
                  dur="8s" begin="{delay:.3f}s"
                  repeatCount="indefinite"/>
                <animate attributeName="cy"
                  values="{y + 5};{y + 5};{y + 5 + dy};{y + 5 + dy * 1.5}"
                  keyTimes="0;.60;.65;1"
                  dur="8s" begin="{delay:.3f}s"
                  repeatCount="indefinite"/>
              </circle>
            """)

OUTPUT.parent.mkdir(parents=True, exist_ok=True)

svg = f"""<svg xmlns="http://www.w3.org/2000/svg"
  width="{width}" height="{height}"
  viewBox="0 0 {width} {height}">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#0d1117"/>
      <stop offset="1" stop-color="#101820"/>
    </linearGradient>
    <pattern id="grid" width="13" height="13"
             patternUnits="userSpaceOnUse">
      <rect width="10" height="10" rx="2" fill="#21262d"/>
    </pattern>
    <filter id="glow" x="-100%" y="-100%"
            width="300%" height="300%">
      <feGaussianBlur stdDeviation="1.5" result="blur"/>
      <feMerge>
        <feMergeNode in="blur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>
  </defs>

  <rect width="100%" height="100%" rx="12" fill="url(#bg)"/>
  <rect x=".5" y=".5" width="{width-1}" height="{height-1}"
        rx="11" fill="none" stroke="#30363d"/>

  <text x="26" y="27" fill="#e6edf3"
        font-family="monospace" font-size="13"
        font-weight="bold">
    {escape(USERNAME.upper())} / {YEAR} CONTRIBUTIONS
  </text>

  <circle cx="{width-47}" cy="22" r="4" fill="#39d353">
    <animate attributeName="opacity"
      values="1;.3;1" dur="1.5s"
      repeatCount="indefinite"/>
  </circle>

  <rect x="26" y="48" width="{weeks*13}" height="91"
        fill="url(#grid)"/>

  <g id="contributions">
    {''.join(cells)}
  </g>

  <g id="particles" filter="url(#glow)">
    {''.join(particles)}
  </g>

  <text x="26" y="169" fill="#8b949e"
        font-family="monospace" font-size="10">
    YEAR TO DATE · UPDATED {TODAY.isoformat()}
  </text>

  <text x="{width-26}" y="169" fill="#39d353"
        font-family="monospace" font-size="10"
        text-anchor="end">LOOP ∞</text>
</svg>
"""

OUTPUT.write_text(svg, encoding="utf-8")

print(f"Generated: {OUTPUT}")
print(f"Year: {YEAR}")
print(f"Days rendered: {len(cells)}")
print(f"Active days: {sum(1 for item in contributions.values() if item.get('count', 0) > 0 and item['date'] <= TODAY.isoformat() and item['date'] >= jan_first.isoformat())}")
