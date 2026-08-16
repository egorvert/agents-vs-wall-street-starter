# 🟢 Combine / final call — David

Produces `out/<company_id>/final.json` (Contract F, `schemas/final.example.json`).
Blind estimate (consensus redacted) → reveal anchors → bounded reconciliation.
The LLM schema has NO field for the final value — it emits drivers/deltas/evidence;
this code computes the value, clamps into 🔵's range, applies a fixed blend toward
the anchor. Anchor priority: consensus → guidance midpoint → range base → seasonal
naive. Non-zero deltas need ≥2 cited evidence items. Prompts live here as `.md` files.
