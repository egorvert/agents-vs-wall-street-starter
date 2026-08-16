# Historical-document search helper

This small Python script searches both the frozen historical Markdown corpus and the dated live external-evidence snapshot, then writes a cited research note. It does not calculate forecasts, select final values or edit the submission workbooks.

Python 3.10 or later is sufficient. There are no external dependencies.

## Run it

Search for the three challenge metrics for Home Depot:

```bash
python3 starter/search.py --company HD
```

Supply one or more narrower searches:

```bash
python3 starter/search.py \
  --company HD \
  --query "net sales" \
  --query "adjusted diluted EPS" \
  --query "comparable sales"
```

The default output is `research/HD.md`. Each result includes the source document, publication date, reporting period, excerpt and any numbers found in that excerpt. Live evidence comes from `challenge/live-data/` and is fixed at the cutoff recorded in its `snapshot.json`; the helper does not browse or refresh it.

Search only one evidence root, or supply several explicitly:

```bash
python3 starter/search.py --company HD \
  --document-root challenge/offline-data \
  --document-root challenge/live-data
```

The supported company selectors are:

- `HD` — Home Depot
- `ADI` — Analog Devices
- `HAS` — Hays plc
- `DE` — Deere & Company

The results are leads, not verified financial history or forecasts. Read the cited document before using a figure; check its source URL and cutoff; and keep reported, adjusted, quarterly and annual values separate.

## Use it with Codex or Claude Code

You can ask either harness:

> Run the historical-document search helper for Home Depot, open the resulting research note and help me check the evidence for each challenge metric.

The same script works with another configured company. It identifies the matching folders in both evidence roots from company metadata rather than hardcoding the four folder names.

## Test it

```bash
python3 -m unittest discover -s starter -p 'test_*.py'
```
