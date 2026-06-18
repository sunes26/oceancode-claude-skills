#!/usr/bin/env python3
"""
Run lint test fixtures against the rule set.

Only rules with `blocklist` or `patterns` fields are tested automatically.
Rules whose `check` field is natural-language description (e.g.
"len(title_body) > 60") are partially supported via a small DSL implemented
here. Rules not covered get marked SKIP with a note.

Usage:
    python tests/run-lint-tests.py
    python tests/run-lint-tests.py --verbose
    python tests/run-lint-tests.py --rule ai-saturation   # filter

Exit code 0 if all assertions hold, 1 otherwise.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RULES_PATH = ROOT / "lint" / "anti-patterns.json"
FIXTURES_PATH = Path(__file__).resolve().parent / "fixtures.json"

# Rules whose `check` field cannot be evaluated by this runner.
NL_CHECK_RULES = {
    "title-case-everything",
    "we-without-team",
    "no-context-link",
    "url-missing",
}


def strip_show_hn_prefix(title: str) -> str:
    return re.sub(r"^show hn:\s*", "", title, flags=re.IGNORECASE).strip()


def word_count(text: str) -> int:
    return len(text.split())


def evaluate_check(rule_id: str, text: str, scope: str) -> bool:
    """Evaluate simple checks that the runner understands. Returns True on hit."""
    if rule_id == "title-too-long" and scope == "title":
        return len(strip_show_hn_prefix(text)) > 60
    if rule_id == "title-too-many-words" and scope == "title":
        return word_count(strip_show_hn_prefix(text)) > 10
    if rule_id == "missing-show-hn-prefix" and scope == "title":
        return not text.startswith("Show HN:")
    if rule_id == "emoji":
        return bool(re.search(r"[\U0001F300-\U0001FAFF☀-➿]", text))
    if rule_id == "em-dash":
        return "—" in text
    if rule_id == "multiple-exclamation":
        if scope == "title":
            return text.count("!") > 1
        if scope == "body":
            return text.count("!") > 0
    if rule_id == "question-title" and scope == "title":
        return strip_show_hn_prefix(text).endswith("?")
    if rule_id == "non-english-content":
        # Allow printable ASCII and common Unicode punctuation (en/em dash, curly quotes,
        # ellipsis, etc.). Em-dash gets its own dedicated rule so we don't want to double-count.
        # CJK, Cyrillic, Greek letters, etc. → hit.
        ALLOWED_PUNCT = {
            0x2013,  # en-dash
            0x2014,  # em-dash (own rule)
            0x2018, 0x2019,  # curly single quotes
            0x201C, 0x201D,  # curly double quotes
            0x2026,  # ellipsis
            0x00A0,  # non-breaking space
        }
        for ch in text:
            cp = ord(ch)
            if cp < 0x80 or cp in ALLOWED_PUNCT:
                continue
            # Emoji range — already covered by emoji rule, skip here.
            if 0x1F300 <= cp <= 0x1FAFF or 0x2600 <= cp <= 0x27BF:
                continue
            return True
        return False
    if rule_id == "body-too-long" and scope == "body":
        return word_count(text) > 280
    if rule_id == "body-too-short" and scope == "body":
        return word_count(text) < 100
    if rule_id == "metrics-flex":
        return bool(re.search(r"\$\d+[kKmM]?|\d{2,}[kKmM]?\+? users|grew \d+", text))
    if rule_id == "all-caps-emphasis":
        # Find any token that is all-caps with length >= 3.
        rule = next((r for r in _CACHED_RULES if r["id"] == "all-caps-emphasis"), {})
        whitelist = set(rule.get("acronym_whitelist", []))
        for token in re.findall(r"\b[A-Za-z0-9]+\b", text):
            if re.match(r"^[A-Z]{3,}$", token) and token not in whitelist:
                return True
        return False
    if rule_id == "concept-without-product-name" and scope == "title":
        rule = next((r for r in _CACHED_RULES if r["id"] == "concept-without-product-name"), {})
        anti = rule.get("anti_patterns", [])
        for raw in anti:
            m = re.match(r"^/(.*)/([a-z]*)$", raw)
            if not m:
                continue
            body, flags_str = m.group(1), m.group(2)
            flags = re.IGNORECASE if "i" in flags_str else 0
            try:
                if re.search(body, text, flags):
                    return False  # anti-pattern matched → escape hatch → no hit
            except re.error:
                continue
        return True  # no anti-pattern matched → fire
    return False


# Cached rules list so check helpers can access metadata
_CACHED_RULES: list = []


def check_blocklist(blocklist: list[str], text: str) -> bool:
    lowered = text.lower()
    for phrase in blocklist:
        # Whole-word match for short tokens; substring match for multi-word phrases.
        if " " in phrase or "-" in phrase:
            if phrase.lower() in lowered:
                return True
        else:
            if re.search(rf"\b{re.escape(phrase.lower())}\b", lowered):
                return True
    return False


def check_patterns(patterns: list[str], text: str) -> bool:
    for raw in patterns:
        # Strip leading / trailing slashes and trailing flags, support /i suffix.
        m = re.match(r"^/(.*)/([a-z]*)$", raw)
        if not m:
            try:
                if re.search(raw, text):
                    return True
            except re.error:
                continue
            continue
        body, flags_str = m.group(1), m.group(2)
        flags = 0
        if "i" in flags_str:
            flags |= re.IGNORECASE
        try:
            if re.search(body, text, flags):
                return True
        except re.error:
            continue
    return False


def rule_applies_to_scope(rule: dict, scope: str) -> bool:
    rs = rule.get("scope", "both")
    if rs == "both":
        return True
    if rs == "submission":
        return False  # not checkable from text alone
    return rs == scope


def lint_text(rules: list[dict], text: str, scope: str) -> tuple[list[str], list[str]]:
    """Return (hit_rule_ids, skipped_rule_ids)."""
    hits = []
    skipped = []
    for rule in rules:
        if not rule_applies_to_scope(rule, scope):
            continue
        rid = rule["id"]
        hit = False
        if "blocklist" in rule:
            hit = check_blocklist(rule["blocklist"], text)
        elif "patterns" in rule:
            hit = check_patterns(rule["patterns"], text)
        elif "pattern" in rule:
            hit = check_patterns([rule["pattern"]], text)
        elif rid in NL_CHECK_RULES:
            skipped.append(rid)
            continue
        else:
            hit = evaluate_check(rid, text, scope)
        if hit:
            hits.append(rid)
    return hits, skipped


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--rule", help="Only show fixtures whose expected hits include this rule")
    args = parser.parse_args()

    rules_doc = json.loads(RULES_PATH.read_text(encoding="utf-8"))
    rules = rules_doc["rules"]
    _CACHED_RULES.clear()
    _CACHED_RULES.extend(rules)
    fixtures_doc = json.loads(FIXTURES_PATH.read_text(encoding="utf-8"))
    cases = fixtures_doc["cases"]

    passed = 0
    failed = 0
    skipped = 0
    failures = []

    for case in cases:
        if args.rule and args.rule not in case.get("expect_hits", []):
            continue

        name = case["name"]
        text = case["input"]
        scope = case["scope"]
        expected = set(case.get("expect_hits", []))

        if case.get("manual_only"):
            skipped += 1
            print(f"SKIP  {name}  (manual_only)")
            continue

        actual, skipped_ids = lint_text(rules, text, scope)
        actual_set = set(actual)

        if actual_set == expected:
            passed += 1
            mark = "PASS"
        else:
            failed += 1
            mark = "FAIL"
            missing = expected - actual_set
            extra = actual_set - expected
            failures.append((name, missing, extra, actual, expected))

        if args.verbose or mark == "FAIL":
            print(f"{mark}  {name}")
            if args.verbose:
                print(f"      input: {text[:80]}{'...' if len(text)>80 else ''}")
                print(f"      expected: {sorted(expected) or 'no hits'}")
                print(f"      actual:   {sorted(actual_set) or 'no hits'}")
                if skipped_ids:
                    print(f"      skipped rules (manual): {skipped_ids}")
            if mark == "FAIL":
                if missing:
                    print(f"      MISSING (expected but not hit): {sorted(missing)}")
                if extra:
                    print(f"      EXTRA (hit but not expected): {sorted(extra)}")

    print()
    print(f"== summary ==  passed={passed}  failed={failed}  skipped={skipped}  total={passed+failed+skipped}")
    if failures:
        print(f"\nfailures listed above. {len(failures)} fixture(s) need attention.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
