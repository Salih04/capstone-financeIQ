# unnecessary/

Files moved out of the active project. Nothing here is imported by running code.
Restore with `git mv unnecessary/<file> <original/path>` if needed.

| File | Origin | Why moved |
|---|---|---|
| `generate_data.py` | `2.backend/seed_data/` | Synthetic fundamentals generator. Self-labeled "Deprecated: no longer used". No importers. Produces fabricated financial rows — violates the real-data-only rule. |
| `seed_companies_old_44.py` | `2.backend/scripts/` | Stale `_old_44` backup of `seed_companies.py`. No importers. |
| `seed.py` | `2.backend/` | Old startup seeder. Ran on every container boot (`CMD python seed.py`) and pulled data from xlsx + synthetic sources → the jumbled/incorrect DB. Replaced by `scripts/load_trusted_fundamentals.py`. |
| `import_datasets.py` | `2.backend/scripts/` | Imported `3.Datasets/*.xlsx` into `quarterly_fundamentals`/`financials` — a competing, non-trusted fundamentals source. No importers in `app/`. |
| `seed_companies.py` | `2.backend/scripts/` | Seeded the company universe independently of the trusted CSV. Companies are now derived from the CSV by the loader. |
| `import_kap_html_financials.py` | `2.backend/scripts/` | Scraped financials from KAP HTML — another non-trusted data direction. No importers. |
| `sample_quarterly_fundamentals.csv` | repo root | Old duplicate fundamentals CSV. Not the trusted source. |
| `quarterly_fundamentals_correct.csv` | repo root | Old duplicate fundamentals CSV. Not the trusted source. |
| `quarterly_fundamentals_extended.csv` | repo root | Old duplicate fundamentals CSV. Not the trusted source. |
| `quarterly_fundamentals_fixed.csv` | repo root | Old duplicate fundamentals CSV. Not the trusted source. |

The single trusted source — `quarterly_fundamentals_2025.csv` — was **not** touched and remains in the repo root.
