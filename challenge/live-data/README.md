# Live external-evidence snapshot

This folder is a dated research archive of public information that was available by **16 August 2026 at 10:55 London time**. It complements the canonical frozen corpus in `challenge/offline-data/`; it does not modify or extend that corpus.

The archive prioritises:

1. company earnings releases and explicit management guidance;
2. company-hosted consensus and regulatory announcements;
3. official government and industry data that bear directly on the challenge metrics; and
4. material recent corporate developments.

Each evidence note has machine-readable frontmatter, a direct source URL, publication and retrieval dates, a concise factual summary, forecast relevance and cautions. The notes paraphrase sources and retain only small supporting excerpts or key figures. They are research inputs, not forecasts.

## Cutoff discipline

- `snapshot_cutoff_at` is `2026-08-16T10:55:00+01:00`.
- Do not silently refresh a source in place. Add a new dated note and update the indexes.
- Evidence published after the cutoff must not be used for the event forecasts represented by this snapshot.
- Home Depot, Analog Devices, Hays and Deere all had target-period results scheduled shortly after the cutoff. Their event-calendar notes are explicit leakage guards.
- A source being recent does not make it comparable to a challenge metric. Respect fiscal periods, reported versus adjusted definitions, currencies and units.

## Layout

```text
live-data/
├── INDEX.md
├── snapshot.json
├── home-depot/
├── analog-devices/
├── hays/
└── deere/
```

Within each company, `company-releases/` contains first-party guidance, `market-data/` contains official or industry indicators, `news/` contains other material developments, and `events/` contains known reporting dates and cutoff warnings.

The starter search helper searches both `challenge/offline-data/` and this folder by default.

