#!/usr/bin/env python3
"""
prep_photo.py — turn a normal photo into a clean, high-contrast, background-free
grayscale source image that converts well to ASCII art.

Usage:
    python scripts/prep_photo.py source-photo.jpg [output.png]

Pipeline:
    1. Remove the background with rembg so only the subject remains.
    2. Convert to grayscale and boost local contrast with CLAHE
       (contrast-limited adaptive histogram equalization) — this is what
       gives a flatly-lit face real highlights and shadows.
    3. Composite onto pure white so the background maps to the blank end
       of the ASCII ramp (white -> space character).
"""
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
from rembg import remove, new_session

# Use the lightweight u2netp model instead of rembg's newer multi-GB default
# (bria-rmbg) — u2netp is ~4MB and plenty accurate for a bust-shot portrait.
_SESSION = new_session("u2netp")


def prep_photo(input_path: str, output_path: str = "prepped-photo.png") -> str:
    input_path = Path(input_path)
    if not input_path.exists():
        raise FileNotFoundError(f"Could not find {input_path}")

    print(f"Removing background from {input_path.name} ...")
    with open(input_path, "rb") as f:
        input_bytes = f.read()
    output_bytes = remove(input_bytes, session=_SESSION)

    # rembg gives us RGBA with a transparent background
    rgba = Image.open(__import__("io").BytesIO(output_bytes)).convert("RGBA")

    # Crop tightly to the subject (plus a little breathing room) so the
    # portrait isn't mostly wasted whitespace once downsampled to a
    # character grid — a full-frame shot otherwise prints as a tiny
    # smudge in the middle of the ASCII canvas.
    alpha_full = np.array(rgba)[:, :, 3]
    ys, xs = np.where(alpha_full > 10)
    if len(xs) and len(ys):
        pad_x = int((xs.max() - xs.min()) * 0.08)
        pad_y = int((ys.max() - ys.min()) * 0.06)
        left = max(0, xs.min() - pad_x)
        right = min(rgba.width, xs.max() + pad_x)
        top = max(0, ys.min() - pad_y)
        bottom = min(rgba.height, ys.max() + pad_y)
        rgba = rgba.crop((left, top, right, bottom))

    # Composite onto pure white so transparent areas -> white -> blank glyph
    white_bg = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
    composited = Image.alpha_composite(white_bg, rgba).convert("RGB")

    # Convert to grayscale for CLAHE
    gray = cv2.cvtColor(np.array(composited), cv2.COLOR_RGB2GRAY)

    print("Boosting local contrast with CLAHE ...")
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    contrasted = clahe.apply(gray)

    # Re-flatten background to pure white using the alpha mask from rembg,
    # since CLAHE can slightly darken previously-transparent regions.
    alpha = np.array(rgba)[:, :, 3]
    contrasted[alpha < 10] = 255

    out_img = Image.fromarray(contrasted)
    out_img.save(output_path)
    print(f"Wrote {output_path} ({out_img.size[0]}x{out_img.size[1]})")
    return output_path


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/prep_photo.py <source-photo.jpg> [output.png]")
        sys.exit(1)
    src = sys.argv[1]
    dst = sys.argv[2] if len(sys.argv) > 2 else "source-prepped.png"
    prep_photo(src, dst)
