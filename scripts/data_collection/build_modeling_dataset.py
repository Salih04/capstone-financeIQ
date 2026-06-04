"""Thin CLI: build only the modeling dataset (delegates to pipeline)."""
import sys
from scripts.data_collection import pipeline as P
if __name__ == "__main__":
    cfg = P.PipelineConfig()
    P.build_modeling_dataset(cfg)
    sys.exit(0)
