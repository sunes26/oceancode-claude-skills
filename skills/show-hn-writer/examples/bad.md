# Anti-examples

Synthetic but representative. Each shows what to avoid, what rule catches it, and the rewrite.

---

## 1. Hype overload

**Bad:**
> Show HN: 🚀 Revolutionary AI-powered platform to supercharge your workflow!!!

**Rules tripped:**
- `emoji` (reject)
- `hype-words`: revolutionary, supercharge (reject)
- `multiple-exclamation` (reject)
- `title-too-many-words`: 11 (warn)

**Rewrite:**
> Show HN: A workflow tool that runs LLM steps in a YAML pipeline

---

## 2. Em-dash + AI tells

**Bad:**
> Show HN: Foo — the seamless, robust solution for modern teams

**Rules tripped:**
- `em-dash` (reject)
- `hype-words`: seamless, robust (reject)

**Rewrite:**
> Show HN: Foo – a CI cache that survives runner restarts

---

## 3. Metrics flex

**Bad:**
> Show HN: How I grew Bar to $50k MRR in 6 months

**Rules tripped:**
- `metrics-flex` (warn)
- Misuse of Show HN — this belongs in a separate "Show HN: Bar" post about the product itself

**Rewrite:**
> Show HN: Bar – a self-hosted error tracker (open source)

Save the MRR story for the first comment if relevant.

---

## 4. Generic ask in body

**Bad body ending:**
> Hope you like it! Let me know what you think.

**Rules tripped:**
- `weak-ask` (warn)

**Rewrite:**
> Curious if the latency budget makes sense for streaming workloads — that is the tradeoff I am least confident in.

---

## 5. Solo founder using "we"

**Bad:**
> We built this over the weekend to solve our team's problem.

**Context:** user.team_size == 1.

**Rules tripped:**
- `we-without-team` (warn)

**Rewrite:**
> I built this over a weekend to solve a problem I kept hitting.

---

## 6. Title with everything Capitalized

**Bad:**
> Show HN: A New Way To Build Better Software Faster

**Rules tripped:**
- `title-case-everything` (warn)
- `hype-words`: faster (warn, borderline)
- Lacks concreteness — no noun for the thing being shown

**Rewrite:**
> Show HN: Baz – a build tool that caches compiler artifacts in S3

---

## 7. Question title

**Bad:**
> Show HN: What if Postgres had Redis-style pub/sub?

**Rules tripped:**
- `question-title` (warn)

**Rewrite (Formula 4 conversion):**
> Show HN: If Postgres had Redis-style pub/sub

(Statement of fact about the demo, not a question.)

---

## 8. URL missing

**Bad:** Submission with no URL, body says "DM me for access".

**Rules tripped:**
- `url-missing` (warn)
- Implicit: closed beta on HN reads as exploitation of the channel

**Fix:** Wait until there is a public landing page or repo. Show HN is not a waitlist channel.

---

# Pattern: what makes a Show HN post bad

1. Tries to sell rather than show
2. Cannot survive removing every adjective
3. Treats HN as a marketing channel rather than an engineering audience
4. Buries the artifact under language
5. Demands trust before offering proof (no URL, no repo, no demo video)

If your draft trips 3+ of these, do not post. Build more first.
