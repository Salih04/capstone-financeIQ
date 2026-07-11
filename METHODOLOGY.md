# Methodology

How FinanceIQ scores BIST stocks and validates those scores against realized
performance. Written to be honest about what the scores can and cannot do.

> **Honest result (2026-06):** with 40 validated features and an expanded
> 81-ticker internal training universe, the walk-forward signal is still
> **weak/unstable** — overall Spearman remains close to zero and ML does not
> establish a reliable edge over simple baselines. Scores are research support,
> **not** investment advice.
> Hybrid research score = 0.65·ML + 0.20·confidence + 0.15·AI-evidence, components always shown.
> The AI-evidence term contributes ONLY when the local model returns a meaningful score
> in (0,1]; a null/zero value means "AI evidence unavailable" and its weight is
> redistributed to ML + confidence (the AI can never drag or dominate the final score).

## Data

Primary trusted modeling outputs:

- `data/trusted_clean/modeling_dataset_training_2020_2025.csv`: internal training
  split, 403 rows / 81 tickers / 321 target rows.
- `data/trusted_clean/modeling_dataset_public_2020_2025.csv`: public UI split,
  240 rows / 40 tickers / 200 target rows.

Realized yearly return is treated strictly as **ground truth / target**, never as
a feature for the same row. The 2025 rows are inference-only unless explicit,
validated T+1 outcome data is added later.

### Important data reality: source fields are mixed-quality

Verified by `scripts/validate_trusted_data.py` (`column_variability`):

- **Accepted per-year fundamentals:** corrected income statement, profitability,
  balance-sheet, leverage, liquidity, growth, cash-flow-derived fields, and
  free-reconstructed valuation fields where inputs pass shape/coverage checks.
- **Accepted year-T market features:** Yahoo year-end price, year-T return,
  volatility, drawdown, benchmark-relative return, dividend/split indicators,
  sector metadata, and data-coverage indicators.
- **Rejected or guarded fields:** frozen snapshot columns, current-only multiples,
  same-row realized returns, future-derived targets, and any post-target fields.

Consequences, stated honestly:

- The dataset is more realistic than the original frozen snapshot, but still
  small and sparse.
- The expanded 81-ticker universe is used internally for training and evaluation;
  the public UI universe remains the selected 40 BIST companies.
- The product does **not** claim robust predictive alpha. It tests whether
  leakage-safe year-T information has measurable T+1 rank signal.

## Two separate scores

### Fundamental Score
Built only from financial-statement, valuation, growth, balance-sheet, and
cash-flow metrics. Cross-sectional **rank normalization within each year**:
every metric is ranked into a percentile, lower-is-better metrics (P/E, leverage,
…) are inverted, value multiples are ranked over positive values only, and
missing values are excluded and tracked (never filled with fake zeros). Category
scores are averaged into a 0–100 score. Rank normalization is robust to the
dataset's extreme outliers (growth % in the trillions) without deleting data.

### Market/Price Features
Year-T price-derived features can be used in the T→T+1 experiment only when the
measurement window ends inside year T. Same-row realized return and future price
movement are target-only and never feature inputs.

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
   training). It compares simple baselines and ML models on year-T features
   against year-(T+1) outcomes.

## Serving-side experimental ranking heuristic ≠ walk-forward models

The CSV-backed ranking shown by the forecasting service is a deterministic,
explainable heuristic, not one of the linear or tree models evaluated by the
`experiments/` walk-forward harness. Its source is
`backend/app/services/forecasting_csv_service.py`; the relevant functions are
`train_parameters()` and `run_forecast()`.

`train_parameters()` uses the internal training split and finalized T→T+1
targets by default (2020–2024). Within each training year, it marks companies
at or above the 75th percentile of realized next-year return as historical
top-quartile "winners." For each usable numeric feature, it calculates a
non-negative discrimination score from the absolute standardized difference
between the winner mean and the overall training mean, multiplied by the
feature's non-null coverage among winners. It then normalizes each score by the
largest feature score and selects the highest-weighted features (12 by default).

