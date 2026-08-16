# Appendix — Street vs GAAP "actuals" and consensus data quality

Deep-dive by a research sub-agent on I/B/E/S/vendor "actual" EPS mechanics. Matters for two
decisions: (1) which EPS basis our forecast targets, (2) how we score backtests.

## Practical takeaways

1. **~8% of firm-quarters flip beat↔miss depending on whether the "actual" is the vendor's
   street EPS or GAAP EPS** (Abarbanell & Lehavy 2007, fn.19; ~10.3% conditional on non-zero
   surprise). Asymmetric: ~6% street-favorable vs ~2% GAAP-favorable. A basis error swamps any
   model improvement — verify the consensus basis per company before forecasting.
2. **~50% of firm-quarters have street == GAAP exactly** (split-adjusted data); 65–79% on
   unadjusted data. The gap between those numbers is split-adjustment + penny rounding, not economics.
3. **The vendor "actual" is a majority-rule construct, not a fact**: it differs from the
   analyst-inferred actual by ≥1¢ **39%** of the time (Brown & Larocque 2013), and zero-difference
   rates vary by vendor over the same window: First Call 47% / I/B/E/S 52% / Zacks 60%.
   Zacks maintains two consensuses (BNRI vs Street) that differ ≥2¢ for 5–10% of names.
4. **Named disaster case**: Citigroup Q4-2017 — FactSet first recorded actual EPS **−$7.15** vs
   $0.56 consensus (TCJA charge), then *changed the actual to $1.28* after reviewing analyst
   notes. Same quarter, same press release; the "actual" depends on the vendor's exclusion call.
   (FactSet Insight, Jan 2018.)
5. **Dispersion in cents is flat across the size distribution** — median SD of analyst EPS
   forecasts is **$0.02 in every price decile** (Cheong & Thomas 2011). Consensus absolute EPS
   error: median 2–3¢, mean 5–6¢. Percentage EPS metrics are dominated by the denominator →
   score EPS in **cents**, never MAPE.
6. **Using GAAP actuals vs street actuals to compute surprise roughly doubles the IQR and
   triples the SD of the surprise distribution** (COMPFE vs FCSTERR, Cheong & Thomas).
7. **Revenue consensus error is ~8.6× smaller than EPS error** (Houlihan Lokey 2024: Russell 3000
   1-yr weighted % error: revenue 9.76% vs earnings 84.05%). Revenue coverage for mega-caps is now
   as thick as EPS coverage (e.g. MSFT: 37 revenue vs 27 EPS quarterly estimates).
8. **Coverage is bimodal**: 86–89% of large caps have 11+ analysts; 57% of Russell 2000 have ≤5;
   ~6% of R2000 have zero. Low-coverage names have noisier consensus but also noisier scoring.

## Key sources

- Bradshaw & Sloan (2002) JAR — street−GAAP gap grew through the 1990s; I/B/E/S "stepped up"
  exclusions ~1992. https://doi.org/10.1111/1475-679x.00038
- Doyle, Lundholm & Soliman (2003) RAST — 65% of firm-quarters have zero exclusions; $1 of
  "other exclusions" → ≈$3 less future cash flow. https://papers.ssrn.com/sol3/papers.cfm?abstract_id=303563
- Abarbanell & Lehavy (2007) CAR "Tail Wag the Dog" — flip rates, vendor zero-diff table.
  https://webuser.bus.umich.edu/rlehavy/tail.pdf
- Brown & Larocque (2013) TAR — I/B/E/S actual vs analyst-inferred actual. https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1732573
- Bochkay et al. (2022) JAR — Sept-2009 Thomson methodology change; FITB $0.65 vs $0.43 same
  quarter. https://doi.org/10.1111/1475-679x.12457
- Larocque, Watkins & Weisbrod (2026, JAR) — 5 vendors disagree on actuals for the same
  firm-quarter; I/B/E/S highest quality. https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4640370
- Cheong & Thomas (2011) JAR — dispersion/error flat in cents across scale. https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1675603
- Houlihan Lokey "Do We Have a Consensus?" (2024) — revenue vs EPS error magnitudes.
  http://cdn.hl.com/pdf/2024/accuracy-of-analyst-estimates-2024.pdf

## Implications for our build

- **Target the basis the scorer uses.** Confirm with organizers which vendor/basis "actual" and
  "consensus" the hackathon scores against; per company, detect GAAP vs non-GAAP basis from the
  last quarter's consensus-vs-reported gap before forecasting.
- **Score EPS in absolute cents** on the eval harness; revenue in % error.
- **Prefer high-coverage names** (consensus and actual are well-defined and stable) — aligns with
  the company-selection doc's top-5.
- **Expect ±2–3¢ irreducible noise** in the EPS target itself; don't chase precision below that.
