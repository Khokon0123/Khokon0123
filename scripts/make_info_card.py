#!/usr/bin/env python3
"""
make_info_card.py — a neofetch-style panel that fades/slides in line by line.

Edit the CONTENT block below whenever your "now / prev / stack / highlights"
change — that's the whole point of keeping this separate from the heatmap,
which already covers your raw GitHub stats.

Usage:
    python scripts/make_info_card.py            # animated version
    STATIC=1 python scripts/make_info_card.py    # frozen frame (for Quick Look)
"""
import os
from pathlib import Path

WIDTH = 490
TITLE = "khokon@github"
ACCENT = "#39d353"     # GitHub-green accent for the title bar / labels
LABEL_COLOR = "#7d8590"
VALUE_COLOR = "#c9d1d9"
BG = "transparent"
LINE_H = 24
STAGGER = 0.09
DUR = 0.4

ROWS = [
    ("OS", "Bangladesh -> Ohio, USA"),
    ("Host", "Ohio Wesleyan University '29"),
    ("Kernel", "Computer Science, GPA 3.89"),
    ("Now", "CTO @ EUNRI | SWE Intern @ ByteWright"),
    ("Prev", "OnlySwap - 2nd place, HackPrinceton"),
    ("Stack", "Python, React Native, C++, Supabase"),
    ("Papers", "ICCSIS 2026 Toronto | ICCIE 2026 Paris"),
    ("Leads", "President, OWU Robotics + Debate Club"),
    ("Roots", "Founder, Green Education (Bangladesh)"),
]

SWATCHES = ["#f78166", "#e3b341", "#39d353", "#58a6ff", "#bc8cff", "#f778ba"]


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build_svg(static: bool) -> str:
    content_top = 46
    height = content_top + len(ROWS) * LINE_H + 40

    lines_svg = []
    for i, (label, value) in enumerate(ROWS):
        y = content_top + i * LINE_H
        begin = round(i * STAGGER, 3)

        if static:
            opacity_attr = 'opacity="1"'
            transform_attr = 'transform="translate(0,0)"'
            anim = ""
        else:
            opacity_attr = 'opacity="0"'
            transform_attr = f'transform="translate(-12,0)"'
            anim = f'''
        <animate attributeName="opacity" from="0" to="1" begin="{begin}s" dur="{DUR}s" fill="freeze" />
        <animateTransform attributeName="transform" type="translate"
                           from="-12,0" to="0,0" begin="{begin}s" dur="{DUR}s"
                           fill="freeze" calcMode="spline" keySplines="0.2 0 0.2 1" />'''

        lines_svg.append(f'''
    <g {opacity_attr} {transform_attr}>{anim}
      <text x="24" y="{y}" font-family="'JetBrains Mono','Fira Code',monospace"
            font-size="13" font-weight="600" fill="{ACCENT}">{esc(label)}</text>
      <text x="120" y="{y}" font-family="'JetBrains Mono','Fira Code',monospace"
            font-size="13" fill="{VALUE_COLOR}">{esc(value)}</text>
    </g>''')

    swatch_y = content_top + len(ROWS) * LINE_H + 14
    swatch_begin = round(len(ROWS) * STAGGER, 3)
    swatches_svg = []
    for i, color in enumerate(SWATCHES):
        x = 24 + i * 22
        if static:
            op = '1'
            anim = ""
        else:
            op = '0'
            anim = f'''<animate attributeName="opacity" from="0" to="1"
                 begin="{round(swatch_begin + i * 0.04, 3)}s" dur="0.25s" fill="freeze" />'''
        swatches_svg.append(
            f'<rect x="{x}" y="{swatch_y}" width="16" height="16" rx="3" '
            f'fill="{color}" opacity="{op}">{anim}</rect>'
        )

    lines_body = "\n".join(lines_svg)
    swatches_body = "\n".join(swatches_svg)

    return f'''<svg viewBox="0 0 {WIDTH} {height}" width="{WIDTH}" height="{height}"
     xmlns="http://www.w3.org/2000/svg" style="background:{BG}">
  <rect x="0" y="0" width="{WIDTH}" height="{height}" rx="10"
        fill="#0d1117" stroke="#30363d" stroke-width="1" />
  <rect x="0" y="0" width="{WIDTH}" height="30" rx="10" fill="#161b22" />
  <rect x="0" y="16" width="{WIDTH}" height="14" fill="#161b22" />
  <circle cx="18" cy="15" r="5" fill="#f78166" />
  <circle cx="36" cy="15" r="5" fill="#e3b341" />
  <circle cx="54" cy="15" r="5" fill="#39d353" />
  <text x="{WIDTH / 2}" y="20" font-family="'JetBrains Mono','Fira Code',monospace"
        font-size="12" fill="{LABEL_COLOR}" text-anchor="middle">{esc(TITLE)}</text>
  {lines_body}
  {swatches_body}
</svg>'''


def main():
    static = os.environ.get("STATIC") == "1"
    svg = build_svg(static)
    out = "info-card.svg" if not static else "info-card-static.svg"
    Path(out).write_text(svg)
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
