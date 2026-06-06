.PHONY: data data-validate data-benchmark benchmark extract-yearly-financials research full-research \
	inspect-quarterly research-agent-dataset research-agent-check full-research-agent ingest-corrected-yearly \
	prices valuation shares \
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

# Ingest the CORRECTED yearly XLSX files (real per-year income/profitability).
# Writes a validated candidate into data/trusted_raw/financials/ so build_all
# picks it up; valuation stays frozen-rejected, 2024 misalignment rejected.
ingest-corrected-yearly:
	PYTHONPATH=. python -m scripts.data_collection.ingest_corrected_yearly_financials

# Collect free year-end prices from Yahoo (TICKER.IS) and cache them. No shares.
prices:
	PYTHONPATH=. python -m scripts.data_collection.build_free_valuation_history --prices-only

# Expand capital-EVENT rows into per-ticker-year shares outstanding (carry-forward).
# Generates an events template if missing; never crashes.
shares:
	PYTHONPATH=. python -m scripts.data_collection.expand_shares_outstanding_events

# Build free-data valuation candidate (market_cap/pe/pb/ev/ev_ebitda) from
# Yahoo prices + manual shares + validated financials. Generates a shares
# template and reports honestly if shares are missing (never crashes).
valuation:
	$(MAKE) shares
	PYTHONPATH=. python -m scripts.data_collection.build_free_valuation_history

# Build the T->T+1 modeling dataset + validation report.
# Runs from the repo root so `scripts.data_collection` resolves correctly.
data:
	$(MAKE) ingest-corrected-yearly
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

# Full pipeline: extract -> benchmark -> corrected yearly -> valuation -> build -> experiments.
full-research:
	$(MAKE) extract-yearly-financials
	$(MAKE) benchmark
	$(MAKE) ingest-corrected-yearly
	$(MAKE) valuation
	$(MAKE) data
	PYTHONPATH=. python experiments/run_experiments.py
