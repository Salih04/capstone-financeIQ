.PHONY: data data-validate data-benchmark

# Build the T->T+1 modeling dataset + validation report.
data:
	cd 2.backend >/dev/null 2>&1 || true; \
	PYTHONPATH=. python -m scripts.data_collection.build_all

# Re-run validation only on the existing modeling dataset.
data-validate:
	PYTHONPATH=. python -m scripts.data_collection.build_all --validate-only

# Emit/validate the manual BIST100 benchmark file.
data-benchmark:
	PYTHONPATH=. python -m scripts.data_collection.collect_bist100_benchmark
