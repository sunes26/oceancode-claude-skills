#!/usr/bin/env python3
"""
Fetch body text (story_text) + author first comments for sampled posts.

Source: HN Firebase API (hacker-news.firebaseio.com). Algolia hits do not
include story_text reliably; Firebase does. Rate-limited to ~2 req/s.

Output:
- patterns/bodies-success.json
- patterns/bodies-failed.json
- patterns/first-comments-success.json

Sampling:
- success: 500 posts random from corpus.json
- failed:  500 posts random from failed-corpus.json
- first-comments: same 500 success posts (fetched as part of body pull)

Each entry: {id, points, title, body_text, first_comment_by_author}
"""
from __future__ import annotations

import json
import random
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
SUCCESS_PATH = SKILL_ROOT / "patterns" / "corpus.json"
FAILED_PATH = SKILL_ROOT / "patterns" / "failed-corpus.json"
BODIES_SUCCESS_PATH = SKILL_ROOT / "patterns" / "bodies-success.json"
BODIES_FAILED_PATH = SKILL_ROOT / "patterns" / "bodies-failed.json"
FC_SUCCESS_PATH = SKILL_ROOT / "patterns" / "first-comments-success.json"

SAMPLE_SUCCESS = 300
SAMPLE_FAILED = 300
RNG_SEED = 20260618
SLEEP = 0.15
COMMENT_SCAN_LIMIT = 12  # walk first N top-level kids for author comment


def hn_item(item_id) -> dict | None:
    url = f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json"
    try:
        with urllib.request.urlopen(url, timeout=15) as r:
            return json.loads(r.read())
    except urllib.error.URLError:
        return None


def strip_html(html: str) -> str:
    import re
    out = re.sub(r"<[^>]+>", " ", html or "")
    out = out.replace("&#x27;", "'").replace("&#x2F;", "/")
    out = out.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    out = out.replace("&quot;", '"').replace("&#62;", ">").replace("&#60;", "<")
    out = re.sub(r"\s+", " ", out).strip()
    return out


def fetch_post(post_id) -> dict | None:
    item = hn_item(post_id)
    if not item or item.get("type") != "story":
        return None
    body = strip_html(item.get("text") or "")
    author = item.get("by")
    fc = None
    for kid_id in (item.get("kids") or [])[:COMMENT_SCAN_LIMIT]:
        kid = hn_item(kid_id)
        time.sleep(SLEEP / 2)
        if kid and kid.get("by") == author:
            fc = strip_html(kid.get("text") or "")
            break
    return {
        "id": str(post_id),
        "points": item.get("score"),
        "title": item.get("title"),
        "author": author,
        "body": body,
        "first_comment": fc,
    }


def fetch_batch(ids: list, label: str) -> tuple[list[dict], list[dict]]:
    bodies = []
    fcs = []
    for i, pid in enumerate(ids):
        item = fetch_post(pid)
        if item is None:
            continue
        if item["body"]:
            bodies.append({"id": item["id"], "points": item["points"], "title": item["title"], "body": item["body"]})
        if item["first_comment"]:
            fcs.append({"id": item["id"], "points": item["points"], "title": item["title"], "first_comment": item["first_comment"]})
        time.sleep(SLEEP)
        if (i + 1) % 50 == 0:
            print(f"[fetch-bc] {label} {i+1}/{len(ids)}  bodies={len(bodies)} fcs={len(fcs)}", flush=True)
    return bodies, fcs


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    rng = random.Random(RNG_SEED)

    success = json.loads(SUCCESS_PATH.read_text(encoding="utf-8"))
    failed = json.loads(FAILED_PATH.read_text(encoding="utf-8"))
    s_ids = [h["id"] for h in rng.sample(success, min(SAMPLE_SUCCESS, len(success)))]
    f_ids = [h["id"] for h in rng.sample(failed, min(SAMPLE_FAILED, len(failed)))]

    print(f"[fetch-bc] success sample: {len(s_ids)}  failed sample: {len(f_ids)}")
    s_bodies, s_fcs = fetch_batch(s_ids, "success")
    BODIES_SUCCESS_PATH.write_text(json.dumps(s_bodies, ensure_ascii=False, indent=0), encoding="utf-8")
    FC_SUCCESS_PATH.write_text(json.dumps(s_fcs, ensure_ascii=False, indent=0), encoding="utf-8")
    print(f"[fetch-bc] wrote {len(s_bodies)} success bodies, {len(s_fcs)} first comments")

    f_bodies, _ = fetch_batch(f_ids, "failed")
    BODIES_FAILED_PATH.write_text(json.dumps(f_bodies, ensure_ascii=False, indent=0), encoding="utf-8")
    print(f"[fetch-bc] wrote {len(f_bodies)} failed bodies")
    print("[fetch-bc] DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
