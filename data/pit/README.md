# Point-in-time reference data

Inputs of the PIT-v2 evaluation ([`docs/PIT_PROTOCOL.md`](../../docs/PIT_PROTOCOL.md)).

| File | Content |
| --- | --- |
| `feature_availability_registry.json` | Machine-readable availability record for every model feature; read by `experiments/pit/guard.py` |
| `reporting_deadlines.csv` | Statutory annual-report deadlines per fiscal year (and ticker-specific extensions), with the MKK letter or rule they come from and the SHA-256 of the retrieved letter where one was read |
| `filing_dates_sample.csv` | Manually verified public dates of sampled annual reports (press reports dated the evening or morning after the KAP filing). The only input of `ACTUAL_FILING_DATE` mode |
| `yahoo_daily_provenance.csv` | URL, access time, SHA-256 and size of each raw Yahoo Chart API response. The raw bytes are `PRIVATE_LOCAL_RAW` and are not committed |
| `derived/listing_and_events.csv` | First quote, Yahoo split events and unexplained one-day jumps per ticker |
| `derived/price_panel_<cutoff>.csv` | Per ticker and fiscal year: cutoff, prediction date, target window and return, PIT price features, PIT market value and every exclusion reason |

Rebuild (needs network for the first step):

```bash
python scripts/data_collection/fetch_yahoo_daily_history.py --end 2026-10-03
PYTHONPATH=. python -m experiments.pit.prices
```

Yahoo revises `adjclose` when later dividends are paid, so a fresh fetch can
differ slightly from the committed derived tables; the committed tables are
the inputs of the registered run.
