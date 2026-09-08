#!/usr/bin/env python3
"""
make_ascii_svg.py — convert a prepped grayscale photo into a monochrome ASCII
portrait that "types" itself in row by row, as a self-contained animated SVG.

Usage:
    python scripts/make_ascii_svg.py [source-prepped.png] [avi-ascii.svg]

Design choices (deliberate, don't "fix" these):
    - Monochrome. One light-gray fill. Per-character rainbow coloring is
      exactly what makes most ASCII portraits look like noisy static.
    - High contrast in / low contrast out. A busy background washes out to
      the space glyph so only the subject actually prints.
    - Prints once and freezes. No looping — it's a portrait, not a gif.
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image

# bright (sparse) -> dark (dense); leading space clears the background to nothing
RAMP = " .`:-=+*cs#%@"

GRID_COLS = 100
GRID_ROWS = 53
FONT_SIZE = 9
CHAR_W = FONT_SIZE * 0.6      # monospace advance width approximation
LINE_H = FONT_SIZE * 1.0
FILL_COLOR = "#adbac7"        # single light-gray tone — no rainbow
BG_COLOR = "transparent"
ROW_STAGGER = 0.045           # seconds between each row starting its wipe
ROW_DURATION = 0.5            # seconds for a single row to fully wipe in


def image_to_ascii_rows(path: str, cols: int, rows: int) -> list[str]:
    img = Image.open(path).convert("L")
    # Characters are taller than wide, so undersample rows relative to cols
    img = img.resize((cols, rows), Image.LANCZOS)
    arr = np.array(img, dtype=np.float32) / 255.0  # 0 (black) .. 1 (white)

    ramp_len = len(RAMP)
    ascii_rows = []
    for r in range(rows):
        line_chars = []
        for c in range(cols):
            brightness = arr[r, c]
            # brightness 1.0 (white) -> index 0 (space); 0.0 (black) -> last (densest)
            idx = int((1.0 - brightness) * (ramp_len - 1))
            idx = max(0, min(ramp_len - 1, idx))
            line_chars.append(RAMP[idx])
        ascii_rows.append("".join(line_chars).rstrip() or " ")
    return ascii_rows


def escape_xml(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def build_svg(ascii_rows: list[str], cols: int) -> str:
    width = int(cols * CHAR_W) + 20
    height = int(len(ascii_rows) * LINE_H) + 20

    row_groups = []
    for i, row_text in enumerate(ascii_rows):
        row_width = len(row_text) * CHAR_W
        begin_time = round(i * ROW_STAGGER, 3)
        clip_id = f"clip-row-{i}"
        safe_text = escape_xml(row_text) if row_text.strip() else " "

        row_groups.append(f'''
    <clipPath id="{clip_id}">
      <rect x="0" y="{i * LINE_H - FONT_SIZE}" width="0" height="{LINE_H + 2}">
        <animate attributeName="width" from="0" to="{row_width + 4}"
                 begin="{begin_time}s" dur="{ROW_DURATION}s"
                 fill="freeze" calcMode="spline" keySplines="0.2 0 0.2 1" />
      </rect>
    </clipPath>
    <g clip-path="url(#{clip_id})">
      <text x="0" y="{i * LINE_H}" font-family="'JetBrains Mono','Fira Code',monospace"
            font-size="{FONT_SIZE}" fill="{FILL_COLOR}" xml:space="preserve">{safe_text}</text>
      <rect x="0" y="{i * LINE_H - FONT_SIZE}" width="2" height="{LINE_H}" fill="{FILL_COLOR}" opacity="0.85">
        <animate attributeName="x" from="0" to="{row_width}"
                 begin="{begin_time}s" dur="{ROW_DURATION}s" fill="freeze"
                 calcMode="spline" keySplines="0.2 0 0.2 1" />
        <animate attributeName="opacity" from="0.85" to="0"
                 begin="{begin_time + ROW_DURATION}s" dur="0.15s" fill="freeze" />
      </rect>
    </g>''')

    body = "\n".join(row_groups)

    return f'''<svg viewBox="0 0 {width} {height}" width="{width}" height="{height}"
     xmlns="http://www.w3.org/2000/svg" style="background:{BG_COLOR}">
  <defs></defs>
  <g transform="translate(10,{FONT_SIZE + 6})">{body}
  </g>
</svg>'''


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else "source-prepped.png"
    dst = sys.argv[2] if len(sys.argv) > 2 else "khokon-ascii.svg"

    if not Path(src).exists():
        print(f"No prepped photo found at {src}.")
        print("Run: python scripts/prep_photo.py <your-photo.jpg> first.")
        sys.exit(1)

    ascii_rows = image_to_ascii_rows(src, GRID_COLS, GRID_ROWS)
    svg = build_svg(ascii_rows, GRID_COLS)
    Path(dst).write_text(svg)
    print(f"Wrote {dst}")


if __name__ == "__main__":
    main()
