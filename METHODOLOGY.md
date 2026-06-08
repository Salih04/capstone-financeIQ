# Methodology

How FinanceIQ scores BIST stocks and validates those scores against realized
performance. Written to be honest about what the scores can and cannot do.

> **Honest result (2026-06):** with 32 validated features (incl. real income/
> profitability and free-reconstructed valuation) the walk-forward signal is still
> **weak/unstable** — mean Spearman ≈ 0 and ML does not consistently beat a simple
> baseline on ~40 stocks/year. Scores are research support, **not** investment advice.
> Hybrid research score = 0.65·ML + 0.20·confidence + 0.15·AI-evidence, components always shown.
> The AI-evidence term contributes ONLY when the local model returns a meaningful score
> in (0,1]; a null/zero value means "AI evidence unavailable" and its weight is
> redistributed to ML + confidence (the AI can never drag or dominate the final score).

## Data

Single trusted source: the 2020–2025 yearly dataset
(`data/trusted/stocks_2020_2025.csv`), 40 BIST companies × 6 years. No external
APIs, no synthetic data. Realized yearly return (`annual_return_pct`) is treated
strictly as **ground truth / target**, never as a feature.

### ⚠️ Important data reality: the dataset is INCONSISTENT

Verified by `scripts/validate_trusted_data.py` (`column_variability`):

- **Frozen across years** (a single 2025 snapshot repeated in every file):
  income statement (revenue, net income, EBITDA, operating income), profitability
  (ROE, ROA, ROIC, margins), valuation multiples (P/E, P/B, EV/EBITDA, PEG),
  price, market cap, and **all** momentum/return windows (1W…5Y).
- **Genuinely per-year**: balance sheet (total/current/non-current assets,
  liabilities, equity, working capital, net debt), leverage & liquidity ratios
  (current ratio, leverage ratio, financial-debt ratio, net-debt/EBITDA), the
  growth % columns, and the realized annual return (`annual_return_pct`).

Consequences, stated honestly:

- The **Fundamental Score only partly varies** across years — its Profitability,
  Value and Size categories are frozen; only Balance-Sheet and Growth move.
- Year-over-year analysis of profitability/valuation is **not meaningful** on this
  data; those fields do not actually change between files.
- Robust multi-year fundamental forecasting is **not supported** until the
  income-statement/valuation fields are real per-year history.

The product still answers the core question — "our score rates this company
strong; did the stock actually perform in year X, and where did it rank?" —
because realized returns are real and per-year. It does **not** claim time-series
fundamental forecasting on this data.

## Two separate scores

### Fundamental Score
Built only from financial-statement, valuation, growth, balance-sheet, and
cash-flow metrics. Cross-sectional **rank normalization within each year**:
every metric is ranked into a percentile, lower-is-better metrics (P/E, leverage,
…) are inverted, value multiples are ranked over positive values only, and
missing values are excluded and tracked (never filled with fake zeros). Category
scores are averaged into a 0–100 score. Rank normalization is robust to the
dataset's extreme outliers (growth % in the trillions) without deleting data.

### Market-Aware Score
Built only from momentum/return windows (3M, 6M, YTD, 1Y, 3Y, 5Y). Reported
separately and **never mixed** into the Fundamental Score, because momentum
overlaps the realized-return window and would leak the target.

## Literature motivation (references, not data)

- **Fama–French five-factor** (value, profitability, investment, size): motivates
  using valuation multiples, margins/returns-on-capital, growth/investment, and
  size as cross-sectional return descriptors.
- **q-factor model** (Hou–Xue–Zhang): profitability and investment as the core
  drivers — reflected in our Profitability and Growth categories.
- **Expected profitability and returns**: profitable firms have historically
  carried a return premium; we test whether that holds on BIST here.
- **Financial ratios and stock returns / MCDM ranking**: multi-criteria ranking
  of firms by financial ratios — our rank-normalized category averaging is a
  transparent MCDM-style aggregation.
- **Decision-tree / ML on financial ratios**: motivates the experiment loop,
  where ML models must beat simple ratio baselines to be used at all.

These are **motivation only**. We do not claim to reproduce any paper's results.

## Same-year explanation ≠ future prediction

Two clearly separated questions:

1. **Explanatory (same year):** did high-Fundamental-Score companies also have
   high realized return *that same year*? Measured by Pearson/Spearman
   correlation, top-k hit rate, and quintile spread (`/research/validation`).
   This is descriptive, **not** a forecast.
2. **Predictive (next year):** the `experiments/` walk-forward harness is built
   with strict leakage controls (no same-year target, no future data in
   training) and is ready for genuinely time-varying fundamentals. **On the
   current data it is degenerate**: because fundamentals are a static snapshot,
   the "year-Y features" are identical every year, so the harness effectively
   tests one fixed fundamental ranking against each year's returns. Treat its
   numbers as illustrative of the pipeline, not as real out-of-sample
   forecasting skill.

## Honest findings (current data)

- Same-year: the single fundamental cross-section has mean Spearman ≈ **−0.08**
  against realized return across 2020–2025 — **negative/weak** in 2020–2023
  (notably the 2021–2022 hyperinflation rally, where low-quality names led),
  positive only in 2024–2025. The static Fundamental ranking does **not** reliably
  match the best-performing stocks in most years.
- Experiment harness: the **equal-weight baseline beats every ML model** on rank
  correlation — but see the degeneracy caveat above; with static features this
  mostly reflects ML overfitting noise on 40 samples. No heavy model is deployed.

## Leakage controls

Enforced in `app/services/research/feature_registry.py`:
- Realized return is target-only.
- Momentum is barred from same-year explanatory scoring (overlaps target).
- Next-year prediction uses only prior-year features.
- Selected year never silently falls back to the latest year.

## Limitations

- Tiny dataset (40 × 6). All out-of-sample numbers are noisy; overfitting is easy.
- No survivorship/look-ahead audit of how the 40-company universe was selected.
- BIST100 benchmark is **not** included; excess-return is hidden until the user
  provides real values in `data/trusted/bist100_benchmark_returns.csv`.
- Supervised ML is **not** presented as a trained predictor — baselines win.

## Disclaimer

Research and educational tool. **Not financial advice.** Scores describe
historical cross-sectional patterns in a small dataset and do not predict future
returns.
