#!/usr/bin/env python3
"""Prep a portrait for ASCII conversion.

Removes the background, boosts contrast, and composites onto flat white so the
density ramp in make_ascii_svg.py maps subject detail instead of scenery.

    python scripts/prep_photo.py source-photo.jpg   ->  source-prepped.png
"""
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageEnhance
from rembg import remove

TARGET = 900  # working resolution before downsampling to characters


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 1

    src = Path(sys.argv[1])
    if not src.exists():
        print(f"no such file: {src}")
        return 1

    img = Image.open(src).convert("RGB")

    # Scale to a consistent working size so contrast settings are predictable.
    scale = TARGET / max(img.size)
    if scale < 1:
        img = img.resize(
            (round(img.width * scale), round(img.height * scale)), Image.LANCZOS
        )

    cut = remove(img)  # RGBA, background alpha -> 0

    # CLAHE on luminance: local contrast survives downsampling far better than a
    # global curve, which is what keeps the eyes//jawline readable at 88 columns.
    rgb = np.array(cut.convert("RGB"))
    lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB)
    lab[..., 0] = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8)).apply(lab[..., 0])
    rgb = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)

    boosted = Image.fromarray(rgb)
    boosted = ImageEnhance.Contrast(boosted).enhance(1.35)
    boosted = ImageEnhance.Brightness(boosted).enhance(1.05)
    boosted.putalpha(cut.getchannel("A"))

    # Composite on white, then crop to the subject with a small margin.
    white = Image.new("RGB", boosted.size, (255, 255, 255))
    white.paste(boosted, (0, 0), boosted)

    bbox = cut.getchannel("A").point(lambda a: 255 if a > 12 else 0).getbbox()
    if bbox:
        pad = round(0.04 * max(white.size))
        white = white.crop(
            (
                max(bbox[0] - pad, 0),
                max(bbox[1] - pad, 0),
                min(bbox[2] + pad, white.width),
                min(bbox[3] + pad, white.height),
            )
        )

    out = src.with_name(src.stem.replace("-photo", "") + "-prepped.png")
    white.save(out)
    print(f"wrote {out}  ({white.width}x{white.height})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
