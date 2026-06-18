#!/usr/bin/env python3
"""
Refresh the Show HN corpus from the HN Algolia API.

Writes:
- patterns/corpus.json     (1000 slimmed entries, sorted by points desc)
- patterns/top-100.json    (top 100 with full readable fields)
- patterns/posting-time.md  (regenerated stats — manual edit zone marked)

Run quarterly. Algolia public API rate limit is generous (no key required);
this script makes at most 10 requests and sleeps 1s between pages.

Algolia caps `tags=show_hn` search at 1000 hits per tag-filtered query, so this
is the practical ceiling without an Algolia API key for re-ranking.

Usage:
    python tools/refresh-corpus.py [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ALGOLIA_URL = "https://hn.algolia.com/api/v1/search?tags=show_hn&hitsPerPage=1000&page={page}"
ALGOLIA_RECENT_URL = "https://hn.algolia.com/api/v1/search_by_date?tags=show_hn&hitsPerPage=1000&page={page}"
SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
CORPUS_PATH = SKILL_ROOT / "patterns" / "corpus.json"
TOP100_PATH = SKILL_ROOT / "patterns" / "top-100.json"
FAILED_PATH = SKILL_ROOT / "patterns" / "failed-corpus.json"
POSTING_TIME_PATH = SKILL_ROOT / "patterns" / "posting-time.md"
FAILED_POINT_CEILING = 5

MAX_PAGES = 10
SLEEP_BETWEEN_PAGES_SEC = 1.0


def fetch_page(url_template: str, page: int) -> list[dict]:
    url = url_template.format(page=page)
    req = urllib.request.Request(url, headers={"User-Agent": "show-hn-writer/refresh"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read())
    return data.get("hits", [])


def fetch_all(url_template: str) -> list[dict]:
    all_hits: list[dict] = []
    for page in range(MAX_PAGES):
        try:
            hits = fetch_page(url_template, page)
        except urllib.error.HTTPError as e:
            print(f"[refresh-corpus] page {page} HTTP {e.code}; stopping.", file=sys.stderr)
            break
        if not hits:
            break
        all_hits.extend(hits)
        if len(hits) < 1000:
            break
        time.sleep(SLEEP_BETWEEN_PAGES_SEC)
    return all_hits


def slim(hit: dict) -> dict:
    return {
        "points": hit.get("points"),
        "comments": hit.get("num_comments"),
        "title": hit.get("title"),
        "url": hit.get("url"),
        "created_at": hit.get("created_at"),
        "id": hit.get("objectID"),
    }


def dedup_key(url: str | None) -> str | None:
    """Conservative dedup: github.com/owner/repo only.

    Other hostnames are NOT deduped because most are author blogs (multiple
    distinct projects per blog) or multi-tenant platforms (medium.com,
    play.google.com). Aggregating those would erase real distinct posts.
    Only github.com paths reliably map 1:1 to a single project."""
    if not url:
        return None
    try:
        parsed = urllib.parse.urlparse(url)
    except ValueError:
        return None
    host = parsed.netloc.lower().replace("www.", "")
    if host != "github.com":
        return None
    parts = [p for p in parsed.path.split("/") if p]
    if len(parts) < 2:
        return None
    return f"github.com/{parts[0]}/{parts[1]}"


def dedup_hits(hits: list[dict]) -> tuple[list[dict], int]:
    """Keep highest-point entry per dedup_key. Untouched entries pass through.

    Returns (deduped_list, removed_count)."""
    by_key: dict[str, dict] = {}
    pass_through: list[dict] = []
    for h in hits:
        k = dedup_key(h.get("url"))
        if k is None:
            pass_through.append(h)
            continue
        prev = by_key.get(k)
        if prev is None or (h.get("points") or 0) > (prev.get("points") or 0):
            by_key[k] = h
    deduped = pass_through + list(by_key.values())
    deduped.sort(key=lambda h: -(h.get("points") or 0))
    return deduped, len(hits) - len(deduped)


def write_corpus(hits: list[dict], dry_run: bool) -> None:
    deduped, removed = dedup_hits(hits)
    if removed:
        print(f"[refresh-corpus] deduped {removed} github.com/owner/repo reposts")
    slimmed = [slim(h) for h in deduped]
    top = slimmed[:100]
    if dry_run:
        print(f"[dry-run] would write {len(slimmed)} to {CORPUS_PATH}")
        print(f"[dry-run] would write {len(top)} to {TOP100_PATH}")
        return
    CORPUS_PATH.write_text(
        json.dumps(slimmed, ensure_ascii=False, indent=0),
        encoding="utf-8",
    )
    TOP100_PATH.write_text(
        json.dumps(top, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[refresh-corpus] wrote {len(slimmed)} -> {CORPUS_PATH}")
    print(f"[refresh-corpus] wrote {len(top)} -> {TOP100_PATH}")


def compute_time_stats(hits: list[dict]) -> dict:
    dow_pts: dict[int, list[int]] = defaultdict(list)
    hour_pts: dict[int, list[int]] = defaultdict(list)
    dow_hour_pts: dict[tuple[int, int], list[int]] = defaultdict(list)
    for h in hits:
        if not h.get("created_at") or not h.get("points"):
            continue
        try:
            dt = datetime.fromisoformat(h["created_at"].replace("Z", "+00:00"))
        except ValueError:
            continue
        et = dt.astimezone(timezone.utc).replace(tzinfo=None)
        et_hour = (et.hour - 5) % 24
        dow = et.weekday()
        pts = h["points"]
        dow_pts[dow].append(pts)
        hour_pts[et_hour].append(pts)
        dow_hour_pts[(dow, et_hour)].append(pts)
    return {"dow": dow_pts, "hour": hour_pts, "dow_hour": dow_hour_pts}


def render_posting_time(stats: dict, n_total: int) -> str:
    dow_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    def percentile(sorted_vals, p):
        if not sorted_vals:
            return 0
        return sorted_vals[min(len(sorted_vals) - 1, int(len(sorted_vals) * p))]

    dow_lines = []
    for d in range(7):
        pts = sorted(stats["dow"][d])
        if not pts:
            continue
        dow_lines.append(
            f"| {dow_names[d]} | {len(pts)} | {statistics.median(pts):.0f} | "
            f"{percentile(pts, 0.75)} | {percentile(pts, 0.90)} |"
        )

    hour_lines = []
    for h in range(8, 14):
        pts = sorted(stats["hour"][h])
        if not pts:
            continue
        hour_lines.append(
            f"| {h} | {len(pts)} | {statistics.median(pts):.0f} | {percentile(pts, 0.75)} |"
        )

    qualified = [
        ((d, h), statistics.median(v))
        for (d, h), v in stats["dow_hour"].items()
        if len(v) >= 15
    ]
    qualified.sort(key=lambda kv: -kv[1])
    bucket_lines = []
    for (d, h), m in qualified[:10]:
        bucket_lines.append(
            f"| {dow_names[d]} {h:>2} ET | {m:.0f} | {len(stats['dow_hour'][(d, h)])} |"
        )

    today = datetime.now(timezone.utc).date().isoformat()
    return f"""# Posting time analysis

