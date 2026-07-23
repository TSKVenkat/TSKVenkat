#!/usr/bin/env python3
"""Render the neofetch-style info card that sits beside the ASCII portrait.

Rows are plain key/value pairs; each one fades and slides in on a stagger so the
card assembles itself line by line. Edit PROFILE below to change the content --
the contributions line is filled in from data/contributions.json at render time.
"""
import json
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "contributions.json"
OUT = ROOT / "info-card.svg"

HANDLE = "venkat"
HOST = "github"

PROFILE = [
    ("Location", "Chennai, Tamil Nadu, India"),
    ("Member since", "September 2024"),
    ("Languages", "TypeScript 71% · Python 19% · JS 3%"),
    ("Repos", "59 public"),
    ("Focus", "fintech infra · privacy-preserving systems"),
    ("Also", "AI dev tooling · design systems · CLIs"),
    ("Building", "pramana · sentra · openwiki · pulse-ui"),
    ("Editor", "whatever has a terminal in it"),
]

W = 490
PAD = 22
LINE = 25  # tuned so the card renders the same height as the ASCII portrait
FONT = 11.5

BG = "#0d1117"
FRAME = "#21262d"
KEY = "#39d353"
VAL = "#c9d1d9"
DIM = "#7d8590"
ACCENT = "#9be9a8"
SWATCHES = ["#0e4429", "#006d32", "#26a641", "#39d353", "#9be9a8", "#c9d1d9"]


def main() -> None:
    rows = list(PROFILE)

    if DATA.exists():
        s = json.loads(DATA.read_text())["stats"]
        rows.insert(
            3,
            (
                "Contributions",
                f'{s["total"]:,} in the last year · {s["active_days"]} active days',
            ),
        )
        rows.insert(4, ("Streak", f'{s["current_streak"]} days · best {s["longest_streak"]}'))

    title_y = PAD + 14
    rule_y = title_y + 12
    body_y = rule_y + 24
    palette_y = body_y + len(rows) * LINE + 12
    h = round(palette_y + 34)

    per = 0.11
    hold = 3.6
    total = round(len(rows) * per + 0.55 + hold, 2)
    pct_in = 100 * 0.55 / total
    pct_out = 100 * (total - 0.6) / total

    key_w = max(len(k) for k, _ in rows)
    lines = []
    for i, (k, v) in enumerate(rows):
        y = body_y + i * LINE
        delay = round(0.25 + i * per, 3)
        lines.append(
            f'    <g class="row" style="animation-delay:{delay}s">'
            f'<text class="k" x="{PAD}" y="{y}">{escape(k.ljust(key_w))}</text>'
            f'<text class="s" x="{PAD + key_w * FONT * 0.6 + 6:.1f}" y="{y}">:</text>'
            f'<text class="v" x="{PAD + key_w * FONT * 0.6 + 17:.1f}" y="{y}">{escape(v)}</text>'
            f"</g>"
        )

    swatches = "\n".join(
        f'    <rect x="{PAD + i * 22}" y="{palette_y}" width="16" height="9" rx="2" fill="{c}"/>'
        for i, c in enumerate(SWATCHES)
    )

    nl = "\n"
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h}" viewBox="0 0 {W} {h}" role="img" aria-label="Profile info card for {HANDLE}">
  <title>{HANDLE}@{HOST}</title>
  <style>
    text {{
      font-family: 'SFMono-Regular', 'JetBrains Mono', Consolas, 'Liberation Mono', monospace;
      font-size: {FONT}px;
      white-space: pre;
    }}
    .t {{ font-size: 13px; fill: {ACCENT}; font-weight: 600; }}
    .k {{ fill: {KEY}; }}
    .s {{ fill: {DIM}; }}
    .v {{ fill: {VAL}; }}
    .f {{ font-size: 10px; fill: {DIM}; }}
    .row {{ opacity: 0; animation: slide {total}s ease-out infinite; }}
    @keyframes slide {{
      0%             {{ opacity: 0; transform: translateX(-9px); }}
      {pct_in:.3f}%  {{ opacity: 1; transform: translateX(0); }}
      {pct_out:.3f}% {{ opacity: 1; transform: translateX(0); }}
      100%           {{ opacity: 0; transform: translateX(0); }}
    }}
    .cursor {{ animation: blink 1.06s steps(1) infinite; fill: {KEY}; }}
    @keyframes blink {{ 0%,49% {{ opacity: 1; }} 50%,100% {{ opacity: 0; }} }}
  </style>
  <rect width="{W}" height="{h}" rx="8" fill="{BG}"/>
  <rect x="0.5" y="0.5" width="{W - 1}" height="{h - 1}" rx="8" fill="none" stroke="{FRAME}"/>
  <text class="t" x="{PAD}" y="{title_y}">{HANDLE}<tspan fill="{DIM}">@</tspan>{HOST}</text>
  <rect x="{PAD}" y="{rule_y}" width="{W - PAD * 2}" height="1" fill="{FRAME}"/>
{nl.join(lines)}
{swatches}
  <text class="f" x="{PAD}" y="{h - PAD + 4}">press any key to continue</text>
  <rect class="cursor" x="{W - PAD - 7}" y="{h - PAD - 4}" width="7" height="2.5"/>
</svg>
"""
    OUT.write_text(svg)
    print(f"wrote {OUT.name}: {len(rows)} rows, {W}x{h}px, {total}s loop")


if __name__ == "__main__":
    main()
