---
name: show-hn-writer
description: Draft Show HN posts using 999 real high-scoring submissions as the pattern corpus. Produces 3 title variants from distinct proven formulas, drafts a 4-section body, and runs an anti-pattern lint pass before output. Use when the user wants to launch a project on Hacker News, asks to write a Show HN post, or requests title variants for an HN submission.
---

# show-hn-writer

Drafts Show HN posts grounded in a corpus of 999 real submissions (250th-percentile cutoff: 676 points). No invention from priors. Every recommendation traces back to a measured frequency in `patterns/corpus.json`.

## When to invoke

Trigger phrases: "write a Show HN", "Show HN draft", "launch on HN", "HN title variants", "post my project on Hacker News".

Skip if the user wants generic launch copy, Reddit, dev.to, or non-HN channels. Crosspost reshaping after a Show HN exists is fine but pass the existing draft as input.

## Inputs required

Ask once at the start, batched:

1. `product_name` — exact casing as it should appear
2. `one_liner` — what it does, in plain language (no marketing)
3. `url` — live demo or landing (HN penalizes posts without it)
4. `repo_url` — optional, GitHub link if OSS
5. `tech_stack` — optional, only if novel
6. `why_built` — 1-2 sentences, the itch that started it
7. `target_audience` — who would use it
8. `constraints` — optional, things like "built in a weekend", "self-hosted", "MIT licensed"

If the user already supplied some of these in the conversation, do not re-ask. Confirm and proceed.

## Domain detection (for conditional lint rules)

Before drafting, infer the product domain from inputs. This decides which hype blocklists apply.

Domain inference rules (apply in order, first match wins):

1. **AI/LLM** — if `tech_stack` mentions `OpenAI`, `Anthropic`, `Gemini`, `LLM`, `embedding`, `vector DB`, OR `one_liner` mentions `agent`, `prompt`, `chatbot`, `RAG`. Apply `hype-words-ai`.
2. **Dev tool** — if `target_audience` mentions `developer`, `engineer`, `SRE`, OR `tech_stack` indicates a CLI / SDK / build tool / linter. Apply `hype-words-devtool`.
3. **SaaS / business product** — if `target_audience` mentions `team`, `business`, `enterprise`, `B2B`, OR the project has a paid tier. Apply `hype-words-saas`.

Multiple domains can apply at once (e.g., AI + dev tool for an LLM developer SDK). Run every applicable blocklist.

The generic `hype-words` rule always applies regardless of domain.

## Output language

Always English regardless of input language. Hacker News is an English-speaking audience and non-English Show HN posts get flagged or downvoted within minutes. If the user supplied inputs in another language (Korean, Japanese, etc.), translate during drafting without asking. Preserve product name casing exactly as the user wrote it.

Exception: code blocks, command examples, URL paths stay verbatim.

## Workflow

### Step 1 — Retrieve patterns

Read these files in order:

1. `patterns/title-formulas.md` — 12 proven title formulas with frequency data
2. `patterns/body-structure.md` — 4-section body skeleton
3. `lint/anti-patterns.json` — reject rules with justification
4. `patterns/top-100.json` — high-scoring reference titles (only if user asks "show me examples")
5. `patterns/first-comment.md` — load only if first-comment generation is triggered (see Step 4)
6. `patterns/failure-signals.md` — load when the user input contains potential failure signals (e.g., "AI", "agentic", "RAG", concept-only title) so the lint output can cite the comparative data

Do not load `corpus.json` or `failed-corpus.json` (raw arrays, big) unless the user specifically requests deeper analysis.

### Step 2 — Generate 3 title variants

Pick 3 *different* formulas from `patterns/title-formulas.md`. Diversity matters: do not return 3 variants of formula 1. Prefer combinations that cover different angles (e.g., one curiosity-driven, one OSS-signal, one personal/builder voice).

Constraints per variant:
- Body length ≤ 50 chars (median) or ≤ 60 chars (hard cap)
- Body word count ≤ 10 words (target 8)
- Title must include the product name OR a concrete differentiator
- Always prefix with `Show HN:` exactly (no lowercase, no missing colon)

### Step 3 — Draft body

Follow `patterns/body-structure.md` exactly:

1. **Hook** (1-2 sentences) — why built, the itch
2. **What it does** (3-5 bullets) — outcomes not features
3. **How it works** (2-3 sentences) — stack, novel approach
4. **Ask** (1 sentence) — invite feedback specifically

Total: 120-250 words. Longer reads as marketing.

### Step 4 — Draft first comment (conditional)

Generate an author first-comment block ONLY if any of these triggers fire:

- Body lint flagged `body-too-long` and material was trimmed
- User supplied `constraints` or cost/scale inputs that did not fit the body
- User explicitly requested a first comment

If a trigger fires, load `patterns/first-comment.md`, follow the template, and append the output. Otherwise skip this step and let the pre-publish checklist remind the user that the first comment is optional.

### Step 5 — Lint title and body

Run every rule in `lint/anti-patterns.json` against BOTH each title variant AND the body. Report per-variant:

- `✓ passes` — no hits
- `⚠ warning: <rule_id>` — soft anti-pattern, explain
- `✗ reject: <rule_id>` — hard violation, must fix before posting

If a hard violation exists in all 3 titles, regenerate.

### Step 6 — Output format

Return as a single markdown block:

```
## Title variants (ranked)

### Variant A — Formula <N>: <formula name>
> Show HN: <title>
- chars: <N> / words: <N>
- lint: ✓ passes

### Variant B — Formula <N>: <formula name>
> Show HN: <title>
- chars: <N> / words: <N>
- lint: ⚠ <rule_id>: <reason>

### Variant C — Formula <N>: <formula name>
> Show HN: <title>
- chars: <N> / words: <N>
- lint: ✓ passes

## Body

<4-section draft>

## Pre-publish checklist
- [ ] URL resolves and shows demo or landing (HN penalizes 404)
- [ ] You can reply to comments for the first 2 hours after posting
- [ ] First comment ready: tech details / cost / "happy to answer X"
- [ ] Posted Tue/Wed/Thu, 8:00-12:00 ET (corpus-derived window — 9 of top 10 (dow, hour) buckets fall here; KST = 22:00 prior day to 02:00 next day). See `patterns/posting-time.md` for caveats.
- [ ] No emoji, no rocket, no "revolutionary"
```

## What this skill does NOT do

- No posting to HN. Output is text only. User submits manually.
- No A/B prediction. Variants ranked by formula match strength, not predicted points.
- No comment reply drafting. Separate concern.
- No SEO optimization. HN is not Google.

## Data provenance

`patterns/corpus.json` fetched 2026-06-18 from HN Algolia API:
```
https://hn.algolia.com/api/v1/search?tags=show_hn&hitsPerPage=1000
```
1000 hits, sorted by points desc. 999 actual Show HN titles after filtering. 250th-percentile = 676 points. Refresh quarterly via `tools/refresh-corpus.py` (not yet built).

## Anti-bloat rules for the skill itself

- Never expand the body draft beyond 250 words without explicit user ask
- Never invent stats not in `patterns/*.md`
- Never recommend gimmicks ("post in incognito", "rally friends", etc.)
- Never add an emoji or em-dash (`—`) to output. En-dash (`–`) only as title separator if formula 2 chosen.
