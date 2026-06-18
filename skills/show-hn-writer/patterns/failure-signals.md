# Failure signals (negative dataset analysis)

## Methodology

Two corpora compared:

| Corpus | Source | n | Definition |
|---|---|---|---|
| Success | `corpus.json` | 999 | Show HN posts with >676 points (top 25% historically) |
| Failed | `failed-corpus.json` | 861 | Recent Show HN posts with ≤5 points (mode of the distribution) |

Failed corpus pulled via `https://hn.algolia.com/api/v1/search_by_date?tags=show_hn`, 1000 most recent Show HN. After filtering for points ≤ 5: 861 posts. Median = 2 points, p75 = 4 points. These are not borderline cases; they are posts that landed and died.

## Caveat — temporal confound

Success corpus spans HN history (oldest 2008, newest 2026). Failed corpus is recent (last ~3-6 weeks). Differences could reflect:

- A genuine signal: the pattern is bad regardless of era
- An era shift: the pattern was fine in 2020 but is exhausted in 2026

Where the data suggests an era shift, this file flags it. To resolve, re-fetch a recent-only success cohort and compare (TODO).

## Lift table — patterns that discriminate

Lift = success_freq / failed_freq. >1.5 = success-favored. <0.67 = failure-favored.

### Strong success signals (lift ≥ 2.0)

| Pattern | Success% | Failed% | Lift |
|---|---|---|---|
| `I made/built X` | 12.9% | 3.5% | **3.70** |
| First-person `I` | 21.5% | 6.2% | **3.49** |
| First-person `we` | 1.7% | 0.6% | 2.93 |
| `modern` in title | 1.2% | 0.3% | 3.44 (small n) |
| `easy` in title | 0.5% | 0.2% | 2.15 (small n) |

**Takeaway:** Solo builder voice ("I built/made X") is the single most discriminating winning signal. Confirms Formula 1 strength.

### Strong failure signals (lift ≤ 0.5)

| Pattern | Success% | Failed% | Lift |
|---|---|---|---|
| `AI` / `LLM` / `GPT` in title | 4.5% | **21.4%** | **0.21** |
| `agentic` / `agent` | 0.1% | 0.8% | 0.12 |
| `RAG` | 0.1% | 0.7% | 0.14 |
| Hype words (revolutionary, seamless, etc.) | 0.1% | 0.3% | 0.29 |
| Colon inside title body (not the `Show HN:` prefix) | 1.1% | 2.3% | 0.47 |

**Takeaway:** AI/LLM/GPT in the title is a strong negative signal in 2026. Possible explanations:
- Saturation: HN front page already covers AI heavily, novelty bar is high
- Reader fatigue: title with "AI" gets skipped by readers who have seen 50 this month
- Selection: posts that ONLY mention AI in the title often have nothing else distinctive

Likely all three. Practical guidance: if your project uses LLMs, lead with what it DOES, not that it uses AI. Compare:

- Failed: `Show HN: Reyn – local-first AI that journals and recalls your work` (4 pts)
- Hypothetical reframe: `Show HN: Reyn – a local-first journal that remembers what you actually did`

The AI is incidental; the user-facing capability is the lede.

### Reframed patterns (lift inversion vs prior assumption)

| Pattern | Prior assumption | Reality |
|---|---|---|
| En-dash separator (`–`) | Winning formula (32.8% of success) | Used MORE in failed (50.9%). It is the default HN title format; success comes from departing from defaults. |

**Implication for Formula 2 (`Product – one-line value`):** still acceptable, still common, but no longer presented as a winning shortcut. Formula 1 (first-person builder) is the stronger lever.

## Title length validates the hard cap

| Metric | Success | Failed |
|---|---|---|
| Median chars | 50 | 59 |
| Median words | 8 | 9 |
| % over 60 chars | 27.3% | 44.5% |

Posts over 60 chars are 1.6x more likely to be in the failed bucket than the success bucket. The `title-too-long` lint reject at >60 is data-validated.

## Qualitative review — 20 failed titles

Most failed titles fall into 2-3 patterns:

1. **Buzzword pile-up:** `Righthand – Autonomous AI assistants with skills, goals, and a CLI` (2 pts). Three trend-words in 9 words. No anchor.
2. **Concept-only, no artifact:** `Local personal data redaction for any AI tools` (3 pts). No product name, no concrete demo.
3. **Niche without bridge:** `Pitch-by-pitch baseball simulation app to simulate games and seasons` (2 pts). Audience is small; title does not pull a non-baseball reader in.
4. **AI-incidental:** `Reyn – local-first AI that journals and recalls your work` (4 pts). The AI is not the product; the journaling is. Title buries the lede.

## New lint rules derived

Three rules added to `lint/anti-patterns.json`:

- `ai-saturation`: warn if title contains `AI`, `LLM`, `GPT`, `ChatGPT` as a standalone token. Suggested fix: lead with what the product does.
- `buzzword-stack-2026`: warn on `agentic`, `RAG`, `LLM-native`, `AI-powered`, `AI-first`. These are 2026-specific era markers; revisit annually.
- `concept-without-product-name`: warn if title contains no capitalized noun that could be a product name and no first-person verb (`I built`). Catches "Local personal data redaction for any AI tools" type titles.

## Refresh

`tools/refresh-corpus.py` updated to also fetch the recent sample and write `failed-corpus.json`. Re-running the script quarterly keeps failure signals current as the HN zeitgeist shifts.
