#!/usr/bin/env python3
"""
Train a body text signal scorer from fetched Show HN post bodies.

Model: Naive Bayes over body token unigrams + bigrams + structural features.
Output: lint/body-scorer.json

Usage:
    python tools/train-body-scorer.py
    python tools/train-body-scorer.py --validate
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from collections import Counter
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
SUCCESS_PATH = SKILL_ROOT / "patterns" / "bodies-success.json"
FAILED_PATH = SKILL_ROOT / "patterns" / "bodies-failed.json"
WEIGHTS_PATH = SKILL_ROOT / "lint" / "body-scorer.json"

TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z\-']{1,}")
ALPHA = 1.0
MIN_FREQ = 3
MAX_FEATURES = 60   # structural-only: no token noise at small n
PER_FEATURE_CAP = 1.5
TOTAL_LOGODDS_CAP = 3.0

# At n=112 success / n=116 failed, token unigrams overfit badly — single-post words
# cap at +1.5 instantly. Only structural (hand-crafted regex) features are reliable.
STRUCTURAL_ONLY = True


def tokenize(text: str) -> list[str]:
    return [t.lower() for t in TOKEN_RE.findall(text or "") if len(t) > 1]


def features_for(body: str) -> list[str]:
    body = body or ""
    tokens = tokenize(body)
    unigrams = [] if STRUCTURAL_ONLY else list(tokens)
    bigrams = [] if STRUCTURAL_ONLY else [f"{a}_{b}" for a, b in zip(tokens, tokens[1:])]

    structural: list[str] = []
    words = body.split()
    word_count = len(words)

    if word_count < 30:
        structural.append("STRUCT_very_short")
    elif word_count < 80:
        structural.append("STRUCT_short")
    elif word_count > 300:
        structural.append("STRUCT_long")

    if re.search(r"github\.com/", body, re.IGNORECASE):
        structural.append("STRUCT_has_github_link")
    if re.search(r"https?://", body):
        structural.append("STRUCT_has_any_link")
    if re.search(r"\bdemo\b|\blive\b.*\bhttps?://|\btry it\b", body, re.IGNORECASE):
        structural.append("STRUCT_has_demo")
    if re.search(r"\bfree\b.*\bopen[\s-]?source\b|\bopen[\s-]?source\b.*\bfree\b", body, re.IGNORECASE):
        structural.append("STRUCT_free_open_source")
    if re.search(r"\bself[\s-]?host", body, re.IGNORECASE):
        structural.append("STRUCT_self_hosted")
    if body.count("?") >= 2:
        structural.append("STRUCT_multiple_questions")
    elif body.count("?") == 1:
        structural.append("STRUCT_one_question")
    if re.search(r"\bfeedback\b", body, re.IGNORECASE):
        structural.append("STRUCT_asks_feedback")
    if re.search(r"\bdocker\b", body, re.IGNORECASE):
        structural.append("STRUCT_mentions_docker")
    if re.search(r"\bpric\w+\b|\bfree\s+tier\b|\bopen[\s-]?source\b", body, re.IGNORECASE):
        structural.append("STRUCT_mentions_pricing_or_oss")
    if re.search(r"\bscreenshot\b|\bdemo\s+gif\b|\brecording\b", body, re.IGNORECASE):
        structural.append("STRUCT_mentions_screenshot")
    if re.search(r"\bI\s+(built|made|created|wrote|spent|started)\b", body):
        structural.append("STRUCT_personal_story")
    if re.search(r"\bwould\s+love\s+(to\s+hear|your|any)\b|\bany\s+(feedback|thoughts|suggestions)\b", body, re.IGNORECASE):
        structural.append("STRUCT_explicit_feedback_request")

    return unigrams + bigrams + structural


def train(success: list[dict], failed: list[dict]) -> dict:
    s_features = Counter()
    f_features = Counter()
    for h in success:
        for feat in features_for(h.get("body") or ""):
            s_features[feat] += 1
    for h in failed:
        for feat in features_for(h.get("body") or ""):
            f_features[feat] += 1

    n_s = len(success)
    n_f = len(failed)
    all_features = set(s_features) | set(f_features)

    weights: dict[str, dict] = {}
    for feat in all_features:
        cs = s_features[feat]
        cf = f_features[feat]
        if cs + cf < MIN_FREQ:
            continue
        p_s = (cs + ALPHA) / (n_s + 2 * ALPHA)
        p_f = (cf + ALPHA) / (n_f + 2 * ALPHA)
        raw_log_odds = math.log(p_s / p_f)
        capped = max(-PER_FEATURE_CAP, min(PER_FEATURE_CAP, raw_log_odds))
        weights[feat] = {
            "log_odds": round(capped, 4),
            "raw_log_odds": round(raw_log_odds, 4),
            "success_count": cs,
            "failed_count": cf,
        }

    sorted_feats = sorted(weights.items(), key=lambda kv: -abs(kv[1]["log_odds"]))
    trimmed = dict(sorted_feats[:MAX_FEATURES])

    log_prior_s = math.log((n_s + ALPHA) / (n_s + n_f + 2 * ALPHA))
    log_prior_f = math.log((n_f + ALPHA) / (n_s + n_f + 2 * ALPHA))
    intercept = log_prior_s - log_prior_f

    return {
        "schema_version": 1,
        "model": "naive_bayes_log_odds",
        "training": {
            "success_n": n_s,
            "failed_n": n_f,
            "min_feature_freq": MIN_FREQ,
            "alpha": ALPHA,
            "per_feature_cap": PER_FEATURE_CAP,
            "total_logodds_cap": TOTAL_LOGODDS_CAP,
            "feature_count_kept": len(trimmed),
            "intercept": round(intercept, 4),
        },
        "caveats": [
            "Body-only signal. Trained on 112 success + 116 failed bodies — small sample, treat as directional.",
            "Success = top-1% Show HN (>=262pts). Failed = random <=5pt sample.",
            "Output is a relative confidence (0-100), NOT a quality guarantee.",
            "Structural features (STRUCT_*) are more reliable than token unigrams at this sample size.",
        ],
        "weights": trimmed,
    }


def score_body(body: str, model: dict) -> float:
    feats = features_for(body)
    log_odds = model["training"]["intercept"]
    weights = model["weights"]
    for feat in feats:
        if feat in weights:
            log_odds += weights[feat]["log_odds"]
    cap = model["training"].get("total_logodds_cap", 3.0)
    log_odds = max(-cap, min(cap, log_odds))
    p = 1.0 / (1.0 + math.exp(-log_odds))
    return round(100 * p, 1)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--validate", action="store_true")
    args = parser.parse_args()

    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

    success = json.loads(SUCCESS_PATH.read_text(encoding="utf-8"))
    failed = json.loads(FAILED_PATH.read_text(encoding="utf-8"))
    print(f"[train-body] success n={len(success)}  failed n={len(failed)}")

    model = train(success, failed)
    WEIGHTS_PATH.write_text(
        json.dumps(model, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[train-body] wrote {len(model['weights'])} features -> {WEIGHTS_PATH}")

    if args.validate:
        print("\n=== top structural features by |log_odds| ===")
        struct_w = {k: v for k, v in model["weights"].items() if k.startswith("STRUCT_")}
        for feat, w in sorted(struct_w.items(), key=lambda kv: -abs(kv[1]["log_odds"]))[:15]:
            print(f"  {w['log_odds']:+.3f}  {feat}  (s={w['success_count']} f={w['failed_count']})")

        print("\n=== top 10 token features (winner-coded) ===")
        tok_w = {k: v for k, v in model["weights"].items() if not k.startswith("STRUCT_")}
        for feat, w in sorted(tok_w.items(), key=lambda kv: -kv[1]["log_odds"])[:10]:
            print(f"  {w['log_odds']:+.3f}  {feat}  (s={w['success_count']} f={w['failed_count']})")

        print("\n=== top 10 token features (loser-coded) ===")
        for feat, w in sorted(tok_w.items(), key=lambda kv: kv[1]["log_odds"])[:10]:
            print(f"  {w['log_odds']:+.3f}  {feat}  (s={w['success_count']} f={w['failed_count']})")

        print("\n=== body scores for sample success posts ===")
        for h in success[:10]:
            s = score_body(h.get("body") or "", model)
            title_short = (h.get("title") or "")[:50]
            print(f"  {s:>5.1f}  [{h.get('points'):>4}]  {title_short}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
