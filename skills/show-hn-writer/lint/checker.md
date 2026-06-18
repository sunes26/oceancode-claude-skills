# Lint Checker Workflow

Run `anti-patterns.json` rules against generated titles and body. This file describes how a language model should execute the checks without a runtime.

## Execution model

For each rule in `anti-patterns.json`:

1. Read `rule.scope` — `title`, `body`, `submission`, or `both`
2. Apply `rule.check` against the relevant text
3. Collect hits as `{rule_id, severity, snippet, fix_suggestion}`

A rule with `severity: "reject"` and at least one hit means the variant MUST be regenerated. A rule with `severity: "warn"` means flag and ask the user to confirm.

## Per-rule check guidance

For rules with a `check` field, evaluate the boolean directly.

For rules with a `blocklist`:
- Lowercase the target text
- For each phrase in `blocklist`, check if it appears as a whole word/phrase (word-boundary match)
- Hit if any match

For rules with a `pattern` (regex):
- Apply the regex with the documented flags
- Hit if any match

## Reporting format

Per-variant lint output:

```
lint: <result>
```

Where `<result>` is one of:

- `✓ passes` — zero hits across all rules for this scope
- `⚠ <rule_id> (warn): <one-line reason> — fix: <suggestion>` — soft hit
- `✗ <rule_id> (reject): <one-line reason> — fix: <suggestion>` — hard hit

If multiple hits, list each on its own line.

## Fix suggestions per rule

| Rule | Fix suggestion |
|---|---|
| title-too-long | Cut filler words. Drop adjectives that do not change meaning. |
| title-too-many-words | Same as above. |
| missing-show-hn-prefix | Prepend `Show HN: ` exactly (note the space after colon, no space before). |
| emoji | Remove the emoji. Do not replace. |
| em-dash | Replace `—` with en-dash `–` only if used as title separator. In body, rewrite as two sentences or use a comma. |
| multiple-exclamation | Remove all but at most one in title; zero in body. |
| hype-words | Replace with the concrete fact behind the claim. `revolutionary` becomes `does X without Y`. |
| weak-ask | Replace with a specific question: what to add, what to break, what tradeoff is unclear. |
| url-missing | Add demo URL to the submission link field, or repo URL in body. |
| metrics-flex | Remove from title; can mention in first author comment instead. |
| all-caps-emphasis | Lowercase the word. Keep caps only for acronyms (API, CLI, HN, AI) and product names. |
| we-without-team | Replace `we` with `I` or remove the pronoun. |
| question-title | Convert to declarative. `Should X have Y?` becomes `If X had Y`. |
| no-context-link | Add the repo URL to the "How it works" section. |
| title-case-everything | Convert to sentence case after the prefix. |
| body-too-long | Cut from the "How it works" section first, then the bullet list. |
| body-too-short | Add a bullet to "What it does" or one sentence on the constraint that made it interesting. |
| competitor-callout | Remove competitor name. Describe the capability ("self-hosted LLM observability") instead of the comparison ("alternative to Langfuse"). |
| non-english-content | Re-translate the affected passage to English. Per SKILL.md, HN is English-only. |
| ai-saturation | Replace `AI`/`LLM`/`GPT` token with the user-facing capability. The AI mention moves to the body's "How it works" section. |
| buzzword-stack-2026 | Remove the trend word entirely. Describe the mechanism in plain language. Revisit the blocklist annually. |
| concept-without-product-name | Add the product name (Formula 2 shape) or convert to first-person Formula 1 (`I built X`). |
| upvote-begging | Delete the sentence. HN guidelines treat vote rallying as a flagging offense. |
| apology-self-promo | Delete the apology line. Show HN is for posting work. |
| lurker-coming-out | Delete the disclosure. Open with the project. |
| preemptive-praise | Remove self-congratulation. Move excitement (if any) to a first-comment line. |
| meta-narrative | Cut the meta-commentary about the post itself. Shorten the post instead of announcing length. |
| hype-words-ai | Replace AI jargon with the mechanism. `AI-powered X` becomes `X via prompt Y returning Z`. |
| hype-words-devtool | Quantify. `blazingly fast` becomes a number. `just works` becomes a concrete invariant. |
| hype-words-saas | Drop the marketing phrase entirely. State the verb the user runs. |

## Regeneration policy

If any title variant has a `reject` hit, regenerate that variant from a different formula. Do not edit-in-place — formulas are atomic patterns and editing breaks the formula match.

If the body has a `reject` hit, regenerate the affected section only (Hook, What it does, How it works, or Ask).

Max 2 regeneration cycles. If hits persist after 2 cycles, output what you have with explicit warnings and let the user decide.

## What lint does NOT do

- No grammar checking — out of scope, HN tolerates rough prose
- No spell check — same
- No factual verification — that is the user's job
- No tone scoring beyond the rule set — rules are explicit, no vibes
