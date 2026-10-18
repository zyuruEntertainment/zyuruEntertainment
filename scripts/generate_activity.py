
import json
import urllib.request
import random
from datetime import date, timedelta
from pathlib import Path
from xml.sax.saxutils import escape

USERNAME = "zyuruEntertainment"
OUTPUT = Path("Assets/svg/activity.svg")

API = (
    f"https://github-contributions-api.jogruber.de/v4/"
    f"{USERNAME}?y=last"
)

request = urllib.request.Request(
    API,
    headers={"User-Agent": "GitHub-Activity-SVG"}
)

with urllib.request.urlopen(request, timeout=30) as response:
    data = json.loads(response.read().decode("utf-8"))

contributions = {
    item["date"]: item["count"]
    for item in data["contributions"]
}

today = date.today()
start = today - timedelta(days=363)
start -= timedelta(days=(start.weekday() + 1) % 7)

colors = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]
cells = []
particles = []
random.seed(42)

for i in range(53 * 7):
    day = start + timedelta(days=i)
    if day > today:
        continue

    count = contributions.get(day.isoformat(), 0)
    level = 0 if count == 0 else min(4, 1 + count // 3)
    x = (i // 7) * 12
    y = (i % 7) * 12

    delay = (i % 53) * 0.035 + (i % 7) * 0.025
    color = colors[level]

    cells.append(f"""
    <g transform="translate({x},{y})">
      <rect width="9" height="9" rx="2"
            fill="{color}" opacity="0">
        <title>{day.isoformat()}: {count} contributions</title>
        <animate attributeName="opacity"
          values="0;1;1;0;0"
          keyTimes="0;0.12;0.62;0.78;1"
          dur="8s" begin="{delay:.3f}s"
          repeatCount="indefinite"/>
        <animateTransform attributeName="transform"
          type="scale" values=".1;1;1;.01;.01"
          keyTimes="0;0.12;0.62;0.78;1"
          dur="8s" begin="{delay:.3f}s"
          repeatCount="indefinite"
          additive="replace"/>
      </rect>
    </g>
    """)

    if count > 0:
        for _ in range(min(level + 1, 4)):
            dx = random.randint(-15, 15)
            dy = random.randint(-15, 15)
            particles.append(f"""
            <circle cx="{x + 4.5}" cy="{y + 4.5}"
                    r="{random.uniform(1, 2):.1f}"
                    fill="{color}" opacity="0">
              <animate attributeName="opacity"
                values="0;0;1;0;0"
                keyTimes="0;.60;.64;.80;1"
                dur="8s" begin="{delay:.3f}s"
                repeatCount="indefinite"/>
              <animateTransform attributeName="transform"
                type="translate"
                values="0 0;0 0;{dx} {dy};{dx * 1.3} {dy * 1.3};0 0"
                keyTimes="0;.60;.64;.80;1"
                dur="8s" begin="{delay:.3f}s"
                repeatCount="indefinite"/>
            </circle>
            """)

OUTPUT.parent.mkdir(parents=True, exist_ok=True)

svg = f"""<svg xmlns="http://www.w3.org/2000/svg"
     width="700" height="140" viewBox="0 0 700 140">
  <rect width="700" height="140" rx="12" fill="#0d1117"/>
  <text x="20" y="25" fill="#e6edf3"
        font-family="monospace" font-size="13">
    {escape(USERNAME)} / CONTRIBUTION ACTIVITY
  </text>
  <g transform="translate(20 38)">
    {''.join(cells)}
  </g>
  <g transform="translate(20 38)">
    {''.join(particles)}
  </g>
  <text x="20" y="130" fill="#8b949e"
        font-family="monospace" font-size="10">
    LIVE DATA SNAPSHOT · AUTO GENERATED
  </text>
</svg>
"""

OUTPUT.write_text(svg, encoding="utf-8")
print(f"Generated {OUTPUT} with {len(cells)} contribution cells")