Auto-generated by `tools/refresh-corpus.py` on {today}. Source: `corpus.json` ({n_total} Show HN posts, all >676 points = top 25% historically). Times converted from UTC to ET using a fixed UTC-5 offset (DST drift ±1h tolerated).

## Caveat — survivor bias

The corpus contains only high-scoring posts. This data answers "when do top performers tend to post", not "when does posting maximize the chance of becoming a top performer". Treat the windows below as where the survivors cluster, not as a guarantee.

## Day of week (ET)

| Day | n | median pts | p75 | p90 |
|---|---|---|---|---|
{chr(10).join(dow_lines)}

## Hour of day (ET) — peak window

| Hour ET | n | median | p75 |
|---|---|---|---|
{chr(10).join(hour_lines)}

## Top 10 (dow, hour) buckets — n ≥ 15

| Slot | median pts | n |
|---|---|---|
{chr(10).join(bucket_lines)}

## Recommendation

Tue, Wed, Thu — 8:00 to 12:00 ET. For KST conversion: ET 8:00-12:00 = KST 22:00 to 02:00 next day.

<!-- The narrative caveats above this line are auto-rewritten on every refresh.
     Manual prose below this marker is preserved across refreshes. -->

## What this data does NOT cover

- Time-of-year effects (holiday weeks etc.)
- Topic-specific timing
- Counterfactuals: whether the same post would do better at a different time
- Front-page duration after the post hour
"""


def write_posting_time(stats: dict, n_total: int, dry_run: bool) -> None:
    rendered = render_posting_time(stats, n_total)
    if dry_run:
        print(f"[dry-run] would write {len(rendered)} chars to {POSTING_TIME_PATH}")
        return
    POSTING_TIME_PATH.write_text(rendered, encoding="utf-8")
    print(f"[refresh-corpus] wrote {POSTING_TIME_PATH}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="print what would change, write nothing")
    args = parser.parse_args()

    print("[refresh-corpus] fetching success corpus from HN Algolia (by relevance)...")
    hits = fetch_all(ALGOLIA_URL)
    if not hits:
        print("[refresh-corpus] no success hits fetched; aborting without overwrite.", file=sys.stderr)
        return 1
    print(f"[refresh-corpus] fetched {len(hits)} success hits")

    write_corpus(hits, args.dry_run)
    stats = compute_time_stats(hits)
    write_posting_time(stats, len(hits), args.dry_run)

    print("[refresh-corpus] fetching recent posts for failure corpus (by date)...")
    recent = fetch_all(ALGOLIA_RECENT_URL)
    failed = [slim(h) for h in recent if (h.get("points") or 0) <= FAILED_POINT_CEILING]
    if args.dry_run:
        print(f"[dry-run] would write {len(failed)} (points<={FAILED_POINT_CEILING}) to {FAILED_PATH}")
    else:
        FAILED_PATH.write_text(
            json.dumps(failed, ensure_ascii=False, indent=0),
            encoding="utf-8",
        )
        print(f"[refresh-corpus] wrote {len(failed)} -> {FAILED_PATH}")

    print("[refresh-corpus] done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
