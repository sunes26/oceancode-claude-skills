#!/usr/bin/env python3
"""
Train a title signal scorer from the success and failure corpora.

Model: Naive Bayes over title token unigrams + bigrams + select structural
features. Output: log-odds weight per feature, saved to
`lint/title-scorer.json`.

Limitation acknowledged up front: a title alone explains only ~15-25% of
score variance on HN (timing, current front-page competition, network
effects, and the actual artifact dominate). This scorer reports HONEST
relative-confidence, not a points prediction. Output is a 0-100 signal
score, NOT "this will get N points".

Calibration: the success corpus is the top 25% of all-time Show HN
(>676 pts), and the failure corpus is the recent ≤5 pt mass. Base rate
of being a "success" in the full population of Show HN is ~1%, NOT
50/50 as our training set implies. The scorer's output is therefore a
RELATIVE signal, intentionally uncalibrated to absolute probability.
This is communicated in lint/scorer.md.

Usage:
    python tools/train-scorer.py
    python tools/train-scorer.py --validate   # print top/bottom scoring examples
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
SUCCESS_PATH = SKILL_ROOT / "patterns" / "corpus.json"
FAILED_PATH = SKILL_ROOT / "patterns" / "failed-corpus.json"
WEIGHTS_PATH = SKILL_ROOT / "lint" / "title-scorer.json"

PREFIX_RE = re.compile(r"^show hn:\s*", re.IGNORECASE)
TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z\-']{1,}")

# Smoothing constant for unseen tokens.
ALPHA = 1.0
# Keep features that appear at least this often across both classes combined.
MIN_FREQ = 5
# Cap the saved feature list to this many top-magnitude weights.
MAX_FEATURES = 800
# Per-feature log-odds cap. Prevents single-feature saturation.
# +/- 1.5 corresponds to ~82% probability shift from a single feature alone.
# Without this cap a single rare feature could swing the score from 5 to 95.
PER_FEATURE_CAP = 1.5
# Total log-odds cap applied at scoring time.
# +/- 3.0 bounds output to ~5%-95% range. Multiple features can still
# combine but cannot push past these soft limits.
TOTAL_LOGODDS_CAP = 3.0


def title_body(title: str) -> str:
    return PREFIX_RE.sub("", title or "").strip()


def tokenize(text: str) -> list[str]:
    # Lowercase tokens, drop standalone digits, drop length-1 tokens.
    return [t.lower() for t in TOKEN_RE.findall(text) if len(t) > 1]


def features_for(text: str) -> list[str]:
    """Title features: unigrams + bigrams + structural markers."""
    tokens = tokenize(text)
    unigrams = list(tokens)
    bigrams = [f"{a}_{b}" for a, b in zip(tokens, tokens[1:])]

    body = title_body(text)
    structural: list[str] = []
    if len(body) > 60:
        structural.append("STRUCT_over_60_chars")
    if len(body.split()) > 10:
        structural.append("STRUCT_over_10_words")
    if "–" in body:
        structural.append("STRUCT_en_dash")
    if "—" in body:
        structural.append("STRUCT_em_dash")
    if re.search(r"\bI\b", body):
        structural.append("STRUCT_first_person_I")
    if re.search(r"\b[Ww]e\b", body):
        structural.append("STRUCT_first_person_we")
    if re.search(r"\b(AI|LLM|GPT|ChatGPT|AGI)\b", body):
        structural.append("STRUCT_AI_token")
    if re.search(r"\b[Aa]gentic\b", body):
        structural.append("STRUCT_agentic")
    if re.search(r"\bopen[\s-]?source\b", body, re.IGNORECASE):
        structural.append("STRUCT_open_source")
    if body.endswith("?"):
        structural.append("STRUCT_question")
    if re.search(r"\bI\s+(made|built|created|wrote)\b", body):
        structural.append("STRUCT_I_built")
    if re.search(r"\bself[\s-]?host", body, re.IGNORECASE):
        structural.append("STRUCT_self_hosted")
    if re.search(r"\(MIT\)|\(GPL\)|\(Apache\)|\(BSD\)", body):
        structural.append("STRUCT_license_badge")

    return unigrams + bigrams + structural


def train(success: list[dict], failed: list[dict]) -> dict:
    s_features = Counter()
    f_features = Counter()
    for h in success:
        for feat in features_for(h.get("title") or ""):
            s_features[feat] += 1
    for h in failed:
        for feat in features_for(h.get("title") or ""):
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
        # Smoothed log-likelihood ratio.
        p_s = (cs + ALPHA) / (n_s + 2 * ALPHA)
        p_f = (cf + ALPHA) / (n_f + 2 * ALPHA)
        raw_log_odds = math.log(p_s / p_f)
        # Cap to prevent any single feature from dominating the score.
        capped = max(-PER_FEATURE_CAP, min(PER_FEATURE_CAP, raw_log_odds))
        weights[feat] = {
            "log_odds": round(capped, 4),
            "raw_log_odds": round(raw_log_odds, 4),
            "success_count": cs,
            "failed_count": cf,
        }

    # Trim to top |weight| features for shipping size.
    sorted_feats = sorted(weights.items(), key=lambda kv: -abs(kv[1]["log_odds"]))
    trimmed = dict(sorted_feats[:MAX_FEATURES])

    # Class priors (intentionally uncalibrated; see file docstring).
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
            "Title-only signal. Body, timing, and competition dominate the actual outcome.",
            "Success base rate is ~1% of all Show HN submissions, not 50% as the training split implies.",
            "Output is a relative confidence (0-100), NOT a predicted point count.",
            "Refresh when corpora are refreshed; trend words shift annually.",
        ],
        "weights": trimmed,
    }


def score_title(title: str, model: dict) -> float:
    """Return a 0-100 signal score. 50 = neutral; >50 leans winner; <50 leans loser."""
    feats = features_for(title)
    log_odds = model["training"]["intercept"]
    weights = model["weights"]
    for feat in feats:
        if feat in weights:
            log_odds += weights[feat]["log_odds"]
    # Cap total log-odds so multiple correlated features cannot saturate
    # the sigmoid beyond the soft probability band. The cap is model-driven
    # (training metadata), with a stdlib fallback if absent.
    cap = model["training"].get("total_logodds_cap", 3.0)
    log_odds = max(-cap, min(cap, log_odds))
    p = 1.0 / (1.0 + math.exp(-log_odds))
    return round(100 * p, 1)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--validate", action="store_true")
    args = parser.parse_args()

    # Force utf-8 for stdout so titles with en-dash etc. print on Windows cp949.
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

    success = json.loads(SUCCESS_PATH.read_text(encoding="utf-8"))
    failed = json.loads(FAILED_PATH.read_text(encoding="utf-8"))
    print(f"[train-scorer] success n={len(success)}  failed n={len(failed)}")

    model = train(success, failed)
    WEIGHTS_PATH.write_text(
        json.dumps(model, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[train-scorer] wrote {len(model['weights'])} features -> {WEIGHTS_PATH}")

    if args.validate:
        print("\n=== top 10 success titles by signal score ===")
        scored = [(score_title(h["title"], model), h) for h in success[:50]]
        scored.sort(key=lambda kv: -kv[0])
        for s, h in scored[:10]:
            print(f"  {s:>5.1f}  [{h['points']:>5}]  {h['title'][:75]}")
        print("\n=== top 10 failed titles by signal score (should be LOW) ===")
        scored_f = [(score_title(h["title"], model), h) for h in failed[:200]]
        scored_f.sort(key=lambda kv: -kv[0])
        for s, h in scored_f[:5]:
            print(f"  {s:>5.1f}  [{h['points']:>5}]  {h['title'][:75]}")
        print("\n=== bottom 10 failed titles by signal score ===")
        scored_f.sort(key=lambda kv: kv[0])
        for s, h in scored_f[:10]:
            print(f"  {s:>5.1f}  [{h['points']:>5}]  {h['title'][:75]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
