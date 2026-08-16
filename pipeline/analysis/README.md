# 🟢 Analysis products — David

Produces `out/<company_id>/analysis/{context,facts,news}.md` + `out/<company_id>/consensus.json`
(Contracts B/C — templates in `schemas/`). Consumes the 🔴 dossier + live-data.
Every numeric fact goes in the ```jsonl fact block; 🔵's extractor parses only that.
Prompts live here as versioned `.md` files.
