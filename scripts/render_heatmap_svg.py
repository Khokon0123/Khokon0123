#!/usr/bin/env python3
"""
render_heatmap_svg.py — draw data/contributions.json as the classic
53-week x 7-day calendar of rounded boxes, revealed once with a diagonal
line-after-line slide-down (then frozen — no looping "glow").

Usage:
    python scripts/render_heatmap_svg.py [data/contributions.json] [contrib-heatmap.svg]
"""
import json
import sys
from datetime import datetime
from pathlib import Path

# none -> brightest (level 5 is a neon top end, past GitHub's real max of 4)
PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]

CELL = 11
GAP = 3
CELL_STEP = CELL + GAP
LEFT_PAD = 30       # room for day-of-week labels
TOP_PAD = 24         # room for month labels
RIGHT_PAD = 12
BOTTOM_PAD = 40      # room for legend + stats footer

STAGGER = 0.006      # seconds between diagonal "wave" steps
DUR = 0.35

MONTH_LABELS = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
]
DOW_LABELS = {1: "Mon", 3: "Wed", 5: "Fri"}  # Mon/Wed/Fri, GitHub-style


def level_from_count(count: int, thresholds=(0, 2, 5, 9, 14)) -> int:
    # thresholds tuned generously; real distribution varies a lot by person,
    # so this maps into 0..4 (level 5 is reserved as a "personal best" pop)
    if count <= thresholds[0]:
        return 0
    if count <= thresholds[1]:
        return 1
    if count <= thresholds[2]:
        return 2
    if count <= thresholds[3]:
        return 3
    return 4


def build_weeks(days: list[dict]) -> list[list[dict | None]]:
    """Bucket days into GitHub-style weeks (columns), Sunday-first rows."""
    parsed = []
    for d in days:
        dt = datetime.strptime(d["date"], "%Y-%m-%d").date()
        parsed.append({**d, "_dt": dt, "_dow": dt.isoweekday() % 7})  # 0=Sun..6=Sat

    if not parsed:
        return []

    weeks: list[list[dict | None]] = []
    current_week: list[dict | None] = [None] * 7

    first_dow = parsed[0]["_dow"]
    for i in range(first_dow):
        current_week[i] = None

    for entry in parsed:
        current_week[entry["_dow"]] = entry
        if entry["_dow"] == 6:
            weeks.append(current_week)
            current_week = [None] * 7

    if any(c is not None for c in current_week):
        weeks.append(current_week)

    return weeks


