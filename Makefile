.PHONY: data data-validate data-benchmark benchmark extract-yearly-financials research full-research \
	inspect-quarterly research-agent-dataset research-agent-check full-research-agent \
	research-agent-dataset-1k research-agent-dataset-5k research-agent-dataset-20k \
	research-agent-dataset-validate research-agent-eval-local research-agent-collect-failures \
	research-agent-autoresearch-iteration

# Diagnose whether new_data_quarter/ files vary per period (they are frozen).
inspect-quarterly:
	PYTHONPATH=. python -m scripts.data_collection.inspect_quarterly_snapshots

# Frozen-column evidence report for the data provider / stakeholders.
frozen-evidence:
	PYTHONPATH=. python -m scripts.data_collection.generate_frozen_column_evidence

# Generate the research-agent instruction dataset (sample + full).
research-agent-dataset:
	PYTHONPATH=. python research_agent_training/generate_instruction_dataset.py

# Sized instruction datasets (AutoResearch preparation; NO training, NO downloads).
research-agent-dataset-1k:
	PYTHONPATH=. python research_agent_training/generate_instruction_dataset.py --n 1000

research-agent-dataset-5k:
	PYTHONPATH=. python research_agent_training/generate_instruction_dataset.py --n 5000

research-agent-dataset-20k:
	PYTHONPATH=. python research_agent_training/generate_instruction_dataset.py --n 20000

# Validate the generated dataset against policy + schema.
research-agent-dataset-validate:
	PYTHONPATH=. python research_agent_training/validate_instruction_dataset.py

# Evaluate the configured local LLM (LM Studio/Ollama) — skips cleanly if none.
research-agent-eval-local:
	PYTHONPATH=. python research_agent_training/evaluate_local_llm.py

# Turn eval failures into a corrective dataset.
research-agent-collect-failures:
	PYTHONPATH=. python research_agent_training/collect_failure_cases.py

# One AutoResearch iteration: generate -> validate -> (eval) -> collect -> report.
research-agent-autoresearch-iteration:
	PYTHONPATH=. python research_agent_training/build_autoresearch_iteration.py --n 1000

# Run the test suite.
research-agent-check:
	PYTHONPATH=. python -m pytest tests/

# Full pipeline + frozen evidence + dataset generation + tests.
full-research-agent:
	$(MAKE) full-research
	$(MAKE) frozen-evidence
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
