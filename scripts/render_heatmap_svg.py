#!/usr/bin/env python3
"""Render data/contributions.json as an animated contribution heatmap SVG.

Cells reveal along the diagonal (week + weekday), so the grid sweeps in from the
top-left rather than appearing all at once.
"""
import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "contributions.json"
OUT = ROOT / "contrib-heatmap.svg"

CELL = 12
GAP = 3
PITCH = CELL + GAP
LEFT = 32           # weekday label gutter
TOP = 60            # title + month labels
BOTTOM = 34         # legend row
RIGHT = 14

BG = "#0d1117"
FRAME = "#21262d"
TEXT = "#7d8590"
BRIGHT = "#e6edf3"
LEVELS = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]
MONTHS = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()
WEEKDAYS = {1: "Mon", 3: "Wed", 5: "Fri"}


def main() -> None:
    if not DATA.exists():
        raise SystemExit("missing data/contributions.json - run fetch_contributions.py")

    payload = json.loads(DATA.read_text())
    days, stats = payload["days"], payload["stats"]

    # Lay out into columns keyed on the Sunday-start week, matching GitHub.
    first = date.fromisoformat(days[0]["date"])
    origin = first.toordinal() - ((first.weekday() + 1) % 7)

    cells = []
    for d in days:
        off = date.fromisoformat(d["date"]).toordinal() - origin
        cells.append((off // 7, off % 7, d))

    weeks = max(c[0] for c in cells) + 1
    w = LEFT + weeks * PITCH + RIGHT
    h = TOP + 7 * PITCH + BOTTOM

    step = 0.012        # per-diagonal delay
    fade = 0.5
    hold = 3.4
    total = round((weeks + 7) * step + fade + hold, 2)
    pct_in = 100 * fade / total
    pct_out = 100 * (total - 0.55) / total

    rects, months, seen = [], [], set()
    for wk, wd, d in cells:
        x = LEFT + wk * PITCH
        y = TOP + wd * PITCH
        delay = round((wk + wd) * step, 3)
        n = d["count"]
        label = f"{n} contribution{'' if n == 1 else 's'} on {d['date']}"
        rects.append(
            f'<rect class="d" style="animation-delay:{delay}s" x="{x}" y="{y}" '
            f'width="{CELL}" height="{CELL}" rx="2.5" fill="{LEVELS[d["level"]]}">'
            f"<title>{label}</title></rect>"
        )

        # One label per month, at the first week that month owns a Sunday. When
        # two would collide the later one wins, which drops the leading partial
        # month rather than the full one behind it.
        dt = date.fromisoformat(d["date"])
        mo, key = dt.month, (dt.year, dt.month)
        if key not in seen and wd == 0:
            seen.add(key)
            if months and x - months[-1][0] < 3 * PITCH:
                months[-1] = (x, MONTHS[mo - 1])
            else:
                months.append((x, MONTHS[mo - 1]))

    month_labels = "\n".join(
        f'    <text class="lbl" x="{x}" y="{TOP - 10}">{name}</text>'
        for x, name in months
    )
    day_labels = "\n".join(
        f'    <text class="lbl" x="{LEFT - 7}" y="{TOP + i * PITCH + CELL - 2.5}" '
        f'text-anchor="end">{name}</text>'
        for i, name in WEEKDAYS.items()
    )

    legend_x = w - RIGHT - 5 * PITCH - 74
    legend_y = h - BOTTOM + 12
    legend = "\n".join(
        f'    <rect x="{legend_x + 26 + i * PITCH}" y="{legend_y}" width="{CELL}" '
        f'height="{CELL}" rx="2.5" fill="{c}"/>'
        for i, c in enumerate(LEVELS)
    )

    total_c = stats["total"]
    summary = (
        f'{total_c:,} contributions  ·  {stats["active_days"]} active days  ·  '
        f'streak {stats["current_streak"]} (best {stats["longest_streak"]})'
    )

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{summary}">
  <title>{summary}</title>
  <style>
    text {{ font-family: 'SFMono-Regular', 'JetBrains Mono', Consolas, 'Liberation Mono', monospace; }}
    .lbl {{ font-size: 9.5px; fill: {TEXT}; }}
    .hd  {{ font-size: 12px; fill: {BRIGHT}; }}
    .sub {{ font-size: 10px; fill: {TEXT}; }}
    .d   {{ opacity: 0; animation: pop {total}s ease-out infinite; }}
    @keyframes pop {{
      0%              {{ opacity: 0; }}
      {pct_in:.3f}%   {{ opacity: 1; }}
      {pct_out:.3f}%  {{ opacity: 1; }}
      100%            {{ opacity: 0.14; }}
    }}
  </style>
  <rect width="{w}" height="{h}" rx="8" fill="{BG}"/>
  <rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="8" fill="none" stroke="{FRAME}"/>
  <text class="hd" x="{LEFT - 7}" y="21">{total_c:,} contributions in the last year</text>
  <text class="sub" x="{LEFT - 7}" y="36">{stats["active_days"]} active days · current streak {stats["current_streak"]} · longest {stats["longest_streak"]} · best day {stats["max_day"]["count"]}</text>
{month_labels}
{day_labels}
  <g>
{chr(10).join("    " + r for r in rects)}
  </g>
  <text class="lbl" x="{legend_x}" y="{legend_y + CELL - 2.5}">Less</text>
{legend}
  <text class="lbl" x="{legend_x + 26 + 5 * PITCH + 4}" y="{legend_y + CELL - 2.5}">More</text>
  <text class="lbl" x="{LEFT - 7}" y="{h - 9}">updated {payload["generated"]}</text>
</svg>
"""
    OUT.write_text(svg)
    print(f"wrote {OUT.name}: {weeks} weeks, {w}x{h}px, {total}s loop")


if __name__ == "__main__":
    main()
