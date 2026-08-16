# 🔴 Foundational research swarm — Egor & co

Produces `out/<company_id>/research/dossier.md` (Contract A, `schemas/dossier.template.md`).
Orchestrator-workers over `challenge/offline-data/` + `challenge/live-data/`; workers
return cited facts, merged into one dossier per company. Web evidence must first be
saved as a dated `challenge/live-data/` note. Prompts live here as versioned `.md` files.
