# Experiment summary (benchmark-aware, walk-forward)

Small data (~40 stocks/year), leakage-controlled. Treat all numbers as noisy.
Features are largely a static snapshot; baselines usually match/beat ML.

Targets evaluated: ['next_year_excess_return_vs_bist100', 'next_year_outperform_bist100', 'next_year_return_pct', 'next_year_top_20pct_returner']

## next_year_excess_return_vs_bist100
- baseline mean Spearman: -0.016
- best ML Spearman: 0.132
- ML beats baseline: True

## next_year_outperform_bist100
- baseline mean Spearman: -0.054
- best ML Spearman: 0.169
- ML beats baseline: True

## next_year_return_pct
- baseline mean Spearman: 0.197
- best ML Spearman: 0.206
- ML beats baseline: True

## next_year_top_20pct_returner
- baseline mean Spearman: 0.112
- best ML Spearman: 0.169
- ML beats baseline: True
