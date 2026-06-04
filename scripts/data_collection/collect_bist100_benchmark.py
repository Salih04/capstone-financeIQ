"""BIST100 benchmark helper.

No reliable free anonymous source is wired (Stooq now requires an API key; we do
not use leaked keys or paid APIs). This emits the manual template and validates a
provided file. Fill data/trusted_clean/bist100_benchmark_returns.csv with REAL
values (year,bist100_return_pct,source,notes). Never fabricated.
"""
import sys
from scripts.data_collection import pipeline as P
if __name__ == "__main__":
    P.ensure_benchmark_template()
    b = P.load_benchmark(P.PipelineConfig())
    print("benchmark present" if b is not None else "benchmark MISSING (fill the template)")
    sys.exit(0)
