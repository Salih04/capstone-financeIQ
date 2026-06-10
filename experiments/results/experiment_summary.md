# Experiment summary (benchmark-aware, walk-forward)

Small data (~40 stocks/year), leakage-controlled. Treat all numbers as noisy.
Features are largely a static snapshot; baselines usually match/beat ML.

Targets evaluated: ['next_year_excess_return_vs_bist100', 'next_year_outperform_bist100', 'next_year_return_pct', 'next_year_top_20pct_returner']

## next_year_excess_return_vs_bist100
- baseline mean Spearman: -0.098
- best ML Spearman: 0.168
- ML beats baseline: True

## next_year_outperform_bist100
- baseline mean Spearman: -0.131
- best ML Spearman: 0.128
- ML beats baseline: True

## next_year_return_pct
- baseline mean Spearman: -0.098
- best ML Spearman: 0.168
- ML beats baseline: True

## next_year_top_20pct_returner
- baseline mean Spearman: -0.098
- best ML Spearman: 0.096
- ML beats baseline: True
