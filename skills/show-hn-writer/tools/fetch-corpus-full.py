#!/usr/bin/env python3
"""
Fetch the full historical Show HN corpus via Algolia date chunking.

Algolia caps each query at 1000 hits. By chunking the time range we get
around the cap. One week per chunk fits comfortably under the cap for
the full HN era (max ~800 Show HN posts in any single week observed).

Output: patterns/all-corpus.json (raw entries, sorted by created_at_i desc).
Use tools/build-corpora.py afterward to derive success and failed
subsets from this file.

Usage:
    python tools/fetch-corpus-full.py
    python tools/fetch-corpus-full.py --since 2020-01-01     # newer-only
    python tools/fetch-corpus-full.py --resume               # continue
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ALGOLIA = "https://hn.algolia.com/api/v1/search_by_date"
SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
ALL_PATH = SKILL_ROOT / "patterns" / "all-corpus.json"

HN_EPOCH = int(datetime(2007, 2, 19, tzinfo=timezone.utc).timestamp())
WEEK_SEC = 7 * 24 * 3600
SLEEP_SEC = 0.7
CHECKPOINT_EVERY = 25  # write to disk every N chunks


def fetch_chunk(start: int, end: int) -> tuple[list[dict], int]:
    params = {
        "tags": "show_hn",
        "hitsPerPage": 1000,
        "numericFilters": f"created_at_i>={start},created_at_i<{end}",
    }
    url = f"{ALGOLIA}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": "show-hn-writer/fetch-full"})
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


def load_existing() -> dict[str, dict]:
    if not ALL_PATH.exists():
        return {}
    try:
        existing = json.loads(ALL_PATH.read_text(encoding="utf-8"))
        return {h["id"]: h for h in existing if h.get("id")}
    except (json.JSONDecodeError, KeyError):
        return {}


def save(by_id: dict[str, dict]) -> None:
    sorted_items = sorted(by_id.values(), key=lambda h: -(h.get("created_at_i") or 0))
    ALL_PATH.write_text(
        json.dumps(sorted_items, ensure_ascii=False, indent=0),
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--since", help="ISO date (YYYY-MM-DD) to start from, default = HN epoch")
    parser.add_argument("--resume", action="store_true", help="Skip chunks already covered")
    args = parser.parse_args()

    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

    if args.since:
        start_epoch = int(datetime.fromisoformat(args.since).replace(tzinfo=timezone.utc).timestamp())
    else:
        start_epoch = HN_EPOCH

    end_epoch = int(time.time())
    total_weeks = (end_epoch - start_epoch) // WEEK_SEC + 1

    by_id = load_existing() if args.resume else {}
    initial_count = len(by_id)
    print(f"[fetch-full] start_epoch={start_epoch} ({datetime.fromtimestamp(start_epoch, tz=timezone.utc).date()})")
    print(f"[fetch-full] end_epoch={end_epoch} ({datetime.fromtimestamp(end_epoch, tz=timezone.utc).date()})")
    print(f"[fetch-full] total weeks to cover: {total_weeks}")
    print(f"[fetch-full] existing entries loaded: {initial_count}")

    truncated_chunks: list[tuple[int, int, int]] = []
    chunk_idx = 0
    cursor = start_epoch
    last_save = time.time()

    while cursor < end_epoch:
        chunk_end = min(cursor + WEEK_SEC, end_epoch)
        try:
            hits, nbhits = fetch_chunk(cursor, chunk_end)
        except urllib.error.URLError as e:
            print(f"[fetch-full] chunk {chunk_idx} network error: {e}; retry in 5s", file=sys.stderr)
            time.sleep(5)
            try:
                hits, nbhits = fetch_chunk(cursor, chunk_end)
            except urllib.error.URLError as e2:
                print(f"[fetch-full] chunk {chunk_idx} retry failed: {e2}; skipping", file=sys.stderr)
                cursor = chunk_end
                chunk_idx += 1
                continue

        for h in hits:
            sh = slim(h)
            hid = sh.get("id")
            if hid:
                by_id[hid] = sh

        if nbhits > 1000:
            truncated_chunks.append((cursor, chunk_end, nbhits))

        chunk_idx += 1
        if chunk_idx % CHECKPOINT_EVERY == 0:
            save(by_id)
            elapsed = time.time() - last_save
            last_save = time.time()
            chunk_date = datetime.fromtimestamp(cursor, tz=timezone.utc).date()
            print(f"[fetch-full] chunk {chunk_idx}/{total_weeks}  date={chunk_date}  total={len(by_id)}  truncated_so_far={len(truncated_chunks)}  ({elapsed:.1f}s/{CHECKPOINT_EVERY}chunks)")

        cursor = chunk_end
        time.sleep(SLEEP_SEC)

    save(by_id)
    print(f"\n[fetch-full] DONE  total entries: {len(by_id)}  net new: {len(by_id) - initial_count}")
    if truncated_chunks:
        print(f"[fetch-full] WARNING: {len(truncated_chunks)} chunks hit 1000-cap, some entries missed:")
        for s, e, n in truncated_chunks[:10]:
            sd = datetime.fromtimestamp(s, tz=timezone.utc).date()
            ed = datetime.fromtimestamp(e, tz=timezone.utc).date()
            print(f"  {sd}..{ed}: nbHits={n}")
        if len(truncated_chunks) > 10:
            print(f"  ... and {len(truncated_chunks)-10} more")
        print("Re-run with a smaller chunk size (modify WEEK_SEC) for truncated ranges.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
