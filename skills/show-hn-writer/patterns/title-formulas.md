# Title Formulas

Derived from 999 Show HN titles (cutoff: 676 points = top 25%). Each formula lists frequency in corpus, sample matches, and when to pick it.

All formulas assume `Show HN: ` prefix already prepended. Bodies stay ≤ 60 chars hard, ≤ 50 chars target.

---

## Formula 1 — "I built/made X" (first-person builder) ★ TOP-TIER WINNING SIGNAL

**Frequency:** 17.1% of success corpus (n=1,945) vs 7.4% of failed corpus (n=5,000). Lift = 2.29. The `I made/built` substring specifically: 10.6% vs 4.9%, lift = 2.18. Strong, consistent winning pattern across the full historical corpus. The single strongest title token is actually `self-hosted` (lift 3.79), but `I built X` covers far more cases.

**Shape:** `I <verb> <product> [to <reason>] [from scratch]`

**Examples from corpus:**
- `I made an open-source laptop from scratch` (3237 pts)
- `I built a workflow app for my Saudi mom` (high)
- `I built a tool to <verb> X` (recurring)

**Use when:** Solo project, weekend hack, personal itch. Signals authenticity. Risky for VC-backed teams (reads as posturing).

**Variations:** `I've been building X for N months`, `I'm building X`

---

## Formula 2 — "Product – one-line value" (en-dash separator)

**Frequency:** 35.0% of success corpus vs 31.3% of failed corpus (n=1,945 vs 5,000). Lift = 1.12. The standard HN title format. Roughly neutral with a slight winner lean — neither magic nor handicap. Use when product name is memorable and value prop fits in 5-6 words after the dash.

(Earlier versions of this file claimed this formula was failure-coded based on a small-sample analysis. The expanded corpus shows the prior finding was a selection artifact.)

**Shape:** `<ProductName> – <concrete value or differentiator>`

**Examples from corpus:**
- `Pico – a tiny static site generator in Rust`
- `Foo – open-source alternative to Bar`

**Use when:** Product name is memorable and short. Value prop fits in 5-6 words after dash. Standard for tooling, SDKs, libraries.

**CRITICAL:** Use en-dash `–` (U+2013), NOT em-dash `—` (U+2014). Em-dash reads as AI-generated.

---

## Formula 3 — "A/An [adjective] X for [audience]"

**Frequency:** 6.0% start with `A`/`An` (60/999).

**Shape:** `A <adjective> <thing> for <specific audience>`

**Examples:**
- `A retro video game console I've been working on in my free time` (2690 pts)
- `A self-hosted X for Y`

**Use when:** Audience is well-defined niche. Adjective is concrete (retro, tiny, self-hosted, open-source) not promotional (amazing, powerful).

---

## Formula 4 — "If X had Y" (counterfactual hook)

**Frequency:** Rare but disproportionately viral.

**Shape:** `If <known thing> had <novel attribute>`

**Examples:**
- `If YouTube had actual channels` (2741 pts)
- `If <X> were built today`

**Use when:** Project reimagines existing well-known service. Title alone makes reader curious. Very high ceiling, hard to write well.

---

## Formula 5 — "Open-source X" (OSS signal)

**Frequency:** 7.8% mention open-source (78/999). 11 start with `Open-source`.

**Shape:** `Open-source <category> [for/of/with <differentiator>]`

**Examples:**
- `Open-source alternative to <SaaS>`
- `Open-source X engine`

**Use when:** OSS is the primary differentiator vs incumbent. HN crowd strongly rewards this signal. Pair with MIT/Apache license mention in body.

---

## Formula 6 — Constraint flex (time/cost/size)

**Frequency:** ~3% mention constraints explicitly.

**Shape:** `<Product>, built in <constraint>` or `<Product> in <N> lines/MB/$`

**Examples:**
- `X in 100 lines of Rust`
- `Y running on a $5 VPS`

**Use when:** Engineering feat is the story. Constraint must be real and verifiable. Do not invent.

---

## Formula 7 — "My weekend/side project: X"

**Frequency:** 5.5% use `My` (55/999).

**Shape:** `My <timeframe> project: <product>`

**Use when:** Hobby project, no commercial intent. Signals low-stakes feedback request. Avoid if product is venture-backed.

---

## Formula 8 — "X but Y" (differentiator)

**Frequency:** ~4% use `but` as differentiator pivot.

**Shape:** `<Familiar X> but <key difference>`

**Examples:**
- `Notion but for terminals`
- `cURL but for gRPC`

**Use when:** Comparison to known tool is clearest description. Risk: positions you as derivative.

---

## Formula 9 — "[Existing thing] for [new domain]"

**Shape:** `<Known tool/pattern> for <unexpected domain>`

**Examples:**
- `Git for designers`
- `Kubernetes for <weird thing>`

**Use when:** Cross-domain application. Works for tools porting patterns from one field to another.

---

## Formula 10 — "Turning X into Y"

**Shape:** `Turning <input> into <output>`

**Use when:** Product is a transformation pipeline. Concrete input/output. Verb-led titles read active.

---

## Formula 11 — "Self-hosted X"

**Frequency:** 1.2% (12/999). Rare but high-quality engagement.

**Shape:** `Self-hosted <category>` or `<Product> – self-hosted alternative to <SaaS>`

**Use when:** Self-host is the headline feature. HN sysadmin crowd over-indexes here.

---

## Formula 12 — "Product – [stack/cost/scale]"

**Shape:** `<Product> – <technical badge>` (e.g., "written in Zig", "$0 to run", "no JS")

**Use when:** Tech choice is the differentiator. Common for systems-level projects.

### Sub-variant 12a — Parenthetical badge

**Shape:** `<Formula 1 or 7 title> (<short badge>)`

**Examples:**
- `I built a self-hosted LLM cost tracker (MIT)`
- `My weekend project: a vector DB (10MB binary)`

**Use when:** Main formula already maxes the character budget but one critical signal (license, size, cost) needs to ride along. Badge MUST be ≤ 6 chars or a well-known acronym (MIT, GPL, Apache, BSD). Anything longer breaks the rhythm.

**Discovered:** 2026-06-18 Spanlens dry-run — Formula 1 hit `title-too-long` at 66 chars, badge sub-variant fit 44 chars while preserving the OSS signal.

---

# Selection heuristic

When generating 3 variants, ensure formula diversity by category:

| Category | Formulas |
|---|---|
| Voice-driven | 1, 7 |
| Structural | 2, 12 |
| Audience | 3, 9 |
| Hook | 4, 8 |
| Signal | 5, 11 |
| Feat | 6, 10 |

Pick from 3 different categories. Never return 3 from the same row.

# Avoided patterns (data-backed)

- Question titles: only 1.6% of corpus. Underperform.
- Emoji: 0.0% of corpus. Hard reject.
- All-caps words >2 letters: 19.1% have them — but ONLY for product name (`HN`, `API`, `CLI`). Never as emphasis.
- "We" first-person: 1.6% only. Reads corporate. Prefer "I" or no pronoun.
