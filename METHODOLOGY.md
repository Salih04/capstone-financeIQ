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
