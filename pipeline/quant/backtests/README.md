# Point-in-time backtests

These event bundles are evaluation-only inputs owned by `pipeline/quant/`; they are not
new shared pipeline contracts and they contain no live submission forecasts. Each event
directory contains:

- `event.json`: the cutoff and post-cutoff cited actuals;
- `timeseries.json`: only observations available before the cutoff;
- `consensus.json`: only anchors published before the cutoff.

`backtest.py` verifies every quote against the local corpus and refuses target-period or
post-cutoff forecast inputs before calculating a forecast.

## HD smoke set

The first smoke set holds out FY2023Q2, FY2024Q2 and FY2025Q2. It scores net sales and
total-company comparable sales: six observations in total. Adjusted EPS is deliberately
absent because the older corpus reports GAAP diluted EPS, while the live target requires
adjusted EPS. Relabelling GAAP history as adjusted would make the sample larger but the
evaluation false.

Historical Q2 analyst consensus is not present in the corpus. Therefore B1 uses the
last pre-cutoff full-year comparable-sales guidance as a documented proxy and falls back
to B0 for net sales. Proxy coverage is explicit in the result: three
`guidance_midpoint` observations and three `b0_fallback` observations.

Run the smoke backtest without committing its generated result:

```powershell
python pipeline/quant/backtest.py `
  --case pipeline/quant/backtests/HD/FY2023Q2 `
  --case pipeline/quant/backtests/HD/FY2024Q2 `
  --case pipeline/quant/backtests/HD/FY2025Q2 `
  --output "$env:TEMP/hd-smoke-results.json"
```

Result at implementation time:

| Config | Mean official score | Median | Win rate vs B1 | Capped |
| --- | ---: | ---: | ---: | ---: |
| B0 seasonal | 2.638 | 1.913 | 0.0% | 33.3% |
| B1 anchor/proxy | 0.833 | 1.000 | 0.0% | 0.0% |
| Current ranges base | 1.079 | 1.046 | 33.3% | 0.0% |
| B1 weight 25% | 2.362 | 1.435 | 0.0% | 16.7% |
| B1 weight 50% | 1.908 | 1.000 | 16.7% | 16.7% |
| B1 weight 75% | 1.102 | 1.000 | 33.3% | 0.0% |

The current base scores `0.961` on comparable sales and `1.197` on net sales when split
by metric. Its ranges cover five of six actuals, but their mean width is about 64 official
floors, so coverage is not yet sharp enough to celebrate. B1 wins the tiny aggregate;
the current model and 75%-B1 blend win selected cases but do not beat it overall.

This is a leak-free plumbing and direction check, not evidence of statistical
significance. Six heterogeneous observations cannot justify regression. Expand companies,
metrics and historical point-in-time anchors before fitting any coefficients.
