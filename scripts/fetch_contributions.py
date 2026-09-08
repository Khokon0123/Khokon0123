#!/usr/bin/env python3
"""
fetch_contributions.py — pull your real contribution calendar with no
GraphQL API and no personal access token.

GitHub serves the calendar as public HTML at
    https://github.com/users/<username>/contributions
which is the exact fragment the profile page itself embeds. We fetch it,
parse the day cells with BeautifulSoup, and write data/contributions.json
with the raw days plus a few derived stats (current streak, longest streak,
best day, monthly totals).

Usage:
    python scripts/fetch_contributions.py [username]
"""
import json
import sys
from collections import defaultdict
from datetime import datetime, date, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

DEFAULT_USERNAME = "Khokon0123"
URL_TEMPLATE = "https://github.com/users/{username}/contributions"


def fetch_calendar_html(username: str) -> str:
    url = URL_TEMPLATE.format(username=username)
    headers = {"User-Agent": "Mozilla/5.0 (profile-readme-generator)"}
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()
    return resp.text


def parse_days(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    days = []

    # GitHub renders each day as a <td> with data-date and either
    # data-level (newer markup) or a data-count/tooltip pairing (older markup).
    cells = soup.select("td.ContributionCalendar-day, td[data-date]")
    if not cells:
        cells = soup.select("rect.ContributionCalendar-day, rect[data-date]")

    tooltip_map = {}
    for tt in soup.select("tool-tip"):
        tooltip_map[tt.get("for")] = tt.get_text(strip=True)

    for cell in cells:
        d = cell.get("data-date")
        if not d:
            continue
        level = cell.get("data-level")
        count = None

        if level is not None:
            level = int(level)
        else:
            level = 0

        cell_id = cell.get("id")
        tooltip_text = tooltip_map.get(cell_id, "")
        if tooltip_text:
            digits = "".join(ch for ch in tooltip_text.split(" ")[0] if ch.isdigit())
            if digits:
                count = int(digits)
            elif "No contributions" in tooltip_text:
                count = 0

        if count is None:
            count = cell.get("data-count")
            count = int(count) if count is not None else 0

        days.append({"date": d, "count": count, "level": level})

    days.sort(key=lambda x: x["date"])
    return days


def compute_stats(days: list[dict]) -> dict:
    if not days:
        return {}

    total = sum(d["count"] for d in days)

    # Streaks
    longest = current = 0
    running = 0
    today = date.today()
    for d in days:
        if d["count"] > 0:
            running += 1
            longest = max(longest, running)
        else:
            running = 0
    # current streak counts backward from the most recent day with data
    running = 0
    for d in reversed(days):
        if d["count"] > 0:
            running += 1
        else:
            break
    current = running

    best_day = max(days, key=lambda x: x["count"])

    monthly = defaultdict(int)
    for d in days:
        month_key = d["date"][:7]  # YYYY-MM
        monthly[month_key] += d["count"]

    return {
        "total_last_year": total,
        "current_streak": current,
        "longest_streak": longest,
        "best_day": {"date": best_day["date"], "count": best_day["count"]},
        "monthly_totals": dict(sorted(monthly.items())),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def main():
    username = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_USERNAME
    print(f"Fetching contribution calendar for {username} ...")
    html = fetch_calendar_html(username)
    days = parse_days(html)

    if not days:
        print("Warning: parsed 0 days. GitHub may have changed its markup —")
        print("inspect the raw HTML and adjust the selectors in parse_days().")

    stats = compute_stats(days)

    out = {"username": username, "days": days, "stats": stats}
    out_path = Path("data/contributions.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2))

    print(f"Wrote {out_path} ({len(days)} days, {stats.get('total_last_year', 0)} contributions)")


if __name__ == "__main__":
    main()
