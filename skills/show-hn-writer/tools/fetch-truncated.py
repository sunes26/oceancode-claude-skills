#!/usr/bin/env python3
"""
Re-fetch weeks that hit the 1000-cap during fetch-corpus-full.

Splits each cap-hitting week into 3.5-day half-chunks and merges results
into patterns/all-corpus.json. Idempotent — runs after the main fetch.
"""
from __future__ import annotations

import json
import sys
import time
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ALGOLIA = "https://hn.algolia.com/api/v1/search_by_date"
SKILL_ROOT = Path(__file__).resolve().parent.parent
ALL_PATH = SKILL_ROOT / "patterns" / "all-corpus.json"

WEEK_SEC = 7 * 24 * 3600
SUBCHUNK_SEC = WEEK_SEC // 2  # 3.5 days
HN_EPOCH = int(datetime(2007, 2, 19, tzinfo=timezone.utc).timestamp())
SLEEP_SEC = 0.7


def fetch_chunk(start: int, end: int) -> tuple[list[dict], int]:
    params = {
        "tags": "show_hn",
        "hitsPerPage": 1000,
        "numericFilters": f"created_at_i>={start},created_at_i<{end}",
    }
    url = f"{ALGOLIA}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": "show-hn-writer/fetch-truncated"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read())
    return data.get("hits", []), data.get("nbHits", 0)


def slim(hit: dict) -> dict:
    return {
        "points": hit.get("points"),
        "comments": hit.get("num_comments"),
        "title": hit.get("title"),
        "url": hit.get("url"),
        "created_at": hit.get("created_at"),
        "created_at_i": hit.get("created_at_i"),
        "id": hit.get("objectID"),
        "author": hit.get("author"),
    }


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

    existing = json.loads(ALL_PATH.read_text(encoding="utf-8"))
    by_id = {h["id"]: h for h in existing if h.get("id")}
    initial = len(by_id)
    print(f"[fetch-truncated] starting: {initial} existing entries")

    by_week = defaultdict(int)
    for h in existing:
        t = h.get("created_at_i") or 0
        week_start = HN_EPOCH + ((t - HN_EPOCH) // WEEK_SEC) * WEEK_SEC
        by_week[week_start] += 1

    cap_hit_weeks = sorted([w for w, c in by_week.items() if c >= 1000])
    print(f"[fetch-truncated] {len(cap_hit_weeks)} weeks at 1000-cap")

    for week_start in cap_hit_weeks:
        for i in range(2):
            sub_start = week_start + i * SUBCHUNK_SEC
            sub_end = sub_start + SUBCHUNK_SEC
            try:
                hits, nbhits = fetch_chunk(sub_start, sub_end)
            except Exception as e:
                print(f"[fetch-truncated] err on {datetime.fromtimestamp(sub_start, tz=timezone.utc).date()}: {e}", file=sys.stderr)
                time.sleep(2)
                continue
            new_added = 0
            for h in hits:
                sh = slim(h)
                hid = sh.get("id")
                if hid and hid not in by_id:
                    by_id[hid] = sh
                    new_added += 1
            d = datetime.fromtimestamp(sub_start, tz=timezone.utc).date()
            cap_warning = " STILL CAPPED" if nbhits > 1000 else ""
            print(f"  {d}: nbHits={nbhits}  new={new_added}{cap_warning}")
            time.sleep(SLEEP_SEC)

    sorted_items = sorted(by_id.values(), key=lambda h: -(h.get("created_at_i") or 0))
    ALL_PATH.write_text(json.dumps(sorted_items, ensure_ascii=False, indent=0), encoding="utf-8")
    print(f"\n[fetch-truncated] DONE  total={len(by_id)}  net new={len(by_id) - initial}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