def month_label_positions(weeks: list[list[dict | None]]) -> list[tuple[int, str]]:
    labels = []
    last_month = None
    for week_idx, week in enumerate(weeks):
        for cell in week:
            if cell is None:
                continue
            month = cell["_dt"].month
            if month != last_month:
                labels.append((week_idx, MONTH_LABELS[month - 1]))
                last_month = month
            break
    return labels


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build_svg(payload: dict) -> str:
    days = payload["days"]
    stats = payload.get("stats", {})
    username = payload.get("username", "")

    weeks = build_weeks(days)
    n_weeks = len(weeks)

    width = LEFT_PAD + n_weeks * CELL_STEP + RIGHT_PAD
    height = TOP_PAD + 7 * CELL_STEP + BOTTOM_PAD

    cells_svg = []
    max_delay = 0.0
    for w_idx, week in enumerate(weeks):
        for d_idx, cell in enumerate(week):
            if cell is None:
                continue
            level = level_from_count(cell["count"], )
            # cap to the real GitHub 0..4 range for color; level 5 reserved for best day
            color = PALETTE[level if level < 5 else 4]
            if stats.get("best_day", {}).get("date") == cell["date"] and cell["count"] > 0:
                color = PALETTE[5]  # neon pop for your single best day

            x = LEFT_PAD + w_idx * CELL_STEP
            y = TOP_PAD + d_idx * CELL_STEP

            # diagonal wave: delay depends on week + day so it slides in
            # top-left to bottom-right rather than column by column
            delay = round((w_idx + d_idx) * STAGGER, 4)
            max_delay = max(max_delay, delay)

            title = esc(f"{cell['count']} contributions on {cell['date']}")

            cells_svg.append(f'''
    <rect x="{x}" y="{y - 8}" width="{CELL}" height="{CELL}" rx="2" ry="2"
          fill="{color}" opacity="0">
      <title>{title}</title>
      <animate attributeName="opacity" from="0" to="1"
               begin="{delay}s" dur="{DUR}s" fill="freeze" />
      <animate attributeName="y" from="{y - 8}" to="{y}"
               begin="{delay}s" dur="{DUR}s" fill="freeze"
               calcMode="spline" keySplines="0.2 0 0.2 1" />
    </rect>''')

    month_labels_svg = []
    for w_idx, label in month_label_positions(weeks):
        x = LEFT_PAD + w_idx * CELL_STEP
        month_labels_svg.append(
            f'<text x="{x}" y="{TOP_PAD - 8}" font-family="\'JetBrains Mono\',monospace" '
            f'font-size="10" fill="#7d8590">{label}</text>'
        )

    dow_labels_svg = []
    for d_idx, label in DOW_LABELS.items():
        y = TOP_PAD + d_idx * CELL_STEP + CELL
        dow_labels_svg.append(
            f'<text x="0" y="{y}" font-family="\'JetBrains Mono\',monospace" '
            f'font-size="9" fill="#7d8590">{label}</text>'
        )

    legend_y = height - 26
    legend_x_start = width - RIGHT_PAD - (len(PALETTE) - 1) * 16 - 60
    legend_svg = [
        f'<text x="{legend_x_start - 34}" y="{legend_y + 9}" '
        f'font-family="\'JetBrains Mono\',monospace" font-size="9" fill="#7d8590">Less</text>'
    ]
    for i, color in enumerate(PALETTE[:5]):  # legend shows the real 0..4 scale
        lx = legend_x_start + i * 16
        legend_svg.append(
            f'<rect x="{lx}" y="{legend_y}" width="10" height="10" rx="2" fill="{color}" />'
        )
    legend_svg.append(
        f'<text x="{legend_x_start + 5 * 16 + 4}" y="{legend_y + 9}" '
        f'font-family="\'JetBrains Mono\',monospace" font-size="9" fill="#7d8590">More</text>'
    )

    total = stats.get("total_last_year", sum(d["count"] for d in days))
    streak = stats.get("current_streak", 0)
    longest = stats.get("longest_streak", 0)
    footer_text = f"{total} contributions in the last year - current streak {streak}d - longest {longest}d"

    footer_svg = (
        f'<text x="{LEFT_PAD}" y="{legend_y + 9}" '
        f'font-family="\'JetBrains Mono\',monospace" font-size="10" fill="#c9d1d9">{esc(footer_text)}</text>'
    )

    cells_body = "\n".join(cells_svg)
    months_body = "\n".join(month_labels_svg)
    dow_body = "\n".join(dow_labels_svg)
    legend_body = "\n".join(legend_svg)

    return f'''<svg viewBox="0 0 {width} {height}" width="{width}" height="{height}"
     xmlns="http://www.w3.org/2000/svg" style="background:transparent">
  <g transform="translate({LEFT_PAD},0)">{months_body}</g>
  <g>{dow_body}</g>
  <g>{cells_body}
  </g>
  <g>{legend_body}</g>
  {footer_svg}
</svg>'''


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else "data/contributions.json"
    dst = sys.argv[2] if len(sys.argv) > 2 else "contrib-heatmap.svg"

    payload = json.loads(Path(src).read_text())
    svg = build_svg(payload)
    Path(dst).write_text(svg)
    print(f"Wrote {dst}")


if __name__ == "__main__":
    main()
