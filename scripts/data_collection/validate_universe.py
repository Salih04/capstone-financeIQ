import pandas as pd

base = pd.read_csv("data/trusted_clean/modeling_dataset_2020_2025.csv")
train = pd.read_csv("data/trusted_clean/modeling_dataset_training_2020_2025.csv")
public = pd.read_csv("data/trusted_clean/modeling_dataset_public_2020_2025.csv")

public_tickers = set(public["ticker"].astype(str))
train_tickers = set(train["ticker"].astype(str))
base_tickers = set(base["ticker"].astype(str))
training_only = sorted(train_tickers - public_tickers)

print("Base rows:", len(base), "| tickers:", len(base_tickers))
print("Training rows:", len(train), "| tickers:", len(train_tickers))
print("Public rows:", len(public), "| tickers:", len(public_tickers))
print("Training-only:", len(training_only), training_only)
print()
print("Training year coverage:")
print(train.groupby("year")["ticker"].nunique())

assert len(public_tickers) == 40, "public universe must remain exactly 40 tickers"
assert len(train_tickers) >= 49, "training universe should be at least 49 tickers"
assert public_tickers.issubset(train_tickers), "public tickers must be included in training"
assert len(training_only) >= 9, "training-only expansion should contain at least the 9 pilot tickers"

print("ALL OK")
