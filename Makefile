.PHONY: data data-validate data-benchmark benchmark extract-yearly-financials research full-research \
	inspect-quarterly research-agent-dataset research-agent-check full-research-agent ingest-corrected-yearly \
	prices valuation shares split-datasets build-company-contexts collect-bist100-financials \
	fetch-training-prices integrate-pilot-tickers check-pilot-financials \
	collect-yfinance-bist100 clean-yfinance-bist100 update-training-universe-yfinance validate-universe data-audit \
	research-agent-dataset-1k research-agent-dataset-5k research-agent-dataset-20k \
	research-agent-dataset-validate research-agent-eval-local research-agent-collect-failures \
	research-agent-autoresearch-iteration demo-check

FINANCEIQ_API_URL ?= http://127.0.0.1:8000

# Diagnose whether data/raw/quarterly_fintables/ files vary per period (they are frozen).
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

# Read-only pre-demo check for a running backend. Override with:
#   make demo-check FINANCEIQ_API_URL=http://127.0.0.1:8000
demo-check:
	python scripts/demo_smoke.py --base-url "$(FINANCEIQ_API_URL)"

# Full pipeline + frozen evidence + universe split + contexts + dataset generation + tests.
full-research-agent:
	$(MAKE) full-research
	$(MAKE) frozen-evidence
	$(MAKE) split-datasets
	$(MAKE) build-company-contexts
	$(MAKE) data-audit
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

# Collect BIST100 expansion financials via yfinance (unofficial; requires pip install yfinance).
# Output: data/trusted_raw/financials/bist100_yfinance_candidate.csv
# Cross-check output against KAP (kap.borsaistanbul.com) before trusting for training.
# Training expansion NOT complete until tickers > 40 and return targets added.
collect-bist100-financials:
	PYTHONPATH=. python scripts/data_collection/collect_bist100_financials_yfinance.py

# Collect yfinance financials for ALL candidates in data/config/bist100_candidates.csv.
# Skips tickers already collected (--missing-only). Does NOT run automatically in full-research-agent.
# Run explicitly when you want to expand the training universe.
#   pip install yfinance  (first time only)
collect-yfinance-bist100:
	PYTHONPATH=. python scripts/data_collection/collect_bist100_financials_yfinance.py \
		--candidates-csv data/config/bist100_candidates.csv \
		--missing-only

# Force re-fetch all candidates (ignores existing raw data).
collect-yfinance-bist100-force:
	PYTHONPATH=. python scripts/data_collection/collect_bist100_financials_yfinance.py \
		--candidates-csv data/config/bist100_candidates.csv \
		--force-refresh

# Clean the raw yfinance candidate CSV: drop rows with missing core fields, write clean CSV + report.
# Input:  data/trusted_raw/financials/bist100_yfinance_candidate.csv
# Output: data/trusted_raw/financials/bist100_yfinance_candidate_clean.csv
#         data/trusted_clean/bist100_yfinance_pilot_report.md
clean-yfinance-bist100:
	PYTHONPATH=. python scripts/data_collection/clean_yfinance_candidate.py

# Add yfinance-verified tickers to the training universe config.
# Reads clean candidate CSV, finds tickers with valid rows, appends to universe_training_bist100.csv.
# Does not touch public_40 or already-present tickers.
update-training-universe-yfinance:
	PYTHONPATH=. python scripts/data_collection/update_training_universe_from_yfinance.py

# Print universe counts and coverage for quick validation.
validate-universe:
	PYTHONPATH=. python scripts/data_collection/validate_universe.py

data-audit:
	PYTHONPATH=. python -m scripts.data_collection.audit_pipeline

check-pilot-financials:
	@test -f "data/trusted_raw/financials/bist100_yfinance_candidate_clean.csv" || \
		{ echo ""; \
		  echo "ERROR: Pilot clean financials not found:"; \
		  echo "  data/trusted_raw/financials/bist100_yfinance_candidate_clean.csv"; \
		  echo ""; \
		  echo "Run: make collect-bist100-financials"; \
		  echo "Then verify and save output as bist100_yfinance_candidate_clean.csv"; \
		  echo ""; \
		  exit 1; }

# Fetch Yahoo year-end prices for the full training universe (public_40 + pilot tickers).
# Required before integrate-pilot-tickers.
fetch-training-prices:
	python scripts/fetch_yahoo_chart_prices.py \
		--start-year 2020 --end-year 2025 \
		--universe-csv data/config/universe_training_bist100.csv

# Integrate yfinance pilot financials into the base modeling dataset (training-only rows).
# Prerequisites: make data && make fetch-training-prices
# Run standalone: make fetch-training-prices integrate-pilot-tickers split-datasets build-company-contexts
integrate-pilot-tickers: check-pilot-financials
	PYTHONPATH=. python scripts/data_collection/integrate_pilot_tickers.py

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

# Split modeling_dataset_2020_2025.csv into training and public subsets.
# Requires data/config/universe_*.csv to exist (created in data/config/).
split-datasets:
	PYTHONPATH=. python -m scripts.data_collection.split_universe_datasets

# Build structured RAG context JSON files for all public-universe companies.
# Run after: make data && make split-datasets && python experiments/run_experiments.py
build-company-contexts:
	PYTHONPATH=. python scripts/build_company_contexts.py

# Full pipeline: extract -> benchmark -> corrected yearly -> fetch prices ->
#   valuation -> build -> integrate pilot tickers -> experiments.
# Pilot expansion is preserved: base dataset ends with 81 tickers (40 public + 41 training-only).
full-research:
	$(MAKE) extract-yearly-financials
	$(MAKE) benchmark
	$(MAKE) ingest-corrected-yearly
	$(MAKE) fetch-training-prices
	$(MAKE) valuation
	$(MAKE) data
	$(MAKE) integrate-pilot-tickers
	$(MAKE) data-validate
	PYTHONPATH=. python experiments/run_experiments.py
