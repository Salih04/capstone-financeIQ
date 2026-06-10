# Experiment summary (benchmark-aware, walk-forward)

Small data (~40 stocks/year), leakage-controlled. Treat all numbers as noisy.
Features are largely a static snapshot; baselines usually match/beat ML.

Additional reports: `feature_coverage.csv`, `feature_stability_summary.csv`, `coverage_impact.csv`.

Targets evaluated: ['next_year_excess_return_vs_bist100', 'next_year_outperform_bist100', 'next_year_return_pct', 'next_year_top_20pct_returner']

## next_year_excess_return_vs_bist100
- baseline mean Spearman: -0.096
- best ML Spearman: 0.116
- ML beats baseline: True

## next_year_outperform_bist100
- baseline mean Spearman: -0.135
- best ML Spearman: 0.254
- ML beats baseline: True

## next_year_return_pct
- baseline mean Spearman: 0.142
- best ML Spearman: 0.218
- ML beats baseline: True

## next_year_top_20pct_returner
- baseline mean Spearman: 0.063
- best ML Spearman: 0.166
- ML beats baseline: True
