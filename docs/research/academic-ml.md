# Earnings forecasting: academic + quant literature

Survey compiled 15 Aug 2026 for the "Agents vs Wall Street" hackathon (16 Aug 2026).
Task being solved: forecast one company's **next quarterly revenue and EPS**, scored against actuals **and** against sell-side consensus ~6 weeks later.

**Read this first — the single most important framing fact.** Almost all the "naive models beat analysts" literature is about *annual* earnings at *long* horizons (12–36 months). We are forecasting the quarter that is about to be reported, i.e. the **shortest possible horizon**, which is exactly the regime where analysts are strongest and where mechanical models lose. Bradshaw et al. say so explicitly: at the 0-month horizon analysts beat a random walk by **245 basis points of price**, and their advantage decays to ~25bp by 11 months and goes *negative* past ~21 months ([Bradshaw, Drake, Myers & Myers 2012, working paper](https://care-mendoza.nd.edu/assets/152185/bradshawpaper.pdf)). Plan around this: our realistic edge is **de-biasing and blending with consensus**, not replacing it.

Legend: **[1-DAY]** implementable tomorrow · **[STRETCH]** possible if things go well · **[NO]** needs data/compute we won't have.

---

## 1. Classic time-series models of quarterly earnings

### 1.1 The canonical ladder (Foster 1977)

Foster, "Quarterly Accounting Data: Time-Series Properties and Predictive-Ability Results," *The Accounting Review* 52(1), 1977 ([full text PDF](https://faculty.utrgv.edu/diego.escobari/teaching/Econ8375/Papers/2018-Auto2-Norman.pdf)) defines the six models everyone still benchmarks against. Let `Q_t` = earnings in quarter t.

| # | Model | Spec |
|---|---|---|
| 1 | Seasonal random walk (SRW) | `E[Q_t] = Q_{t-4}` |
| 2 | SRW + drift | `E[Q_t] = Q_{t-4} + δ` |
| 3 | Random walk | `E[Q_t] = Q_{t-1}` |
| 4 | RW + drift | `E[Q_t] = Q_{t-1} + δ` |
| 5 | **Foster** | `E[Q_t] = Q_{t-4} + φ·(Q_{t-1} − Q_{t-5}) + δ` |
| 6 | Firm-specific Box-Jenkins | identified per firm |

Model 5 is an ARIMA `(1,0,0)×(0,1,0)₄` — an AR(1) on the *seasonally differenced* series. `δ` is the drift (mean of seasonal differences × (1−φ)); `φ` is estimated as the lag-1 autocorrelation of `W_t = Q_t − Q_{t-4}`.

**Why Model 5 exists:** Beaver (1974) showed that Model 2's forecast errors have first-order serial correlation of **+0.416** — the SRW is leaving money on the table. Model 5 mops that up. **[1-DAY]** — this is 15 lines of TypeScript and needs only ~8 quarters of history.

Two other "premier" models:
- **Brown & Rozeff (1979)**, *JAR* 17(1):179–189 — ARIMA `(1,0,0)×(0,1,1)₄`:
  `Q_t = Q_{t-4} + φ(Q_{t-1} − Q_{t-5}) + δ − θ·ε_{t-4} + ε_t`, with φ>0, θ<0.
- **Griffin (1977) / Watts (1975)** — ARIMA `(0,1,1)×(0,1,1)₄`.

Foster's argument for *premier* (one-size-fits-all) models over per-firm Box-Jenkins is **"search bias"**: identifying a model per firm overfits random variation. Collins & Hopwood (1980) and Lorek (1979) confirmed BJ does not beat premier models. But Hopwood & McKeown (1980) ([BEBR 725](http://hdl.handle.net/2142/27053)) found premier-model accuracy **degrades sharply past ~4 quarters ahead** vs BJ, because premier models can pick the wrong differencing/constant. Irrelevant for us — we forecast 1 quarter ahead.

### 1.2 Annual earnings ≈ random walk

Ball & Watts (1972), Albrecht et al. (1977), Watts & Leftwich (1977): annual earnings approximate a random walk, and complexity buys nothing. Brown (1993) called this "pretty much resolved by the late 1970s." Bradshaw et al.'s spec is literally:

```
E_{T-τ}[EPS_T] = EPS_{T-τ},  τ > 0
```

Notable: a random walk beats **random walk with drift** when earnings are deflated by stockholders' equity, but loses when undeflated (Albrecht et al. 1977) — scaling choice matters more than model choice.

### 1.3 Persistence and mean reversion

- Losses are **less persistent** than profits (Hayn 1995). Every good cross-sectional model since carries a `NegE` dummy and a `NegE × E` interaction.
- EPS grows ~**50 basis points of price per year** on average, which is why median random-walk forecast errors are *negatively* biased while median analyst errors are *positively* biased (optimistic) — Bradshaw et al. §4.1.

---

## 2. Cross-sectional / characteristic-based models (implementable specs)

### 2.1 HVZ — Hou, van Dijk & Zhang (2012), *JAE* 53(3):504–526

```
E_{i,t+τ} = α₀ + α₁·A_{i,t} + α₂·D_{i,t} + α₃·DD_{i,t} + α₄·E_{i,t} + α₅·NegE_{i,t} + α₆·AC_{i,t} + ε
```
τ = 1..5 years. `A` = total assets, `D` = dividends, `DD` = dividend-payer dummy, `E` = earnings, `NegE` = loss dummy, `AC` = working-capital accruals. Estimated at the **dollar level** by pooled cross-sectional regression on the **previous ten years**, then coefficients applied to current characteristics (so it's ex ante). Reported lagged-earnings coefficients: **0.8304 / 0.7924 / 0.7871** for 1/2/3-year horizons. ([SSRN](https://www.ssrn.com/abstract=1561682))

**HVZ is a trap.** Li & Mohanram (2014), *RAS* 19:1152–1185, show HVZ is **worse than a naive random walk** ([full PDF](https://english.ckgsb.edu.cn/sites/default/files/evaluating_cross-sectional_forecasting_models_for_implied_cost_of_capital.pdf)), confirming Gerakos & Gramacy (2013).

### 2.2 EP and RI — Li & Mohanram (2014), the models that actually work

**EP (earnings persistence):**
```
E_{t+τ} = β₀ + β₁·NegE_t + β₂·E_t + β₃·(NegE_t × E_t) + ε
```

**RI (residual income, from Feltham–Ohlson 1996):**
```
E_{t+τ} = χ₀ + χ₁·NegE_t + χ₂·E_t + χ₃·(NegE_t × E_t) + χ₄·B_t + χ₅·TACC_t + ε
```
`B` = book value of equity per share, `TACC` = total accruals (Richardson et al. 2005). Expected signs: χ₂>0, χ₃<0, χ₄>0, χ₅<0. Estimated **per share**, same 10-year rolling pooled approach as HVZ.

**Mean absolute forecast error (per share), full Compustat:**

| Horizon | RI | EP | Random walk | HVZ |
|---|---|---|---|---|
| 1 year | **0.092** | 0.092 | 0.100 | 0.127 |
| 3 year | **0.139** | 0.146 | 0.154 | 0.215 |

RI is 28–35% more accurate than HVZ; RW is 21–28% more accurate than HVZ. RI ≈ EP at 1 year; RI pulls ahead at longer horizons. **[STRETCH]** — needs a cross-firm panel in SQLite. If we only get one firm's data, skip.

### 2.3 So (2013) — analyst errors are *predictable*

Eric So, "A new approach to predicting analyst forecast errors: Do investors overweight analyst forecasts?", *JFE* 108(3):615–640 ([Stanford/NYU PDF](https://www.stern.nyu.edu/sites/default/files/assets/documents/con_033633.pdf)).

**Step 1 — characteristic forecast.** Estimate (eq. 9) on all Compustat firms reporting in calendar year t:
```
E_{j,t} = β₀ + β₁·E_{j,t-1} + β₂·NEGE_{j,t-1} + β₃·ACC⁻_{j,t-1} + β₄·ACC⁺_{j,t-1}
        + β₅·AG_{j,t-1} + β₆·DD_{j,t-1} + β₇·DIV_{j,t-1} + β₈·BM_{j,t-1} + β₉·Price_{j,t-1} + ε
```
where `ACC = ΔACT + ΔDCL − ΔCHE − ΔCLI` (split into positive/negative parts), `AG` = % change in total assets, `DD` = zero-dividend dummy, `DIV` = DPS, `BM` = book-to-market, `Price` = fiscal-year-end share price. **Average adjusted R² = 0.561.**

**Step 2 — apply year t−1 coefficients to year t characteristics** to get the ex-ante forecast `CF_{j,t}` (eq. 10).

**Step 3 — the signal.** Characteristic forecast optimism:
```
CO_{j,t} = (CF_{j,t} − AF_{j,t}) / TA_{j,t}
```
`AF` = prevailing I/B/E/S FY1 consensus, `TA` = total assets per share. **Scale by assets, not price** — price already embeds analyst expectations, which induces spurious correlation.

**Findings that matter to us:**
- Firms whose characteristic forecast **exceeds** consensus tend to have realized earnings that exceed consensus (and vice versa) — i.e. `CO` predicts the sign of the surprise.
- Analysts subsequently **revise toward** the characteristic forecast before the announcement. They are slow.
- Unconditional Q5−Q1 strategy: **+5.8%/year**; **+9.4%/year** among firms with high earnings-response sensitivity. Stronger for small firms, firms with disappointing earnings history, low transparency.

**So's methodological point is the important one:** don't regress *past forecast errors* on characteristics (the traditional approach) — that's biased when characteristics correlate with analysts' private information. Instead predict *earnings* and take the difference from consensus. **[1-DAY]** in spirit: build a mechanical earnings estimate, then compute `CO = mechanical − consensus` and use its sign/size as a tilt.

---

## 3. What accuracy do analysts actually achieve vs mechanical models?

### 3.1 Bradshaw, Drake, Myers & Myers (2012), *RAS* 17(4):944–968

Sample 1983–2007; 740,070 consensus forecasts / 69,483 firm-years / 10,140 firms (FY1). Metric:

```
Analysts' Superiority = ( |EPS_{T-1} − EPS_T| − |Forecast EPS_{T,M} − EPS_T| ) / Price_{T,M}
```
positive ⇒ analysts beat the random walk, expressed in fractions of price. Scaled by **price**, not realized EPS (scaling by EPS makes ~30% of errors exceed 100% at long horizons).

| Horizon | Analysts' superiority |
|---|---|
| FY1, month 0 (same month as announcement) | **+245 bp** |
| FY1, month 11 | **+25 bp** |
| FY2, month 21 | +4 bp |
| FY2, months 22–23 | **−6 bp, −11 bp** (RW wins) |
| FY3, month 24 | +70 bp |
| FY3, month 35 | **−40 bp** (RW wins) |

**Conditioning — where analysts lose:**
- **Young firms.** First year on I/B/E/S: analyst FE 527bp vs RW 534bp (superiority just **7bp**). Firms ≥5 years: analyst FE 268bp vs RW 301bp (superiority **33bp**, ~5× better). At month 23, first-year firms show RW superiority of **102bp**.
- **Small firms.** RW wins at 11 months for FY1, and in 6/12 and 11/12 monthly FY2/FY3 forecasts. Differences reach ~1% of price at 23 months and ~1.5% at 35 months.
- **Lightly followed firms** (1–2 analysts): no accuracy difference from RW at the 11-month FY1 horizon.
- **Magnitude of forecast change.** At the 1-month horizon, superiority is **26bp** for the smallest forecast changes but **>600bp** for the largest. But at FY2 month 23, RW is **40bp more accurate** for large forecasted changes while analysts are 29bp better for small ones. Translation: *analysts add value precisely when they are calling a big move — over short horizons. Over long horizons, big analyst calls are worse than doing nothing.*
- **Market expectations track accuracy.** Regressing returns on forecast errors: at month 0 the RW coefficient is only **34%** of the analyst coefficient; by month 11 it's **94%**. Past ~21 months RW is the *better* proxy for market expectations.

Published-version extra: a **naive extrapolation of the analysts' 1-year-ahead forecast** is the most accurate estimator of 2- and 3-year-ahead earnings ([Springer](https://link.springer.com/article/10.1007/s11142-012-9185-8)).

### 3.2 Older baseline numbers

- **Fried & Givoly (1982)**, ~8 months ahead, prediction error = |forecast − actual| / |actual|: **analysts 16.4%**, modified submartingale RW 19.3%, plain RW 20.3%.
- **Collins & Hopwood (1980)**, 4 quarters ahead: **analysts 31.7%** vs best time-series **32.9%**.

Note how *small* the gaps are relative to the error levels. Statistically significant, economically modest.

### 3.3 Quarterly-specific evidence (closest to our setting)

- **Pagach & Warr (2020)**, *Advances in Accounting* 51 ([ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0882611020300675)): ARIMA quarterly EPS forecasts are **equal to or more accurate than consensus in ~40% of cases**. Time-series superiority rises with horizon, falls with firm size, and is higher for high-tech firms. ARIMA dominates SRW (but costs sample size).
- Lorek et al.: **Brown–Rozeff (1,0,0)×(0,1,1)** ties or beats consensus **34% of the time at 1Q ahead, 43% at 3Q ahead** (48% for high-tech at 3Q).

**Implication:** a well-built mechanical quarterly model will beat consensus roughly one time in three. That is not a strategy on its own, but it is a strong *blend component* and a legitimate baseline to show on stage.

### 3.4 Directional accuracy is barely above a coin flip

From Kim, Muhn & Nikolaev's benchmark table (see §5.1 caveat on that paper), for the direction of one-year-ahead earnings change:

| Predictor | Accuracy | F1 |
|---|---|---|
| Naive model | 49.11% | 53.02% |
| Analysts, 1 month after prior release | **52.71%** | 54.48% |
| Analysts, month 3 | 55.95% | — |
| Analysts, month 6 | 56.58% | — |
| High-ability analysts (top 20% by prior error) | 56.75% | 56.26% |

Earnings *changes* are close to unpredictable, even for professionals with a full information set.

### 3.5 Revenue is roughly 8× more forecastable than EPS

Houlihan Lokey, *Accuracy of Analyst Estimates 2024* ([PDF](http://cdn.hl.com/pdf/2024/accuracy-of-analyst-estimates-2024.pdf)), Russell 3000, 1-year consensus, weighted-average % error:

| | FY23 | 5-yr avg | 10-yr avg |
|---|---|---|---|
| **Revenue** | 6.7% | 10.2% | 9.7% |
| **Earnings** | 74.7% | 84.4% | 75.3% |

Averaged over 8 years: **9.76% (revenue) vs 84.05% (earnings) — 8.6× worse.** Also: 1-year analyst *revenue* estimates beat every CAGR model in all 11 sectors, but for *earnings* a simple CAGR model beats the best analyst estimate in **7 of 11 sectors**.

Cheng et al. decompose `Δearnings ≈ w₁·Δsales + w₂·Δmargin` and find **margin errors dominate sales errors** at every size group ([PDF](https://ira.lib.polyu.edu.hk/bitstream/10397/94394/1/Cheng_Analyst_Forecasts.pdf)).

**Design consequence: forecast revenue and margin separately, then multiply to EPS.** Put the modelling effort into margin. **[1-DAY]**

---

## 4. ML approaches to earnings and surprise prediction

### 4.1 Chen, Cho, Dou & Lev (2022), *JAR* 60(2):467–515

("Predicting Future Earnings Changes Using Machine Learning and Detailed Financial Data" — NYU Stern, not Nikolaev.) [PDF](https://www.stern.nyu.edu/sites/default/files/assets/documents/SSRN-id3741015.pdf) · [SSRN 3741015](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3741015)

- **Features:** every XBRL tag in 10-Ks — 167,136 raw tags → 4,627 common standard tags → current value + prior-year value + % change = **13,881 predictors**. Missing→0, scaled by total assets. **Footnote tags contribute the most predictive power**, then balance sheet.
- **Sample:** 8,149 10-K filings, 2012–2018; test 2015–2018. Rolling temporal split (train t−3,t−2 / validate t−1 / test t). Explicitly **no k-fold CV** — that leaks.
- **Target:** *direction* of 1-year-ahead EPS change, **de-trended** by subtracting the mean EPS change over the prior 4 years. De-trending rebalances classes from 5,418/2,731 to 3,610/4,539.
- **Models:** Random Forest (500–2000 trees, mtry≈√p≈110–120, 50% bootstrap) and Stochastic Gradient Boosting (500–2000 trees, depth 1–4, min leaf 10).

| Method | AUC | Annual size-adj. hedge return |
|---|---|---|
| XBRL + RF | 67.52% | 5.02% |
| XBRL + SGB | 67.54% | 6.57% |
| XBRL + SGB, confident subsample (p̂≥0.6 or ≤0.4) | **68.66%** | **9.74%** |
| Ou–Penman (1989) 65-var stepwise logit | 61.79% | 2.48% |
| Ou–Penman 65 vars + RF | 66.63% | 4.67% |
| **Analyst consensus direction** | **63.62–65.09%** | 2.49–3.93% |

Two conclusions worth stealing: **most of the gain comes from nonlinearity, not from the extra 13,816 features** (65 vars + RF gets 66.6% vs 67.5% for the full set); and **confidence filtering works** (68.66% AUC / 9.74% return on the confident subsample).

**⚠️ The critical negative result.** When the same models predict the **level** of one-year-ahead earnings, out-of-sample **R² = 5.3% (RF) / 6.0% (SGB), versus a random walk's 7.5%** — ML *loses to a random walk on levels*. Predicting the *amount* of the change gives R² 8.0%/5.8% but a hedge return of **0.10% (p=0.47)**, i.e. nothing.

> **Direction is tractable; magnitude is not.** Since we are scored on magnitude (revenue and EPS levels vs actuals), this is a warning that a fancy ML level-predictor will lose to a good naive anchor.

### 4.2 Hunt, Myers & Myers (2022), *Accounting Horizons* 36(1):131–149

Same Ou–Penman task. AUC: logit 0.6998, stepwise logit 0.7026, elastic net 0.7030, **random forest 0.7462**. Down-sampling/SMOTE badly *hurt* (AUC 0.59–0.66) — **do not rebalance classes**. ([DOI](https://doi.org/10.2308/horizons-19-125), [dissertation with tables](https://scholarworks.uark.edu/cgi/viewcontent.cgi?article=4410&context=etd))

### 4.3 Easton, Kapons, Monahan, Schütt & Weisbrod (2024), *TAR* 99(3):115–140 — k-NN

**The single most hackathon-implementable paper in this literature.** [Columbia PDF](https://business.columbia.edu/sites/default/files-efs/imce-uploads/CEASA/Events%20Page/forecasting_earnings_using_k-nearest_neighbors.pdf)

Algorithm: match the subject firm-year to historical firm-years with similar recent earnings histories; **forecast = median of the neighbours' lead earnings.** Tuned hyperparameters (on 1979–1995): history length **h = 2 years**, **k = 90 neighbours**. Matched firm-years must precede the subject by at least the forecast horizon.

- Beats random walk, Blouin–Core–Guay matching, HVZ/EP/EP-GICS regressions, and all 8 alternative k-NN variants on MAFE / MDAFE / MSE / TMSE.
- vs analysts: **loses at 1 year, wins at 2 and 3 years** and on aggregate 3-year EPS.
- MAFE 5.36% for analyst-covered firms vs 10.21% for uncovered.
- **Free confidence signal: the MAD of the neighbours' lead earnings predicts realized accuracy better than analyst count, B/M or size.**
- Adding more features or longer history made it **worse**.

**[1-DAY]** if we can get a panel of quarterly EPS histories into SQLite. The MAD-as-confidence trick is a cheap, defensible interval generator.

### 4.4 van Binsbergen, Han & Lopez-Lira (2023), *RFS* 36(6):2361–2396 — "Man vs. Machine Learning"

[NBER w27843 PDF](https://www.nber.org/system/files/working_papers/w27843/w27843.pdf). **⚠️ An Expression of Concern was issued in *RFS* 39(5), May 2026 ([link](https://academic.oup.com/rfs/article/39/5/1555/8502599)) — cite with care.**

Model: `E_t[eps_{i,t+τ}] = RF[Fundamentals_{i,t}, Macro_t, AF_{i,t}]`. Hyperparameters: **2,000 trees, max depth 7, sample fraction 1%, min node size 5**, cross-validated once in 1986 and then frozen. Rolling 12-month training window. Predictors winsorized at 1% and standardized.

Features: past realized EPS, monthly price/returns, **67 WRDS financial ratios**, 4 real-time Philly Fed macro series, and **the analyst forecast itself**.

**Feature importance: analyst forecast ≈ 0.20 (highest), past EPS ≈ 0.15, price ≈ 0.10**, then ROCE/ROE/pre-tax margin. In other words the state-of-the-art "beat consensus" model is essentially a **de-biased, shrunk consensus**.

**Analyst optimism, $/share (1986–2019):**

| Horizon | Mean (AF − actual) | RF bias |
|---|---|---|
| 1 quarter | **+0.028** (t=6.59) | −0.000 |
| 2 quarters | +0.053 | −0.001 |
| 3 quarters | +0.072 | +0.002 |
| 1 year | +0.154 | +0.027 |
| 2 years | +0.384 | −0.004 |

MSE (RF / analyst): 0.076/0.081 (1Q), 0.094/0.102 (2Q), 0.121/0.132 (3Q), 0.670/0.686 (1Y), 1.897/2.009 (2Y). **The RF beats consensus MSE by only ~5–6% at one quarter.** The value is the *bias correction*, not raw accuracy.

Bias signal: `(AF − ML)/Price`. Fama-MacBeth coefficient on next-month returns **−0.054 (t=−3.94)**; Q5−Q1 VW spread **−1.46%/month (t=−5.11)**, FF3 α −1.96% (t=−8.64). Notably the **1-quarter and 1-year** horizon biases do *not* predict returns — analysts try hardest at exactly those horizons.

Key negative: **linear cross-sectional earnings models (So-2013 / Frankel-Lee style) are worse than analysts out-of-sample, and their return predictability vanishes after 2000.**

### 4.5 Campbell, Ham, Lu & Wood — "When (not) to Use Machine Learning Earnings Forecasts"

[SSRN 4495297](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4495297). **90% of evaluated ML forecast specifications fail to beat analysts.** The one that wins does so by correcting predictable analyst biases tied to **(i) prior forecast errors, (ii) the level of forecasted earnings, (iii) stock price** — and the machine-vs-analyst gap **narrows in recent periods**. This is the humility paper; read it before promising the judges an ML edge.

---

## 5. Predictable components of the surprise (PEAD, base rates, thresholds)

### 5.1 Bernard & Thomas (1990), *JAE* 13:305–340 — the autocorrelation structure

[Full text](https://deepblue.lib.umich.edu/bitstreams/76760a1a-7cf1-4f33-abdd-e9cfdda79b80/download). 2,626 firms, 1974–1986.

Mean firm-specific autocorrelations of **seasonally differenced quarterly earnings**, lags 1–8:

```
+0.34, +0.19, +0.06, −0.24, −0.08, −0.07, −0.07, −0.06
```

For **SUE**: +0.40, +0.22, +0.06, −0.21, … For **SUE deciles**: +0.41, +0.23, +0.07, −0.18, … Signs agree across all 37 two-digit SIC industries at lags 1, 2 and 4. Larger firms are slightly *more* positively autocorrelated (0.36 vs 0.28 at lag 1).

Their forecast equation:
```
E[Q_t] = δ + Q_{t-4} + φ(Q_{t-1} − Q_{t-5}) + θ·ε_{t-4},   φ > 0, θ < 0
```
**SUE** = (actual − seasonal-random-walk-with-trend expectation) / (std dev of that error over up to 36 quarters), winsorized at ±5.

Worked example from the paper: quarterly earnings $10, $10, $10, $20, then Q1 actual of $11 (a +$1 shock) ⇒ implied next four expectations **$10.34, $10.19, $20.06, $10.76** — i.e. +0.34, +0.19, +0.06, then a reversal.

Three-day [−2,0] abnormal returns to long-D10/short-D1 on quarter-t SUE, at the announcement of quarter t+k: **+1.32% (t=14.63), +0.70% (t=8.46), +0.04% (n.s.), −0.66% (t=−7.86)**. The ratios (1.00, 0.53, 0.03, −0.50) track the SUE autocorrelation ratios (1.00, 0.56, 0.17, −0.44) almost exactly. Cumulative drift 8.61% through t+4.

**Directly usable prior [1-DAY]:**
```
ΔQ_t = δ + 0.34·ΔQ_{t-1} + 0.19·ΔQ_{t-2} + 0.06·ΔQ_{t-3} − 0.24·ΔQ_{t-4}
       (Δ = seasonal difference, Q_t − Q_{t-4})
```
Coefficients come pre-estimated from the paper — no fitting required.

### 5.2 Analysts underreact, but not enough

Abarbanell & Bernard (1992), *JF* 47(3):1181–1207 ([DOI](https://doi.org/10.1111/j.1540-6261.1992.tb04010.x)): analysts underreact to recent earnings in the direction Bernard & Thomas predict, but the underreaction is **at most half as large as needed** to explain the drift — the market underreacts more than analysts do. Related: analysts' own forecasts at other horizons predict **>10%** of their current-year forecast error; they **underweight the current-quarter forecast and overweight the next-year forecast** ([RAS 2021](https://link.springer.com/article/10.1007/s11142-021-09622-8)).

### 5.3 Beat/miss base rates — the highest-value-per-minute fact in this document

FactSet Earnings Insight (John Butters), [7 Aug 2026](https://insight.factset.com/sp-500-earnings-season-update-august-7-2026):

| Metric | Q2 2026 | 5-yr avg | 10-yr avg |
|---|---|---|---|
| % S&P 500 beating **EPS** consensus | 86% | **78%** | **76%** |
| Aggregate EPS surprise magnitude | 29.2%* | **+7.0%** | **+7.4%** |
| % beating **revenue** consensus | 76% | **70%** | **68%** |
| Aggregate revenue surprise magnitude | 3.2% | **+1.9%** | **+1.6%** |

\* Q2 2026's 29.2% collapses to **10.9%** excluding just Alphabet ($9.11 vs $2.88 est.) and Amazon ($5.75 vs $1.82 est.). The aggregate mean is outlier-dominated; the median is far smaller. **Use the medians/5-yr averages, and note the right skew when sizing intervals.**

**Why the beat rate is structurally above 50%** — earnings management to thresholds:
- Burgstahler & Dichev (1997), *JAE* 24:99–126: **8–12%** of firms with small pre-managed earnings *decreases* manage to an increase; **30–44%** of firms with small pre-managed *losses* manage to positive earnings.
- Degeorge, Patel & Zeckhauser (1999), *J. Business* 72(1):1–33 ([SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=138588)): thresholds are hierarchical — **positive profits > sustain last year > meet consensus** — and firms that just clear a threshold underperform afterwards.

**Consequence: the EPS surprise distribution is left-skewed with a spike just above zero.** A symmetric Gaussian error model is misspecified. Default prior should be a *small beat*, not a zero surprise.

### 5.4 Guidance is not a silver bullet

Hutton, Lee & Shu (2012), *JAR* 50(5) ([PDF](https://www.hbs.edu/faculty/Shared%20Documents/events/18/HuttonLeeShu2012.pdf)): management forecasts beat consensus **only ~50% of the time** (1,903 of 3,775) — matching Ruland (1978, 51%). Managers win at **short horizons, loss years, abnormal inventory, excess capacity**; analysts win for **cyclical, energy-exposed, regulated firms and long horizons**. Guided quarterly estimates are more accurate but **systematically pessimistic** (the classic "walk-down").

Practical: treat company guidance as roughly a coin flip against consensus, weight it *up* for loss quarters and very short horizons, and remember the guidance midpoint is set to be beatable.

---

## 6. LLM-era work

### 6.1 Kim, Muhn & Nikolaev (2024) — "Financial Statement Analysis with LLMs" ⚠️ WITHDRAWN

> **Read this before citing it on stage.** The paper was **withdrawn from arXiv on 20 Feb 2025**. Withdrawal note: *"A co-author identified inconsistencies in the data and analyses while attempting to replicate past analyses from the working paper. Accordingly, we have temporarily withdrawn the working paper from circulation while we review the research findings."* ([arXiv:2407.17866v3](https://arxiv.org/abs/2407.17866v3)). Nikolaev's Chicago Booth page confirms he independently verified the inconsistencies, and that the companion paper **"Bloated Disclosures: Can ChatGPT Help Investors Process Information?" has also been withdrawn** after failing to replicate ([faculty page](https://faculty.chicagobooth.edu/valeri-nikolaev/ongoing-research-projects)). As of 15 Aug 2026 no corrected version has appeared.
>
> The *design* is still worth stealing; the *numbers* are not safe to quote as fact. If you show them, label them as withdrawn.

**Setup** ([arXiv HTML v2](https://arxiv.org/html/2407.17866v2), Nov 2024 draft):
- Input: **2 years of balance sheet + 3 years of income statement**, standardized to Compustat's balancing model so every firm-year has an identical structure. **Company name and dates removed**, replaced with relative labels `t`, `t−1`.
- Target: **binary direction** of next year's earnings change.
- Sample: 150,678 firm-year observations / 15,401 firms, 1968–2021; analyst subsample 39,533 firm-years, 1983–2021.

**The CoT prompt — four steps** (this is the transferable artefact):
1. Identify and describe **notable changes** in financial-statement line items.
2. **Compute key financial ratios** (operating efficiency, liquidity, leverage), showing formulas.
3. Provide **economic interpretations** of the computed ratios.
4. **Synthesize** and predict the direction, with a **confidence score** and a rationale.

**Reported results (withdrawn — treat as indicative):**

| Method | Accuracy | F1 |
|---|---|---|
| Naive | 49.11% | 53.02% |
| Analysts, month 1 | 52.71% | 54.48% |
| Analysts, month 6 | 56.58% | — |
| GPT-4, **simple prompt** | 52.33% | 54.52% |
| GPT-4, **chain-of-thought** | **60.35%** | 63.45% |
| Ou–Penman stepwise logit | 52.94% | 57.23% |
| ANN (specialized) | 60.45% | 61.62% |
| ANN on **BERT embeddings of GPT's narratives** | 59% | 65% |
| Dual input (financials + GPT text) | **63.16%** | 66.33% |

Other reported findings worth designing around:
- **CoT is the whole story**: +8 points over a simple prompt. Without it, GPT-4 ≈ analysts.
- **Confidence is informative**: high-confidence group **62.44%** vs low-confidence, a **2.6pp** gap (4.6pp using logistic probabilities).
- GPT's relative edge is largest for **small firms and loss-making firms** — exactly where analysts struggle.
- Memorization tests: the model **could not guess the firm name or fiscal year** from anonymized statements; accuracy *dropped* in 1974/2008–09/2020, which is the opposite of what look-ahead leakage would produce.
- **Accuracy declines ~0.1pp/year over the 54-year sample** — numeric-only earnings prediction is getting harder.
- Model family matters: GPT-4 61.05%, Gemini 1.5 59.15%, GPT-3.5 only 52.29% on a 20% subsample.

### 6.2 Halawi, Zhang, Yueh-Han & Steinhardt (2024) — "Approaching Human-Level Forecasting with Language Models"

[arXiv:2402.18563](https://arxiv.org/abs/2402.18563). **This is the architecture to copy.** Three stages: retrieval → reasoning → aggregation.

**Retrieval (4 steps):**
1. **Query generation** — two prompts combined and unioned: (a) direct query expansion from the question, (b) **decompose into sub-questions and generate a query per sub-question** (broader coverage; e.g. for an election, one path finds polls, the other finds campaign finance / economic indicators / geopolitics).
2. **News API fetch** — evaluated 5 APIs, chose NewsCatcher + Google News.
3. **Relevance filtering** — a cheap model (GPT-3.5) rates each article on a **6-point scale** using only the **title + first 250 words**. High recall/precision at **70% cost saving**. Threshold 4.
4. **Summarization** — cheap model distills each article w.r.t. the question; top **k = 15** summaries, **ranked by relevance** (beat recency), passed to the reasoner.

**Reasoning scratchpad — four required components:**
1. **Rephrase and expand** the question using the model's own knowledge (more precise phrasing ⇒ better responses).
2. Produce **arguments for and against** the outcome, using both retrieved info and pre-training knowledge.
3. **Weigh the arguments by importance** and aggregate into an initial forecast (don't treat all considerations equally).
4. **Check for over/under-confidence, consider historical base rates**, and amend the prediction.

**Aggregation:** 6 forecasts total — 3 from the base model (best scratchpad + 2 next-best prompts) and 3 from a fine-tuned model at T=0.5 — combined by **trimmed mean**, which beat mean, median, geometric mean and universal self-consistency.

**Results (Brier score, lower is better; random = 0.250):**

| Setting | System | Crowd | **System + Crowd averaged** |
|---|---|---|---|
| All questions | .179 | **.149** | **.146** |
| Crowd uncertain (crowd 0.3–0.7) | **.238** | .240 | **.233** |
| 5+ articles retrieved | .175 | **.142** | **.140** |
| All 3 criteria met (selective) | **.240** | .247 | **.237** |

Baseline zero-shot GPT-4-1106 with no retrieval: **.208**. So retrieval + scaffolding + ensembling moved .208 → .179.

**Three findings that map straight onto our problem:**
1. **The blend of model + crowd beats the crowd in every single setting.** This is the strongest available evidence for "blend with consensus rather than replace it."
2. **The system beats the crowd exactly when the crowd is uncertain** (.238 vs .240). Analogue for us: deviate from consensus most when analyst dispersion is high.
3. The system was **naturally well calibrated**; binning and isotonic regression **did not improve it**. Don't over-engineer post-hoc calibration.

### 6.3 State of LLM forecasting as of 2026 — the Metaculus/AIB evidence

Excellent meta-review: ["AI Forecasting in 2026: What 11 Analyses Say"](https://forum.effectivealtruism.org/posts/Spyz3wESZu2eeqhDj/ai-forecasting-in-2026-what-11-analyses-say) (and [Metaculus research overview](https://www.metaculus.com/notebooks/43363/overview-of-ai-forecasting-research/)).

Brier benchmarks: superforecasters **0.081**, GPT-4.5 on ForecastBench **0.101**, AIA Forecaster backtest 0.108 vs superforecaster median 0.111.

**Techniques with measured effect sizes:**

| Technique | Effect | Notes |
|---|---|---|
| Frontier reasoning model | largest single differentiator | 34/39 Fall-2025 bots used one |
| Quality scaffolding | **+5 to +11 peer-score points/question** | ≈ 9 months of base-model progress |
| **Agentic/iterative search** (not one-shot) | **3.6× Brier degradation without it** | also cuts forecast divergence 21%→6% |
| **Ensemble 3–7 diverse models** | significant | 86% of Fall-2025 winners aggregated |
| **Platt scaling** (logistic recalibration) | **Brier −0.016** (binary), p<0.001 | cheap, replicated |
| Multiple research sources | r=0.42 | winners averaged 1.75 sources vs 1.0 |
| **Prediction capping** (clip extremes) | r=+0.48, p=0.005 | 47% of top-15 vs 29% of bottom half |
| **Explicit base-rate calculation** | r=+0.38, p=0.032 | 40% of top-15 vs 7% of bottom half |
| Lookup of similar resolved questions | Fisher p=0.04 | 34% of winners vs 0% of non-winners |
| Inference spend | winners ~**28 LLM calls/question (~$1.40)** vs 7 (~$0.50), p=0.022 | |

**What does NOT help:** picking one "best" search provider (breadth matters, not brand); optimizing against the community prediction (bots that did underperformed live, +2.76 vs +4.71 pts); multi-personality aggregation ("little to no improvement"); Bayesian-flavoured prompts (consistently underperformed in automated prompt optimization).

Also worth knowing: dev time is uncorrelated with placing top-10 (r=0.08), but **every respondent with 80+ hours won money** — the floor matters more than the ceiling.

### 6.4 LLMs on earnings specifically (2025–2026)

- **FinCall-Surprise** (ACL 2026, [anthology](https://aclanthology.org/2026.acl-long.610/)): 2,688 earnings calls (2019–2021) with transcripts, audio, and slides; 26 unimodal and multimodal LLMs evaluated. **Key warning: apparent high accuracy is "an illusion caused by significant class imbalance"** — and models fail to exploit audio/visual signals. Because ~76–78% of firms beat, a model that always says "beat" scores well. **Our eval harness must score against a "always predict a small beat" baseline, or it will lie to us.**
- **CARAG** (EACL 2026, [anthology](https://aclanthology.org/2026.eacl-long.141/)): cooperative LLM agents (historical performance / guidance credibility / peer benchmarking) retrieving from a Causal-Temporal Knowledge Graph built from statements and calls. SOTA zero-shot on NASDAQ/NYSE/MAEC for post-earnings price shocks. The **role-specialized agent decomposition** is a good design pattern to copy for the demo. **[STRETCH]** on the KG.
- **Chhaochharia, Kumar, Murali & Rantala, "Aggregating Artificially Intelligent Earnings Forecasts"** (Miami Herbert, [PDF](https://www.mbs.miami.edu/_assets/pdfs/faculty-research/business-conferences/machine-learning/ville-rantala.pdf)). I/B/E/S detail file, 1984–2019Q3. Core idea: **individual analyst errors are more predictable than the consensus error**, so de-bias each analyst and *then* aggregate. Analyst-wise neural network improves earnings predictability **24%** vs a linear benchmark and predicts the **sign of the earnings surprise 68% of the time vs 54%** for the linear model; long–short strategy earns **0.50%/month** risk-adjusted. Sample stats: mean price-scaled forecast error 0.056 (sd 1.14); mean 5.7 analysts per announcement, median 4; consensus defined as the **median** of outstanding estimates. **[STRETCH]** — needs analyst-level detail data, but the framing ("de-bias the components, then aggregate") is free.

---

## 7. Combination, ensembling and shrinkage

### 7.1 Bates & Granger (1969) — the optimal-weight formula

For `y_c = w·y₁ + (1−w)·y₂`:
```
var(y_c) = w²σ₁² + (1−w)²σ₂² + 2w(1−w)ρσ₁σ₂
w*       = (σ₂² − ρσ₁σ₂) / (σ₁² + σ₂² − 2ρσ₁σ₂)
ρ = 0    ⇒ w* = (1/σ₁²) / (1/σ₁² + 1/σ₂²)        [inverse-variance]
```
N-forecast form: `w* = Σ⁻¹𝟙 / (𝟙ᵀΣ⁻¹𝟙)`, where Σ is the **forecast-error** covariance matrix.

### 7.2 The forecast combination puzzle — why equal weights win

Clemen (1989), *IJF* 5:559–583, reviewing 209 papers ([PDF](https://www.cin.ufpe.br/~cemb/Mestrado/13.CombiningReview-Clemen-IJOF-89.pdf)): combination reliably improves accuracy, and the **simple average is the benchmark any clever scheme must beat**.

Smith & Wallis (2009), *OBES* 71(3):331–355: the cause is **finite-sample estimation error in the weights**.

Claeskens, Magnus, Vasnev & Wang (2016), *IJF* 32:754–762 ([PDF](https://www.janmagnus.nl/papers/JRM113a.pdf)) give the closed form — when `w` is estimated, the combination is **biased even if both inputs are unbiased**:
```
E[y_c]   = μ + cov(w, y₁ − y₂)
var(y_c) = (Ew)²σ₁² + (1−Ew)²σ₂² + 2(Ew)(1−Ew)ρσ₁σ₂
           + var(w)·var(y₁ − y₂)        ← ESTIMATION PENALTY
           + [cov(w, y₁ − y₂)]²
```

**Direct consequence for us:** the cost of estimating a blend weight scales with `var(F_model − F_consensus)`. Precisely when our model loudly disagrees with the Street, an estimated weight is most dangerous. Use a **fixed** weight. (Adding an intercept absorbs the bias term.)

**When the simple average loses:** Capistrán & Timmermann (2009), *JBES* 27(4):428–440 — least-squares combination dominates equal weights when equal weights are badly suboptimal *and* the panel is balanced; it collapses on unbalanced panels. Their recommended middle ground is a 2-parameter affine projection onto the equal-weighted mean, which is exactly the right tool here:
```
ỹ_{t+1} = a + b · Ȳ_{t+1|t}        (nests equal weights at a=0, b=1 — and that's testable)
```
**[1-DAY]** — two parameters, fit on 20–40 historical quarters.

### 7.3 Trimming and medians

Jose & Winkler (2008), *IJF* 24:163–169 (M3: 3003 series × 22 methods, plus SPF): **trim 10–30%** or **Winsorize 15–45%**; trim more when the individual forecasts are more variable. Both slightly beat the mean and materially cut tail-error risk. Median-vs-mean is genuinely unsettled in the literature (better in Agnew 1985, worse in Stock & Watson 2004).

### 7.4 Shrinkage toward the anchor

Stock & Watson (2004), *J. Forecasting* 23:405–430 ([PDF](https://www.princeton.edu/~mwatson/papers/Stock_Watson_JoForc_2004.pdf)):
```
w_i = λ·ŵ_i^OLS + (1−λ)·(1/n),   λ = max{0, 1 − κ·n/(t − h − T₀ − n)},   κ ∈ {0.25, 0.5, 1}
```
Their headline: **the best combinations are the ones least sensitive to recent individual performance.**

### 7.5 Does blending with consensus beat consensus? Yes — but the weight on consensus is high

- **Halawi et al.**: model+crowd average beat the crowd in **every** reported setting (§6.2 table).
- **van Binsbergen et al.**: the winning RF puts the **analyst forecast as its single most important feature (0.20)** and only improves quarterly MSE ~5–6%.
- **Lin, Tao & Wu (2022)**, *J. Empirical Finance* 68:133–159: regression-based combination of analyst forecasts beats consensus consistently, and **gains increase with analyst dispersion, bias, and under/overreaction**.
- **Lobo & Nair (1990)**, *Decision Sciences* 21:446–460: combined statistical + analyst beats either.

**Defensible prior: `w_consensus ≈ 0.75–0.85` for EPS, maybe 0.65–0.75 for revenue**, with the model contributing (i) a horizon-scaled bias correction and (ii) larger deviations only when dispersion is high or consensus is stale.

### 7.6 Aggregating multiple LLM samples — use the median

"Probing LLM World Models: Wisdom-of-Crowds Decoding" (EMNLP 2025, [PDF](https://aclanthology.org/2025.emnlp-main.234.pdf)): 10 LLMs × 3 numeric-estimation datasets. **Median of k sampled CoT answers consistently beats self-consistency (mode), greedy decoding, and the mean** (Wilcoxon p<0.001/0.02/0.02). **WOC at 5 samples beat self-consistency at 30 samples** on two datasets. Human anchor: median error ε=0.57, mode 0.61, **mean 0.91** — the arithmetic mean is wrecked by right skew on positive quantities (like revenue).

Original self-consistency (Wang et al. 2022): GSM8K 56.5% → 74.4% at k=40, with gains plateauing well before that.

**Use the median (or a 20% trimmed mean) of k ≈ 9–15 samples. Never the plain mean.** **[1-DAY]**

### 7.7 Extremizing — don't

Probability form (Karmarkar/LLO): `p_ext = p^a / (p^a + (1−p)^a)`, GJP practice a≈2. Real-valued form (Satopää & Ungar, [arXiv:1506.06405](https://arxiv.org/abs/1506.06405)): `F_ext = m + a(F̄ − m)`, a>1.

In our setup the "marginal mean" m ≈ consensus, so extremizing means **deliberately amplifying our deviation from the Street on a single scored quarter**. Small gains most of the time, occasional large losses. Later evidence suggests the GJP extremizing win was partly a fluke. **Recommendation: do not extremize — and say so on the slide, it's a good design point.** Note this is consistent with the Metaculus finding that **prediction capping** (clipping extremes) correlates positively with winning.

---

## 8. Intervals, calibration and scoring

### 8.1 Scoring rules

```
Pinball:   L_τ(y, q) = (τ − 1{y < q})·(y − q)
CRPS(F,y) = ∫ (F(z) − 1{y ≤ z})² dz = 2∫₀¹ L_α(F⁻¹(α), y) dα
```
**Sample form of CRPS** (feed k LLM samples straight in — ~15 lines of TypeScript, no quantile fitting):
```
CRPS = (1/k)·Σ_i |x_i − y| − (1/(2k²))·Σ_i Σ_j |x_i − x_j|
```
Interval (Winkler) score:
```
W_α(l,u,y) = (u − l) + (2/α)(l − y)·1{y<l} + (2/α)(y − u)·1{y>u}
```

### 8.2 Split conformal prediction — [1-DAY], ~1 hour

1. Split history into proper-train `I₁` and calibration `I₂` (|I₂| = n).
2. Fit `ĥ` on `I₁` only.
3. Residuals on calibration: `R_i = |Y_i − ĥ(X_i)|`, i ∈ I₂.
4. `q̂` = the `⌈(1−α)(n+1)⌉`-th smallest `R_i`.
5. `C(X_new) = [ĥ(X_new) − q̂, ĥ(X_new) + q̂]`.

Finite-sample coverage ≥ 1−α under exchangeability. Needs `n ≥ ⌈1/α⌉ − 1` (n ≥ 9 for 90%). ([Tibshirani notes](https://www.stat.berkeley.edu/~ryantibs/statlearn-s24/lectures/conformal.pdf)) **Use normalized scores** across firms: `R_i = |Y_i − ĥ| / s(X_i)` with `s` = trailing revenue, or |consensus|, or the std dev of analyst estimates; the interval becomes `ĥ ± q̂·s(X)`.

### 8.3 LLM intervals are far too narrow

FermiEval ([arXiv:2510.26995](https://arxiv.org/abs/2510.26995)): **nominal 99% LLM intervals cover the truth only ~65% of the time** across modern models. A conformal adjustment restores 99% observed coverage and **cuts the Winkler score by 54%**.

Fixes, cheapest first: (a) elicit **quantiles** (p10/p25/p50/p75/p90) rather than "estimate ± CI"; (b) widen multiplicatively on the **log** scale using backtest residuals; (c) with no calibration data, widen half-widths **2–3×** as a crude prior.

Counterpoint from Halawi et al.: their *ensembled* system was naturally well calibrated and post-hoc binning/isotonic did not help. Ensembling many samples appears to do much of the calibration work by itself.

### 8.4 Interval-width priors from the surprise distribution

From §5.3: **revenue** 90% interval ≈ **±2–4% of consensus**; **EPS** far wider in % terms, **right-skewed with a spike just above zero**, and percentage surprise is meaningless when EPS ≈ 0.

### 8.5 Which accuracy metric to use — this matters, EPS can be near zero or negative

- **MAPE** `mean|y−ŷ|/|y|` — undefined at y=0, explodes near-zero EPS, asymmetric, meaningless for negative EPS. **Disqualified for EPS.**
- **sMAPE** — unstable around zero (Hyndman & Koehler 2006), misbehaves with negatives. Also disqualified.
- **MASE** `MAE / [1/(n−m)·Σ|y_t − y_{t−m}|]` — scale-free, robust; the Hyndman & Koehler standard.

**Recommended harness:**
1. **Revenue:** plain APE `|R̂ − R| / R` (large and positive, so APE is safe).
2. **EPS:** **never** percentage. Use **price-scaled error** `(EPS_hat − EPS_act) / Price` — the accounting-literature standard (Bradshaw et al., van Binsbergen et al.), immune to EPS≈0 and negative EPS. Alternative: scale by the std dev of analyst estimates (SUE-style).
3. **Versus the Street:** `Skill = 1 − |ŷ − y| / |consensus − y|` (>0 means we beat consensus). **Clip the denominator at a floor** (e.g. 0.25 × σ_analysts) so a near-perfect consensus can't blow the ratio up. Report **median skill and win-rate**, not the mean.
4. **Distributional:** sample-form CRPS + p10–p90 coverage.
5. **Mandatory baselines in the harness:** consensus itself; seasonal random walk; "consensus + historical median beat" (i.e. always predict a small beat). Per FinCall-Surprise, without that last baseline our scores will flatter us.

---

## Implications for our build

Ranked by (expected value ÷ cost). Everything at rank 1–7 is a single day's work.

| # | Technique | Why (evidence) | Cost | Expected value |
|---|---|---|---|---|
| **1** | **Anchor on consensus; blend with a fixed weight `F = 0.8·consensus + 0.2·F_model` (EPS), `0.7/0.3` (revenue). No estimated weights.** | Halawi: model+crowd beat crowd in *every* setting (.146 vs .149). van Binsbergen: consensus is the RF's top feature (0.20) and the RF only cuts 1Q MSE ~5%. Claeskens: estimated weights carry a `var(ŵ)·var(F₁−F₂)` penalty that is worst exactly when we disagree loudly. | 15 min | **Very high.** This is the difference between "beats consensus sometimes" and "loses badly once." |
| **2** | **Base-rate prior on the surprise: default to a small beat — EPS `+7%` (5-yr avg), revenue `+1.7%` — then move off it only on evidence.** | FactSet 5/10-yr: 78%/76% beat EPS, 70%/68% beat revenue; median magnitudes +7.0%/+1.9%. Burgstahler-Dichev + Degeorge et al. explain *why* it's structural. Metaculus: explicit base-rate calculation correlates with winning (r=+0.38, p=0.032). | 20 min | **Very high.** Beating consensus 50% of the time is the bar; a small-beat prior beats it ~76% of the time on sign. |
| **3** | **Forecast revenue and margin separately, then multiply to EPS.** | Houlihan Lokey: consensus revenue error 9.8% vs earnings error 84.0% — 8.6× gap. Cheng et al.: margin errors dominate sales errors. Revenue is where a model can actually add value; margin is where the error lives. | 1 hr | **High.** Also a strong design/story point for the judges. |
| **4** | **Median (not mean) of k=9–15 LLM samples per line item; 20% trimmed mean if combining heterogeneous model outputs.** | EMNLP 2025 WOC decoding: median beats mode/greedy/mean, p<0.001; k=5 median beat k=30 self-consistency. Human anchor: mean error 0.91 vs median 0.57 on positive quantities. Halawi: trimmed mean of 6 beat mean/median/geometric/USC. | 30 min | **High.** Cheapest accuracy lever with hard evidence. |
| **5** | **Halawi-style pipeline: query decomposition → news retrieval → cheap-model relevance rating (title+250 words, 6-pt scale, threshold 4) → summarize → top-15 by relevance → 4-part scratchpad (rephrase, args for/against, weigh by importance, check confidence against base rates) → trimmed-mean ensemble.** | Retrieval + scaffolding moved Brier .208 → .179. Metaculus 2026: agentic search worth **3.6× Brier**; scaffolding worth +5 to +11 peer points ≈ 9 months of base-model progress. | 3–4 hrs | **High**, and it *is* the demo. |
| **6** | **Eval harness with the right metrics and the right baselines:** revenue APE; EPS price-scaled error; consensus-skill with a clipped denominator; sample-form CRPS; p10–p90 coverage. Baselines: consensus, seasonal random walk, "consensus + median historical beat". | MAPE/sMAPE break on near-zero and negative EPS. FinCall-Surprise: apparent LLM accuracy on surprise is "an illusion caused by class imbalance" — the always-beat baseline is essential. | 1.5 hrs | **High.** Without this we hill-climb on noise. |
| **7** | **Bernard–Thomas SUE prior as the mechanical baseline.** `ΔQ_t = δ + 0.34·ΔQ_{t-1} + 0.19·ΔQ_{t-2} + 0.06·ΔQ_{t-3} − 0.24·ΔQ_{t-4}` on seasonal differences. | Coefficients pre-estimated from Bernard & Thomas (1990) Table 1 — no fitting needed. Beaver's +0.416 serial correlation says the plain seasonal random walk is misspecified. | 30 min | **Medium-high.** Free baseline, and the lag-4 reversal term is a genuinely non-obvious signal. |
| **8** | **Foster (1977) Model 5 + seasonal random walk as reference baselines in the harness.** `E[Q_t] = Q_{t-4} + φ(Q_{t-1} − Q_{t-5}) + δ`. | Pagach & Warr: quarterly ARIMA ties/beats consensus **~40%** of the time; Brown–Rozeff ties/beats **34%** at 1Q. Needs only ~8 quarters of history. | 30 min | **Medium.** Cheap, and it makes the "we know the classical literature" point. |
| **9** | **Analyst-optimism haircut on consensus, horizon-scaled: −$0.028/share at 1Q (van Binsbergen et al. Table 2), or ≈ −0.6% of price.** | Analyst forecasts are biased optimistic at every horizon; RF bias is ~0. Campbell et al.: the only ML specs that beat analysts do so by correcting predictable bias tied to prior errors, forecast level, and price. | 20 min | **Medium.** ⚠️ Interacts with #2 — the beat-rate base rate already embeds most of this. **Pick one, don't double-count.** |
| **10** | **Split conformal intervals** on price-scaled residuals from a 20–40-quarter backtest; widen any raw LLM interval 2–3× on the log scale if no calibration data. | FermiEval: nominal 99% LLM intervals cover only ~65%; conformal adjustment cuts Winkler score 54%. | 1 hr | **Medium.** Doesn't help point accuracy, but intervals with a coverage guarantee are a strong design-judging asset. |
| **11** | **Confidence-gated deviation:** only deviate materially from consensus when (a) analyst dispersion is high, (b) retrieval found ≥5 relevant articles, (c) our k samples agree. | Halawi: system beats crowd exactly when the crowd is uncertain (.238 vs .240) and with 5+ articles. Chen et al.: confident subsample AUC 68.66% vs 67.5%. Easton et al.: neighbour MAD predicts accuracy better than analyst count/size/B-M. | 45 min | **Medium.** Cheap risk control; strong story. |
| **12** | **Capistrán–Timmermann affine calibration `a + b·consensus`** fit on 20–40 past quarters, with an F-test against (a=0, b=1). | Two parameters only; nests equal weighting and lets us *show* whether the deviation is justified. | 1 hr | **Medium.** Only if we have a clean panel of historical consensus vs actuals. |
| **13** | **k-NN forecaster (Easton et al.):** h=2 years of history as match key, k=90 strictly-earlier firm-quarters, forecast = median of neighbours' lead value; ship neighbour MAD as the confidence band. | Beats RW, HVZ, EP, and 8 k-NN variants; adding features made it *worse*. | 2 hrs | **Medium** — *conditional on getting a cross-firm quarterly panel into SQLite.* If we only have one firm's history, skip. |

### Explicitly do NOT do

- **Do not build an ML model to predict the earnings *level*.** Chen et al.: out-of-sample R² 5.3–6.0% vs a random walk's **7.5%**. ML wins on direction, loses on magnitude — and we're scored on magnitude.
- **Do not use HVZ.** It loses to a naive random walk (Li & Mohanram; Gerakos & Gramacy). If you want a cross-sectional model, use **RI** or **EP**.
- **Do not use any linear cross-sectional earnings model as the primary forecast.** van Binsbergen et al.: worse than analysts out-of-sample, predictability gone post-2000. Use So-2013 style models for the *tilt signal* (`CO = mechanical − consensus`), not the level.
- **Do not extremize** away from consensus. Wrong risk profile for a single scored quarter; Metaculus finds prediction *capping* correlates with winning (r=+0.48).
- **Do not rebalance classes** if we do any classification (Hunt et al.: SMOTE/down-sampling dropped AUC from 0.75 to 0.59–0.66).
- **Do not build a 13,881-feature XBRL pipeline** (Chen et al. show most of the gain is nonlinearity, not feature count).
- **Do not quote Kim/Muhn/Nikolaev's numbers as established fact.** Withdrawn Feb 2025 for replication failures, along with the companion "Bloated Disclosures" paper. The **four-step CoT prompt design is still worth copying**; the 60.35% is not safe to cite unlabelled. Same caution on van Binsbergen et al. (Expression of Concern, *RFS* May 2026).
- **Do not treat management guidance as authoritative.** Hutton, Lee & Shu: guidance beats consensus only ~50% of the time, and guided estimates are systematically pessimistic by design.
- **Do not use MAPE or sMAPE anywhere near EPS.**
