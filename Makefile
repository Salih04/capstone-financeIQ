.PHONY: data data-validate data-benchmark benchmark extract-yearly-financials research full-research \
	inspect-quarterly research-agent-dataset research-agent-check full-research-agent

# Diagnose whether new_data_quarter/ files vary per period (they are frozen).
inspect-quarterly:
	PYTHONPATH=. python -m scripts.data_collection.inspect_quarterly_snapshots

# Generate the research-agent instruction dataset (sample + full).
research-agent-dataset:
	PYTHONPATH=. python research_agent_training/generate_instruction_dataset.py

# Run the test suite.
research-agent-check:
	PYTHONPATH=. python -m pytest tests/

# Full pipeline + dataset generation + tests.
full-research-agent:
	$(MAKE) full-research
	$(MAKE) research-agent-dataset
	PYTHONPATH=. python -m pytest tests/

# Collect BIST100 yearly benchmark returns (Yahoo -> manual CSV -> template).
benchmark:
	PYTHONPATH=. python -m scripts.data_collection.collect_bist100_benchmark

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

# Full pipeline: extract -> benchmark -> build -> experiments.
full-research:
	$(MAKE) extract-yearly-financials
	$(MAKE) benchmark
	$(MAKE) data
	PYTHONPATH=. python experiments/run_experiments.py