`run_forecast()` applies those selected weights to the public-universe rows for
one input year. It percentile-ranks each available feature across that year's
public companies, multiplies each percentile by the calculated heuristic weight,
and divides the summed contributions by the total selected weight to produce a
bounded ranking score. Missing features are omitted from a company's
contributions and reduce its reported confidence; they are never fabricated.
The service also exposes the contributing features, missing features, and an
experimental-ranking disclaimer. It does not emit buy/sell/hold signals or
price targets.

This mechanism describes which feature values **historically co-occurred with
top-quartile returners in this small sample**; it does **not** establish that
they predict future winners. Its weights are not validated predictive model
parameters, and the walk-forward experiment result remains weak/unstable
(Spearman IC near zero, with no reliable predictive edge). The ranking is
therefore research support only, not investment advice.

## Honest findings (current data)

- Walk-forward signal remains weak/unstable. The expanded pipeline improved the
  test bed, but not enough to justify claiming reliable signal.
- Before expansion, overall Spearman was about **0.007**. After adding the
  expanded training universe and leakage-safe price/benchmark features, overall
  Spearman is about **0.042**. This is still close to zero.
- The best ML run can look better in isolated folds, but stability is limited.
  The correct conclusion is uncertainty, not a predictive edge.

## Leakage controls

Enforced in `app/services/research/feature_registry.py`:
- Realized return is target-only.
- Same-row realized return is barred from features.
- Next-year prediction uses only prior-year features.
- Selected year never silently falls back to the latest year.
- 2025 is inference-only unless explicit validated T+1 outcomes are added.

## Forward forecast: 2025 → 2026 (inference, not a backtest)

The training/backtest window ends at **2024** because finalized T+1 labels are
available through 2025. 2025 is **not missing** — its rows are used as
**inference inputs**:

- Train the signal on finalized annual T+1 targets, 2020–2024.
- Apply the learned weights to 2025 financial rows → a **2026 forward-looking
  ranking** of the 40 public companies.
- 2026 realized returns do not exist yet, so this ranking is
  `unevaluated_forward_forecast` — never presented as a backtest or realized result.

Endpoint: `GET /forecasting/inference?year=2025` (public). Each row carries
`input_year=2025`, `target_year=2026`, `is_inference=true`,
`realized_return_available=false`. This is the main forward output and is kept
separate from the experimental partial-target mode below.

## Experimental: 2025 partial 2026-YTD target mode (opt-in)

The headline methodology is **finalized annual T+1 only** (2020–2024 training). It
is the sole basis for every model-quality claim (Spearman, IC, walk-forward).

An OPTIONAL experimental mode (`target_mode=include_partial_2025`) can include
2025 using a **partial 2026 year-to-date return** as a stand-in target:

- `target_year = 2026`, `target_status = "partial_ytd"`, `comparable_to_full_year = false`.
- Warning attached everywhere: *"2025 uses partial 2026 YTD return and is not
  directly comparable to finalized annual targets."*
- It is **never** mixed into the headline finalized result. Any Spearman/IC that
  uses partial 2025 must be reported separately and labeled experimental/partial.
- 2025 never appears as a normal finalized training year; `trainable_years`
  stays 2020–2024 in all modes.
- Requires real 2026 price data (`data/trusted_clean/partial_2026_ytd_returns.csv`).
  Absent by default → mode reports unavailable and excludes 2025. No fabrication.

## Limitations

- Small dataset, even after expansion. All out-of-sample numbers are noisy;
  overfitting is easy.
- No survivorship/look-ahead audit of how the 40-company universe was selected.
- BIST100 benchmark/excess-return fields exist where source coverage is valid;
  they are not available for every expanded training row.
- Supervised ML is **not** presented as a reliable trained predictor.

## Disclaimer

Research and educational tool. **Not financial advice.** Scores describe
historical cross-sectional patterns in a small dataset and do not predict future
returns.
