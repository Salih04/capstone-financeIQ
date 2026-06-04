.PHONY: data data-validate data-benchmark extract-yearly-financials research full-research

# Extract candidate financial features from the yearly stock Excel files into a
# manual-ingestion candidate file (validated, never auto-trusted).
extract-yearly-financials:
	PYTHONPATH=. python -m scripts.data_collection.extract_yearly_snapshots_to_manual_financials --validate --strict

# Build the T->T+1 modeling dataset + validation report.
# Runs from the repo root so `scripts.data_collection` resolves correctly.
data:
	PYTHONPATH=. python -m scripts.data_collection.build_all

# Re-run validation only on the existing modeling dataset.
data-validate:
	PYTHONPATH=. python -m scripts.data_collection.build_all --validate-only

# Emit/validate the manual BIST100 benchmark file.
data-benchmark:
	PYTHONPATH=. python -m scripts.data_collection.collect_bist100_benchmark

# Run the walk-forward experiment loop.
research:
	PYTHONPATH=. python experiments/run_experiments.py

# Full pipeline: extract -> build -> experiments.
full-research:
	$(MAKE) extract-yearly-financials
	$(MAKE) data
	PYTHONPATH=. python experiments/run_experiments.py
