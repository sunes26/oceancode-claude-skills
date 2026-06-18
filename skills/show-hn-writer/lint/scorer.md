# Title signal scorer

A small Naive Bayes model over title tokens + structural features. Trained by `tools/train-scorer.py` from `patterns/corpus.json` (success) and `patterns/failed-corpus.json` (failure). Weights stored in `lint/title-scorer.json`.

## What it does

Given a candidate title, return a 0-100 score where:

- **75-100**: title resembles the winner corpus on tokens AND structure
- **50-74**: mixed — some winner patterns, some loser patterns
- **25-49**: leans toward loser patterns (AI-saturation, long titles, buzzwords)
- **0-24**: heavily loser-coded — likely to flop on tokens alone

## What it does NOT do

- Predict a point count. The scorer outputs a relative confidence, not "this will get N points".
- Account for timing, current front-page competition, who the author is, follower network, the actual product quality, or HN luck. These factors dominate the real outcome.
- Calibrate to absolute probability. The training set is artificially balanced (999 success vs 862 failure), while the true Show HN population is roughly 1% success / 99% failure. So a raw score of 80 does NOT mean "80% chance of becoming a top post". It means "this title's token signal places it in the upper portion of the training-set distribution".

These limitations are stated upfront in the scorer file itself (`title-scorer.json`'s `caveats` field).

## How to apply at runtime

Per title variant:

1. Tokenize the title body (after `Show HN:`) into unigrams and bigrams.
2. Compute structural features (length over 60 chars, `I built`, AI token, en-dash, etc.).
3. Sum the log-odds for each feature found in `title-scorer.json.weights`, plus the intercept.
4. Apply sigmoid: `p = 1 / (1 + exp(-log_odds))`.
5. Multiply by 100 and round.

Pseudocode is in `tools/train-scorer.py::score_title`. An LLM applying this skill should follow the same algorithm with the weights file.

## How to use the score in output

Add a line per variant alongside the lint result:

```
### Variant A — Formula 1: I built X
> Show HN: I built a self-hosted cost tracker (MIT)
- chars: 44 / words: 10
- lint: ✓ passes
- signal score: 92 / 100 (strong winner-pattern match)
```

The score is informational, NOT a gate. A variant scoring 30 might still be the right choice if it carries the most honest framing. A variant scoring 95 might still need a body that delivers.

Ranking the 3 variants by signal score is a reasonable tie-breaker after formula diversity is enforced.

## Calibration interpretation guide

When showing the score to the user, pair it with a one-line interpretation:

| Score | Interpretation to display |
|---|---|
| 90-100 | Token signal aligns strongly with the winner corpus |
| 70-89 | Above-median winner signal |
| 50-69 | Mixed signal, no strong push either way |
| 30-49 | Below-median signal, contains some loser patterns |
| 0-29 | Title carries multiple known loser patterns |

Never display the score without one of these labels. A bare "73" reads as a probability and is misleading.

## Refresh

`tools/train-scorer.py` reads the current corpora and overwrites `title-scorer.json`. Re-run whenever:

- `refresh-corpus.py` updates the corpora
- A new lint rule is added that reflects a token pattern (e.g. a new buzzword joins `buzzword-stack-2026`)
- The annual trend-word review changes the AI/dev-tool/SaaS blocklists

The training script ships smoothed (alpha=1) and trimmed (top 800 features) for ship size. Adjust constants at the top of the file if needed.

## Lint and scorer can productively disagree

The lint rules judge strategic risk (controversy, hype, vote begging). The scorer judges token-pattern fit. They can rank the same title oppositely. This is intentional.

Worked example from the Spanlens dry-run (2026-06-18):

| Title | Lint | Scorer | Why |
|---|---|---|---|
| `Open-source alternative to Langfuse and Helicone` | ⚠ competitor-callout | 99.8 | Maximum token fit, but invites a flame war if a competitor's employee spots it |
| `I built a self-hosted LLM cost tracker (MIT)` | ⚠ ai-saturation | 16.4 | `I built` is winner-coded; `LLM` token alone drags the score below 20 |
| `Revolutionary AI-powered agentic platform` | ✗ rejected by 3 rules | 2.5 | Both axes agree: bad |

Display both signals to the user. Do not let one override the other automatically. The user makes the trade-off.

## Known failure modes

1. **Same title pattern, different topic**: "I built X" scores high regardless of whether X is genuinely interesting. The model has no way to evaluate the X.
2. **Long-tail tokens**: rare project names default to neutral. New domain words (a hot framework released this month) start at 0 weight until the corpus refreshes.
3. **Subject-verb agreement of intent**: a title like "I built an AI agent" hits both `STRUCT_I_built` (+) and `STRUCT_AI_token` and `STRUCT_agentic` (-). The model averages, but the user may interpret the AI mention differently from the model.
4. **Adversarial prompting**: a user can ask the skill to generate text designed to score 100. The model will obey. The score is a heuristic, not a quality guarantee.

All four are documented for the user to understand the score as a token-level diagnostic, not a verdict.
