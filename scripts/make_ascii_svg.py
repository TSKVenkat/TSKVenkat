#!/usr/bin/env python3
"""Turn the prepped portrait into an animated ASCII-art SVG.

The image is downsampled to a character grid and each cell picks a glyph from a
density ramp keyed on brightness. Rows then wipe in left-to-right, top-to-bottom,
so the portrait "types" itself onto the page.
"""
from pathlib import Path
from xml.sax.saxutils import escape

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "source-prepped.png"
OUT = ROOT / "avi-ascii.svg"

COLS = 92
FONT = 6.6           # px
CELL_W = FONT * 0.6  # monospace advance width
CELL_H = FONT * 1.0
PAD = 10

# Sparse -> dense. Index by darkness, so white background lands on a space.
RAMP = " .`'\",:;!~+=*achkbdpqwmZO0QLCJUYXzcvunxr#MW&8%B@$"

BG = "#0d1117"
DIM = "#1f6f43"
MID = "#39d353"
HOT = "#9be9a8"


def ascii_grid(img: Image.Image) -> tuple[list[str], np.ndarray]:
    aspect = img.height / img.width
    rows = max(1, round(COLS * aspect * (CELL_W / CELL_H)))

    grid = np.asarray(
        img.convert("L").resize((COLS, rows), Image.LANCZOS), dtype=np.float32
    )

    # Stretch the used range so the ramp is spent on the subject, not the
    # white backdrop the prep step baked in.
    lo, hi = np.percentile(grid, 2), np.percentile(grid, 98)
    norm = np.clip((grid - lo) / max(hi - lo, 1e-6), 0, 1)

    darkness = 1.0 - norm
    idx = np.clip((darkness * len(RAMP)).astype(int), 0, len(RAMP) - 1)
    lines = ["".join(RAMP[i] for i in row) for row in idx]
    return lines, darkness


def main() -> None:
    if not SRC.exists():
        raise SystemExit(f"missing {SRC.name} - run prep_photo.py first")

    lines, darkness = ascii_grid(Image.open(SRC))
    rows = len(lines)
    w = round(COLS * CELL_W) + PAD * 2
    h = round(rows * CELL_H) + PAD * 2

    per_row = 0.055           # stagger between rows
    wipe = 0.42               # how long one row takes to sweep across
    total = round(rows * per_row + wipe + 2.2, 2)

    clips, texts, css = [], [], []
    for i, line in enumerate(lines):
        y = PAD + (i + 0.85) * CELL_H
        delay = round(i * per_row, 3)

        clips.append(
            f'<clipPath id="c{i}"><rect class="w" style="animation-delay:{delay}s" '
            f'x="{PAD}" y="{y - CELL_H}" width="{w}" height="{CELL_H * 1.4:.2f}"/></clipPath>'
        )

        # Colour the row by its mean ink: dense rows read hotter.
        ink = float(darkness[i].mean())
        fill = HOT if ink > 0.55 else MID if ink > 0.25 else DIM
        texts.append(
            f'<text clip-path="url(#c{i})" x="{PAD}" y="{y:.2f}" fill="{fill}">'
            f"{escape(line)}</text>"
        )

    css.append(
        f"""
    text {{
      font-family: 'SFMono-Regular', 'JetBrains Mono', Consolas, 'Liberation Mono', monospace;
      font-size: {FONT}px;
      letter-spacing: 0;
      white-space: pre;
      dominant-baseline: alphabetic;
    }}
    .w {{
      transform-box: fill-box;
      transform-origin: left center;
      transform: scaleX(0);
      animation: wipe {total}s linear infinite;
    }}
    @keyframes wipe {{
      0%   {{ transform: scaleX(0); }}
      {100 * wipe / total:.3f}% {{ transform: scaleX(1); }}
      {100 * (total - 1.0) / total:.3f}% {{ transform: scaleX(1); }}
      100% {{ transform: scaleX(1); }}
    }}
    .cursor {{ animation: blink 1.06s steps(1) infinite; }}
    @keyframes blink {{ 0%,49% {{ opacity: 1; }} 50%,100% {{ opacity: 0; }} }}
    .frame {{ fill: none; stroke: #21262d; stroke-width: 1; }}
    """
    )

    nl = "\n"
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="ASCII-art portrait">
  <title>whoami</title>
  <style>{"".join(css)}</style>
  <rect width="{w}" height="{h}" rx="8" fill="{BG}"/>
  <rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="8" class="frame"/>
  <defs>
{nl.join("    " + c for c in clips)}
  </defs>
  <g>
{nl.join("    " + t for t in texts)}
  </g>
  <rect class="cursor" x="{PAD}" y="{h - PAD - 6}" width="{CELL_W:.2f}" height="5" fill="{MID}"/>
</svg>
"""
    OUT.write_text(svg)
    print(f"wrote {OUT.name}: {COLS}x{rows} chars, {w}x{h}px, {total}s loop")


if __name__ == "__main__":
    main()
