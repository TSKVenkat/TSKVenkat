#!/usr/bin/env python3
"""Scrape the public GitHub contribution calendar into data/contributions.json.

Uses the unauthenticated HTML endpoint, so no token or API quota is involved.
"""
import json
import re
from datetime import date, timedelta
from pathlib import Path

import requests
from bs4 import BeautifulSoup

USER = "TSKVenkat"
URL = f"https://github.com/users/{USER}/contributions"
OUT = Path(__file__).resolve().parent.parent / "data" / "contributions.json"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (profile-art bot; +https://github.com/TSKVenkat)",
    "X-Requested-With": "XMLHttpRequest",
}


def scrape():
    html = requests.get(URL, headers=HEADERS, timeout=30)
    html.raise_for_status()
    soup = BeautifulSoup(html.text, "html.parser")

    # Counts live in the sibling <tool-tip> elements, keyed by the cell's id.
    tips = {t.get("for"): t.get_text(" ", strip=True) for t in soup.select("tool-tip")}

    days = []
    for cell in soup.select("td.ContributionCalendar-day"):
        iso = cell.get("data-date")
        if not iso:
            continue
        text = tips.get(cell.get("id"), "")
        m = re.match(r"([\d,]+)\s+contribution", text)
        days.append(
            {
                "date": iso,
                "count": int(m.group(1).replace(",", "")) if m else 0,
                "level": int(cell.get("data-level") or 0),
            }
        )

    days.sort(key=lambda d: d["date"])
    if not days:
        raise SystemExit("no contribution cells found - GitHub markup may have changed")
    return days


def streaks(days):
    """Current and longest run of consecutive days with >0 contributions."""
    longest = run = 0
    for d in days:
        run = run + 1 if d["count"] else 0
        longest = max(longest, run)

    # A blank today does not break the current streak until the day is over.
    current = 0
    today = date.today().isoformat()
    for d in reversed(days):
        if d["count"]:
            current += 1
        elif d["date"] != today:
            break
    return current, longest


def main():
    days = scrape()
    total = sum(d["count"] for d in days)
    active = [d for d in days if d["count"]]
    best = max(days, key=lambda d: d["count"])
    current, longest = streaks(days)

    payload = {
        "user": USER,
        "generated": date.today().isoformat(),
        "range": {"start": days[0]["date"], "end": days[-1]["date"]},
        "stats": {
            "total": total,
            "active_days": len(active),
            "max_day": {"date": best["date"], "count": best["count"]},
            "current_streak": current,
            "longest_streak": longest,
            "avg_per_active_day": round(total / len(active), 2) if active else 0,
            "last_30": sum(
                d["count"]
                for d in days
                if d["date"] >= (date.today() - timedelta(days=30)).isoformat()
            ),
        },
        "days": days,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2) + "\n")
    print(
        f"wrote {OUT.name}: {len(days)} days, {total} contributions, "
        f"streak {current} (best {longest})"
    )


if __name__ == "__main__":
    main()
