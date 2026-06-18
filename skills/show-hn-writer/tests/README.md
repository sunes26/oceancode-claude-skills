# Lint test fixtures

Regression tests for `lint/anti-patterns.json`. Each fixture in `fixtures.json` is a `{name, input, scope, expect_hits, ...}` row asserting that running the full lint pass produces exactly the listed rule ids.

## Run

```
python tests/run-lint-tests.py             # all fixtures
python tests/run-lint-tests.py --verbose   # show input + actual + expected per case
python tests/run-lint-tests.py --rule ai-saturation   # filter to fixtures that expect this rule
```

Exit 0 = all pass. Exit 1 = at least one fixture failed; failure list printed.

## Coverage

The runner evaluates blocklist and regex rules automatically plus a handful of `check:` rules that are simple enough to express in Python (`title-too-long`, `body-too-short`, `question-title`, `non-english-content`, etc.). Rules whose `check:` field is a natural-language description that the runner cannot evaluate get marked `SKIP (manual_only)`:

- `title-case-everything`
- `all-caps-emphasis`
- `we-without-team`
- `no-context-link`
- `url-missing`
- `concept-without-product-name`

These need an LLM agent to evaluate during real skill use. Their fixture rows are still in `fixtures.json` for documentation but flagged `manual_only: true`.

## When to add a fixture

Add a new fixture whenever you:

1. Add a new rule to `anti-patterns.json` → add at least one positive fixture (text that triggers it) and verify it does not over-trigger on clean text.
2. Change a blocklist or pattern → add a fixture for the new addition.
3. Hit a false positive in real use → add the offending text as a fixture with the corrected expectation.

## Interaction tests

Several fixtures intentionally combine multiple violations (e.g. `weak-ask-body` expects `weak-ask`, `multiple-exclamation`, and `body-too-short` all firing) to catch regressions where one rule starts swallowing or shadowing another.

## Limitations

- The runner is not the production lint pass — it is a regression harness. The skill itself relies on an LLM applying the rules per `lint/checker.md`. Fixtures here ensure the rule data is well-formed and self-consistent.
- Domain-conditional rules (`hype-words-ai`, `hype-words-devtool`, `hype-words-saas`) always run in the test harness regardless of `domain` input. Real skill use filters them by domain per the SKILL.md detection step.
