# Engagement signal analysis

Points and comments are correlated but not identical. Most Show HN posts that get upvotes also get comments (Pearson r = 0.844), but the **ratio** varies — and titles can be tuned for one or the other.

## Methodology

- Source: `all-corpus.json` (196,847 entries) filtered to posts with ≥100 points (n=7,289 — top 4%)
- For each post: `comments / points` ratio
- Top 20% by ratio = "discussion-heavy" (n=1,457) — posts where readers wanted to debate
- Bottom 20% by ratio = "viral-only" (n=1,458) — posts where readers upvoted and moved on
- Median ratio: 0.327 comments per point (so a 200pt post averages ~65 comments)

Lift = `freq(token in discussion-heavy) / freq(token in viral-only)`.

## Discussion-skewing tokens (lift > 2.0)

| Lift | Token | Discussion freq | Viral freq |
|---|---|---|---|
| 2.95 | `you` | 59 | 19 |
| 2.75 | `app` | 88 | 31 |
| 2.36 | `built` | 92 | 38 |
| 2.13 | `website` | 34 | 15 |
| 2.05 | `new` | 45 | 21 |

**Read:** consumer-facing artifacts (`app`, `website`, "for you") spark debate. The first-person `built` ranks here too — readers want to ask the author questions.

## Viral-only tokens (lift > 2.0 toward viral side)

| Lift | Token | Viral freq | Discussion freq |
|---|---|---|---|
| 5.67 | `library` | 51 | 8 |
| 4.78 | `interactive` | 43 | 8 |
| 4.13 | `learning` | 33 | 7 |
| 3.83 | `python` | 69 | 17 |
| 3.77 | `data` | 49 | 12 |
| 2.92 | `editor` | 35 | 11 |
| 2.83 | `source` | 34 | 11 |
| 2.74 | `open-source` | 85 | 30 |
| 2.63 | `open` | 42 | 15 |
| 2.33 | `javascript` | 35 | 14 |

**Read:** technical artifacts (`library`, `editor`, language names, `open-source`) spread without sparking debate. Readers respect the work and upvote, but there is nothing to argue about.

## Strategic interpretation

If the goal is **viral spread + technical credibility**:
- Lead with the technical noun (`library`, `editor`, language)
- Use `open-source` if true
- Keep authorship voice optional

If the goal is **community discussion + long-tail engagement**:
- Use `I built` opening (first-person draws questions)
- Frame as `app` or `website` if accurate
- Reference the reader (`for you`, `your X`)

Both can be true at once. The strongest titles (`Show HN: I made an open-source laptop from scratch`, 3237 pts) hit BOTH signal sets — first-person builder voice + concrete technical noun + open-source. Look for stacking opportunities when the project allows it.

## Caveat

The 0.844 correlation means most of the success-correlated patterns from `failure-signals.md` apply to both metrics. The lift differences above are at the margin. Do not optimize a title for discussion at the expense of viral score; the title-scorer's signal score should remain the primary metric.

## Refresh

This file is currently hand-derived. Add to the `tools/` pipeline if the analysis becomes a regular update target. For now, re-run the inline analysis script (see git history of this file) after each corpus refresh.
