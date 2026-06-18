# Body Structure

Show HN posts that ship to the front page have a recognizable shape. Four sections, 120-250 words total. No headers in the actual post — HN renders plain text. Sections shown here for drafting only.

---

## Section 1 — Hook (1-2 sentences, ≤ 40 words)

**Purpose:** Why this exists. The itch.

**Pattern:**
- Sentence 1: What problem you hit.
- Sentence 2 (optional): Why existing tools did not work.

**Good:**
> I kept losing track of which LLM API calls cost money in my agents. Existing dashboards were either built for SREs or required a credit card before I could see anything, so I built one I could `npm install` in two minutes.

**Bad (marketing voice):**
> Spanlens is the next-generation LLM observability platform that empowers developers to gain unprecedented insights into their AI workloads.

**Lint:** No "next-generation", "empowers", "unprecedented", "leverage", "robust", "seamless", "delightful", "best-in-class".

---

## Section 2 — What it does (3-5 bullets, ≤ 60 words)

**Purpose:** Concrete capability list. Outcomes, not features.

**Pattern:**
- Each bullet starts with a verb
- Each bullet describes what the user gets, not what the system has
- Mention numbers when honest (latency, size, throughput)

**Good:**
- Drop-in replacement for `OpenAI()` — one line change
- Logs every request to ClickHouse with cost calculated per model
- Shows token usage, P95 latency, and per-user spend
- MIT licensed, self-hosted in a Docker container

**Bad:**
- Cutting-edge observability stack
- Built with love using modern technologies
- Industry-leading performance

---

## Section 3 — How it works (2-3 sentences, ≤ 60 words)

**Purpose:** Technical credibility. Show the seams.

**Pattern:**
- Name the architecture in one sentence
- Mention the surprising tradeoff if any
- Link to the repo or architecture doc

**Good:**
> It is a Hono proxy in front of OpenAI/Anthropic/Gemini. Streaming responses tee through to ClickHouse asynchronously so the proxy adds <5ms. Costs are calculated from a model price table that auto-refreshes.

**Lint:** No diagrams in text. No buzzword stacks. Avoid "powered by" — just name the tools.

---

## Section 4 — Ask (1 sentence, ≤ 25 words)

**Purpose:** Invite specific feedback. The community responds better to a real question than to "let me know what you think".

**Good:**
- Curious which provider you would want supported next — Bedrock or Vertex are in the queue.
- Happy to dive into the ClickHouse schema if anyone is doing similar self-hosted observability.
- Would love feedback on the cost calculation accuracy — that is the part I am least sure about.

**Bad:**
- Let me know what you think!
- Hope you like it.
- Feedback welcome.

---

## Composition rules

- Total word count: 120-250 (median Show HN body in corpus: ~180 words)
- Plain text only — HN strips markdown except inline code via backticks
- One URL in the body if not in the title (the live demo or repo)
- No emoji anywhere
- No em-dash (`—`). Two hyphens or a comma instead.
- No "we" if you are solo. If team, use "we" sparingly (max 2x)

## First comment (separate, prepare before posting)

Top Show HN posts have an author first comment within 5 minutes. Pre-draft it:

- One paragraph that adds context not in the body
- Hosting cost or rough scale numbers
- "Happy to answer questions about X, Y, Z"

Not part of skill output but mentioned in pre-publish checklist.
