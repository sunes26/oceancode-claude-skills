# Author first comment

After the post lands on HN, a substantial fraction of top performers reply to their own thread within the first 5-10 minutes. This comment shapes the early discussion and the author's apparent engagement signal.

It is optional. Some top posts have no author first comment at all because the story body already covered everything. The decision depends on what got cut from the body for length.

## When to write a first comment

Write one if any of these apply:

1. Body hit the 250-word cap and you cut technical detail readers will ask about
2. There is a specific tradeoff, cost number, or scale figure too off-topic for the body but the smart commenters will probe for
3. You want to seed an "ask me about X" thread to focus the conversation
4. The project requires a setup step or has a known limitation that pre-empting will avoid 20 duplicate complaints

Skip the comment if:

- Body is already <180 words with room to spare — extend the body instead
- The only thing left to say is thanks or excitement — silence reads better than gratitude

## Observed patterns from top Show HN threads

Surveyed authors of stories at >2500 points:

**Pattern A — Prompt or source artifact**
> "Prompt: <verbatim prompt>"
> (Gemini Pro 3 imagines HN front page, 3346 pts)

The author pasted the exact LLM prompt used. Lets readers reproduce immediately without asking.

**Pattern B — Concrete data extension**
> "Channel 1: Science and Technology / Channel 2: Travel and Events / Channel 3: Food / ..."
> (If YouTube had actual channels, 2741 pts)

The author listed all 12 channels from the demo. Body had the concept; comment had the substance.

**Pattern C — Builder introduction**
> "Hello! I'm Byran. I spent the past ~6 months engineering a laptop from scratch. It's fully open-source on GH at: ..."
> (I made an open-source laptop from scratch, 3237 pts)

Sometimes this lives in the story body itself rather than a comment. The intro + "I spent N months on this" pattern works in either slot.

**Pattern D — Silence**

Some top posts have no author first comment at all. The body answered everything the early commenters had to say. Do not force one.

## Template (Pattern C is most reusable)

```
Hi, I'm <name>. <one-line context: company, day-job, or solo>

I built this because <itch>. The non-obvious part was <one concrete tradeoff or constraint>.

A few things I cut from the body in case anyone is curious:
- <tradeoff 1>
- <cost or scale number>
- <known limitation>

Happy to dive into <topic 1>, <topic 2>, or anything else. AMA.
```

Length: 80-150 words. Shorter than the body.

## Rules

- No "thanks for reading"
- No "would mean the world to me"
- No vote begging in any form
- No emoji
- If you mention costs (server, model, infra), state the actual number
- If you mention a limitation, do not hedge it — name it plainly

## Timing

Post the comment within 5 minutes of the story. Threads that go cold for the first 10 minutes are harder to recover. Keep the comment composed before you submit the story — paste it in immediately.

## Output from this skill

When the skill produces a Show HN draft, it MAY also output a first-comment block if:

- The body lint hit `body-too-long` and content was trimmed
- The user supplied a "constraint" or "cost" input that did not fit in the body
- The user explicitly asks "include a first comment"

Otherwise the first-comment block is omitted and the pre-publish checklist reminds the user to consider whether to write one manually.
