# Failure signals (negative dataset analysis)

## Methodology

Two corpora compared, both derived from the full Show HN corpus (n=196,847 entries, 2009-03 to 2026-06):

| Corpus | Source | n | Definition |
|---|---|---|---|
| Success | `corpus.json` | 1,945 | Show HN posts with ≥262 points = true top 1% of the full distribution |
| Failed | `failed-corpus.json` | 5,000 | Random sample of ≤5 point posts (74.3% of the full corpus is in this bucket — this is the modal Show HN outcome) |

Distribution of the full Show HN corpus (n=196,847):
- ≤1pt: 28.3%
- ≤5pt: 74.3%
- ≥30pt: 9.0%
- ≥100pt: 3.8%
- ≥262pt: 1.0% (success cutoff)
- ≥500pt: 0.3%
- ≥1000pt: <0.05%

Both corpora are stable across refreshes at this size. Prior versions of this file used n=999 vs n=862 from a relevance-ranked top-1000 query, which introduced selection bias toward Algolia's relevance algorithm rather than honest point ranking. The new corpus uses date-chunked exhaustive fetching and selects by points.

## Lift table — patterns that discriminate

Lift = success_freq / failed_freq. >1.5 = success-favored, <0.67 = failure-favored.

### Strong success signals (lift ≥ 2.0)

| Pattern | Success% | Failed% | Lift |
|---|---|---|---|
| `self-hosted` in title | 1.4% | 0.4% | **3.79** |
| `open-source` in title | 7.4% | 2.9% | 2.54 |
| First-person `I` | 17.1% | 7.4% | **2.29** |
| `I made/built/wrote` | 10.6% | 4.9% | **2.18** |
| First-person `we` (when used) | 1.4% | 0.9% | 1.56 |

**Takeaways:**

1. **Self-hosted is the single strongest title signal** when honest. Only 1.4% of winners use it (small category), but those who do beat the failure rate by 3.79x. Prior smaller-sample analysis missed this.
2. First-person builder voice ("I built/made X") remains a top signal but at 2.18x — less dominant than the prior 3.70x estimate. The earlier number was inflated by relevance-ranking bias in the old corpus.
3. Open-source mention is genuinely a strong signal at 2.54x lift. Pair with license badge (Formula 12a) for compounding effect.

### Strong failure signals (lift ≤ 0.5)

| Pattern | Success% | Failed% | Lift |
|---|---|---|---|
| Generic hype words (revolutionary, seamless, etc.) | 0.1% | 0.3% | **0.17** |
| `em-dash` (—) in title | 0.1% | 0.1% | 0.43 |
| `AI` / `LLM` / `GPT` in title | 5.0% | 11.6% | 0.44 |
| `RAG` in title | 0.1% | 0.2% | 0.51 |

**Takeaways:**

1. **Hype words remain catastrophic** — 0.17x lift is the most extreme negative signal in the data. The reject-level rule is correct.
2. **AI saturation moderated**: prior corpus showed 0.21x lift, true corpus shows 0.44x. AI in title is still a negative signal but not as catastrophic as previously documented. Rule severity stays at `warn`, not `reject`.

### Reframed patterns vs prior assumptions

| Pattern | Prior estimate | True lift | Change |
|---|---|---|---|
| `agentic` / `agent` | 0.12x (strong failure) | 0.73x (near-neutral) | Prior was a small-sample artifact. Loosen rule. |
| En-dash separator (`–`) | 0.64x (failure-coded) | 1.12x (slight winner) | **Reversal.** Formula 2 is a genuine baseline, not a failure pattern. |

The earlier en-dash finding ("failed posts use it MORE") was an artifact of n=999 vs n=862 with Algolia relevance bias. With n=1,945 vs n=5,000 the pattern is approximately neutral or slightly winner-favored. Formula 2 status restored in `title-formulas.md`.

## Title length — minor signal at this scale

| Metric | Success | Failed |
|---|---|---|
| Median chars | 50 | 52 |
| Median words | 8 | 8 |
| % over 60 chars | 27.5% | 29.4% |

Length difference is small (27.5% vs 29.4% over 60 chars). The hard cap remains at 60 chars for readability and mobile rendering, not because the data alone strongly justifies it.

## New lint rule adjustments

Three rule adjustments derived from the expanded data:

1. **`buzzword-stack-2026` softened**: `agentic` is no longer a strong negative on its own (lift 0.73). Keep the rule but lower confidence in the rationale. Re-evaluate annually.
2. **`ai-saturation` retained at warn**: still 0.44x lift, but the prior 0.21x figure overstated the penalty. Rule severity stays at `warn`, fix text updated.
3. **New positive signals to celebrate, not lint**: `self-hosted` (3.79x) and `open-source` (2.54x) are not currently surfaced in the title scorer's structural features — already covered by the NB unigram weights. No new rules needed; the scorer captures them automatically.

## Methodology note: corpus refresh

Run `tools/fetch-corpus-full.py` quarterly to refresh `all-corpus.json`, then `tools/fetch-truncated.py` to recover any 1000-cap weeks, then `tools/build-corpora.py` to derive `corpus.json` and `failed-corpus.json` at honest top-1% / bottom-mass thresholds. The final step retrains the scorer via `tools/train-scorer.py`. All four scripts are idempotent.
