# oceancode-claude-skills

Claude Code skills authored from real datasets, not vibes. Each skill ships with the corpus it was derived from, a refresh script to keep it current, and lint test fixtures so rule changes do not silently regress.

## Skills

### `show-hn-writer`

Drafts Show HN posts grounded in 999 high-scoring submissions plus an 862-post failure corpus. Outputs 3 title variants from distinct formulas, drafts a 4-section body, runs a 30-rule lint pass with domain-conditional hype blocklists, and optionally drafts a first-comment block.

Key data:

- Success corpus: 999 Show HN posts above 676 points (top 25%)
- Failure corpus: 862 recent Show HN posts at or below 5 points
- 30 lint rules: 7 reject, 23 warn
- Test coverage: 24 fixture cases passing, 1 manual-only marker

See [skills/show-hn-writer/SKILL.md](skills/show-hn-writer/SKILL.md) for the full workflow and [skills/show-hn-writer/patterns/failure-signals.md](skills/show-hn-writer/patterns/failure-signals.md) for the comparative analysis that drives the lint rules.

## Layout

```
oceancode-claude-skills/
├── LICENSE
├── README.md
├── .claude-plugin/
│   └── plugin.json
└── skills/
    └── show-hn-writer/
        ├── SKILL.md
        ├── patterns/        corpus + derived analyses
        ├── lint/            rule set + checker workflow
        ├── examples/        good and bad post anatomy
        ├── tests/           fixture-based regression harness
        └── tools/           data refresh scripts
```

## Installation

### As a personal skill

Clone or symlink the `skills/<skill-name>/` directory into `~/.claude/skills/`:

```
git clone https://github.com/sunes26/oceancode-claude-skills.git
ln -s "$(pwd)/oceancode-claude-skills/skills/show-hn-writer" ~/.claude/skills/show-hn-writer
```

Claude Code auto-discovers skills under `~/.claude/skills/` and routes to them via the `description` field in `SKILL.md`.

### As a plugin (Claude marketplace)

The `.claude-plugin/plugin.json` manifest at the repo root makes this directory installable as a Claude Code plugin. See the Anthropic plugin docs for the current install command.

## Refreshing data

Each skill that depends on external data ships a `tools/refresh-*.py` script. For `show-hn-writer`:

```
cd skills/show-hn-writer
python tools/refresh-corpus.py
```

This re-pulls from the HN Algolia API, dedupes by github repo, and regenerates `patterns/corpus.json`, `patterns/top-100.json`, `patterns/failed-corpus.json`, and `patterns/posting-time.md`. Run quarterly or whenever the rule set is reviewed.

## Tests

```
cd skills/show-hn-writer
python tests/run-lint-tests.py
```

Exit 0 = all fixtures pass. Add a fixture whenever you add or change a rule. See `tests/README.md` in each skill for details.

## Contributing

Improvements that change rule behavior should be paired with a fixture update. Improvements that change derived analyses (failure-signals, posting-time, etc.) should re-run the refresh script and commit the regenerated data alongside the documentation change.

## License

MIT — see [LICENSE](LICENSE).
