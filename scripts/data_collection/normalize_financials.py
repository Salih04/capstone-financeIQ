"""Thin CLI: build the per-company-year fundamentals file (year-T features)."""
import sys
from scripts.data_collection import pipeline as P
if __name__ == "__main__":
    P.build_fundamentals(P.PipelineConfig()); sys.exit(0)
