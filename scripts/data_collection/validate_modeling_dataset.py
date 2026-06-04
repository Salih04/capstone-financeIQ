"""Thin CLI: validate the existing modeling dataset."""
import sys
import pandas as pd
from scripts.data_collection import pipeline as P, validate as V
if __name__ == "__main__":
    if not P.MODELING_CSV.is_file():
        print("modeling dataset missing; run build_all first"); sys.exit(1)
    rep = V.validate(pd.read_csv(P.MODELING_CSV), P.PipelineConfig())
    sys.exit(0 if rep["valid_for_T_to_T1_modeling"] else 2)
