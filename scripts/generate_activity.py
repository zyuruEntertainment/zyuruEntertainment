
import re
import urllib.request
from datetime import date
from html import unescape
from pathlib import Path
from xml.sax.saxutils import escape

USERNAME = "zyuruEntertainment"
YEAR = date.today().year
TODAY = date.today()

START = date(YEAR, 1, 1)
URL = (
    f"https://github.com/users/{USERNAME}/contributions"
    f"?from={START.isoformat()}&to={TODAY.isoformat()}"
)
OUTPUT = Path("Assets/svg/activity.svg")

request = urllib.request.Request(
    URL,
    headers={"User-Agent": "Mozilla/5.0"}
)

with urllib.request.urlopen(request, timeout=30) as response:
    page = response.read().decode("utf-8")

# Read the actual dates, contribution counts and intensity
# levels from GitHub's rendered contribution calendar.
cells = []

for tag in re.findall(r"<rect\b[^>]*>", page):
    date_match = re.search(r'data-date="([^"]+)"', tag)
    count_match = re.search(r'data-count="(\d+)"', tag)
    level_match = re.search(r'data-level="(\d+)"', tag)

    if not date_match or not count_match:
        continue

    day = date.fromisoformat(date_match.group(1))

    if day < START or day > TODAY:
        continue

    count = int(count_match.group(1))
    level = int(level_match.group(1)) if level_match else 0
    cells.append((day, count, max(0, min(4, level))))

if not cells:
    raise RuntimeError(
        "GitHub calendar could not be parsed. "
        "The page format may have changed."
    )

# Sunday-first calendar columns, matching GitHub's layout.
first_sunday = START.toordinal() - (
    START.weekday() + 1
) % 7

palette = [
    "#161b22",
    "#0e4429",
    "#006d32",
    "#26a641",
    "#39d353",
]

rects = []
particles = []

for day, count, level in cells:
    column = (day.toordinal() - first_sunday) // 7
    weekday = (day.weekday() + 1) % 7

    x = column * 13
    y = weekday * 13
    color = palette[level]
    delay = column * 0.035 + weekday * 0.025

    rects.append(f"""
      <g transform="translate({x},{y})">
        <rect width="10" height="10" rx="2"
              fill="{color}" opacity="0">
          <title>{day.isoformat()}: {count} contributions</title>
          <animate attributeName="opacity"
            values="0;1;1;0;0"
            keyTimes="0;.12;.62;.78;1"
            dur="8s" begin="{delay:.3f}s"
            repeatCount="indefinite"/>
          <animateTransform attributeName="transform"
            type="scale" additive="sum"
            values=".1;.1;1;1;.01"
            keyTimes="0;.05;.12;.62;.78"
            dur="8s" begin="{delay:.3f}s"
            repeatCount="indefinite"/>
        </rect>
      </g>
    """)

    if count:
        for j in range(min(level + 1, 4)):
            dx = (-1 if j % 2 else 1) * (5 + j * 3)
            dy = (-1 if j < 2 else 1) * (6 + j * 2)

            particles.append(f"""
              <circle cx="{x + 5}" cy="{y + 5}"
                      r="1.7" fill="{color}" opacity="0">
                <animate attributeName="opacity"
                  values="0;0;1;0;0"
                  keyTimes="0;.62;.66;.82;1"
                  dur="8s" begin="{delay:.3f}s"
                  repeatCount="indefinite"/>
                <animateTransform attributeName="transform"
                  type="translate"
                  values="0 0;0 0;{dx} {dy};{dx * 1.5} {dy * 1.5}"
                  keyTimes="0;.62;.66;.82"
                  dur="8s" begin="{delay:.3f}s"
                  repeatCount="indefinite"/>
              </circle>
            """)

width = ((TODAY.toordinal() - first_sunday) // 7 + 1) * 13 + 8

svg = f"""<svg xmlns="http://www.w3.org/2000/svg"
  width="{width + 32}" height="150"
  viewBox="0 0 {width + 32} 150">
  <rect width="100%" height="100%" rx="10" fill="#0d1117"/>

  <text x="16" y="23" fill="#e6edf3"
        font-family="monospace" font-size="13">
    {escape(USERNAME)} / {YEAR} CONTRIBUTIONS
  </text>

  <g transform="translate(16 34)">
    {''.join(rects)}
    {''.join(particles)}
  </g>

  <text x="16" y="140" fill="#8b949e"
        font-family="monospace" font-size="10">
    YEAR TO DATE · UPDATED {TODAY.isoformat()}
  </text>
</svg>
"""

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
OUTPUT.write_text(svg, encoding="utf-8")

print(f"Generated {OUTPUT}: {len(cells)} days")
