# Graph Report - /Users/salihcamci/Desktop/CAPSTONE/Capstone_Code  (2026-05-01)

## Corpus Check
- 196 files · ~80,256 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 668 nodes · 1146 edges · 27 communities detected
- Extraction: 68% EXTRACTED · 32% INFERRED · 0% AMBIGUOUS · INFERRED: 370 edges (avg confidence: 0.59)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 11|Community 11]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 17|Community 17]]
- [[_COMMUNITY_Community 18|Community 18]]
- [[_COMMUNITY_Community 19|Community 19]]
- [[_COMMUNITY_Community 20|Community 20]]
- [[_COMMUNITY_Community 21|Community 21]]
- [[_COMMUNITY_Community 23|Community 23]]
- [[_COMMUNITY_Community 24|Community 24]]
- [[_COMMUNITY_Community 25|Community 25]]
- [[_COMMUNITY_Community 26|Community 26]]
- [[_COMMUNITY_Community 27|Community 27]]
- [[_COMMUNITY_Community 28|Community 28]]
- [[_COMMUNITY_Community 29|Community 29]]

## God Nodes (most connected - your core abstractions)
1. `Base` - 40 edges
2. `ComputedMetric` - 38 edges
3. `Company` - 30 edges
4. `ScoringModel` - 19 edges
5. `LabelDefinition` - 18 edges
6. `User` - 16 edges
7. `SectorNormalizedFeature` - 16 edges
8. `Returns the intersection of available periods for the given company IDs.     Use` - 15 edges
9. `Score multiple companies with the same model and return ranked results.` - 15 edges
10. `FinancialStatement` - 15 edges

## Surprising Connections (you probably didn't know these)
- `Hotfix for existing DBs created before new onboarding fields.     We still keep` --uses--> `Base`  [INFERRED]
  2.backend/app/main.py → 2.backend/app/database.py
- `Ingestion Observability – V3 ============================ Tables: IngestionJob,` --uses--> `Base`  [INFERRED]
  2.backend/app/models/ingestion.py → 2.backend/app/database.py
- `Tracks a single batch data-ingestion run.` --uses--> `Base`  [INFERRED]
  2.backend/app/models/ingestion.py → 2.backend/app/database.py
- `Records a specific data-quality problem found during ingestion or normalization.` --uses--> `Base`  [INFERRED]
  2.backend/app/models/ingestion.py → 2.backend/app/database.py
- `Audit Log – V3 ============== Immutable record of every state-changing action in` --uses--> `Base`  [INFERRED]
  2.backend/app/models/audit.py → 2.backend/app/database.py

## Communities

### Community 0 - "Community 0"
Cohesion: 0.0
Nodes (94): Capstone Codebase, AEFES 3b169122, AEFES 9981dbcf, AKSA 58994b2b, AKSA 9f707062, AKSEN 214c8522, AKSEN 5ce63db7, ASELS 176e210d (+86 more)

### Community 1 - "Community 1"
Cohesion: 0.0
Nodes (64): Base, Base, DeclarativeBase, ForecastEvaluationFold, ForecastEvaluationRun, ForecastPrediction, ForecastRun, QuarterlyFundamental (+56 more)

### Community 2 - "Community 2"
Cohesion: 0.0
Nodes (63): BaseModel, common_periods(), compare_stocks(), Returns the intersection of available periods for the given company IDs.     Use, Score multiple companies with the same model and return ranked results., CompanyCreate, CompanyOut, ComputedMetricOut (+55 more)

### Community 3 - "Community 3"
Cohesion: 0.0
Nodes (51): Seed script – populates companies table and imports financial data. Run: python, Return 4 quarterly financial-data dicts for seed insertion (2023Q1–Q4)., seed(), _syn_financial_rows(), ComputedMetric, FinancialStatement, LabelDefinition, ModelValidationRun (+43 more)

### Community 4 - "Community 4"
Cohesion: 0.0
Nodes (39): AuditLog, Audit Log – V3 ============== Immutable record of every state-changing action in, ScoringModel, ScoringModelMetric, User, activate_scoring_model(), archive_scoring_model(), create_scoring_model() (+31 more)

### Community 5 - "Community 5"
Cohesion: 0.0
Nodes (13): Navbar(), ProtectedRoute(), getBand(), ScoreBadge(), useAuth(), Sidebar(), Topbar(), DashboardPage() (+5 more)

### Community 6 - "Community 6"
Cohesion: 0.0
Nodes (31): Company, ScoreRun, export_csv(), export_json(), export_pdf(), _get_run(), routers/reports.py ─────────────────── Export score runs as CSV, JSON, or PDF., main() (+23 more)

### Community 7 - "Community 7"
Cohesion: 0.0
Nodes (28): search_companies(), get_kap_ratios(), upload_fundamentals_csv(), _parse_period(), _to_float(), upload_quarterly_fundamentals_csv(), _compute_ratios(), _extract_company_year_inputs() (+20 more)

### Community 8 - "Community 8"
Cohesion: 0.0
Nodes (30): MetricTransition, Stores sector-wide distribution statistics per metric per period., Per-company, per-period z-score and percentile for each feature., SectorBenchmark, SectorNormalizedFeature, _compute_ratios_from_qf(), main(), _safe_div() (+22 more)

### Community 9 - "Community 9"
Cohesion: 0.0
Nodes (10): _get_sector_z_scores(), score_company(), _to_dict(), build_rich_explanations(), _l2_sentence(), _l3_counterfactual(), Explainability Service – V3 (3-Level) ====================================== Lev, Generate a counterfactual hint: 'if this metric were X better, the score     wou (+2 more)

### Community 10 - "Community 10"
Cohesion: 0.0
Nodes (7): get_current_user(), create_access_token(), decode_token(), hash_password(), verify_password(), login(), register()

### Community 11 - "Community 11"
Cohesion: 0.0
Nodes (9): detect_multiplier(), detect_ticker(), find_periods(), main(), normalize(), parse_file(), parse_number(), upsert_company() (+1 more)

### Community 12 - "Community 12"
Cohesion: 0.0
Nodes (3): ForecastingApiContractTests, _register_and_login(), setUpClass()

### Community 13 - "Community 13"
Cohesion: 0.0
Nodes (6): build_row(), r(), Run this script to regenerate financial_data.csv with multi-year, multi-company, Scale 2023Q4 revenue to a given year's Q4 baseline., base = dict with 2023Q4 financials.     Scale everything proportionally to reven, scale_year()

### Community 15 - "Community 15"
Cohesion: 0.0
Nodes (1): ErrorBoundary

### Community 17 - "Community 17"
Cohesion: 0.0
Nodes (2): parseAISectors(), SearchPage()

### Community 18 - "Community 18"
Cohesion: 0.0
Nodes (2): CompanyPage(), fmt()

### Community 19 - "Community 19"
Cohesion: 0.0
Nodes (2): _ensure_backward_compatible_columns(), Hotfix for existing DBs created before new onboarding fields.     We still keep

### Community 20 - "Community 20"
Cohesion: 0.0
Nodes (4): clean_columns(), main(), parse_period(), to_float()

### Community 21 - "Community 21"
Cohesion: 0.0
Nodes (2): ModelCard(), statusChipStyle()

### Community 23 - "Community 23"
Cohesion: 0.0
Nodes (3): Config, Settings, BaseSettings

### Community 24 - "Community 24"
Cohesion: 0.0
Nodes (3): _db_url(), run_migrations_offline(), run_migrations_online()

### Community 25 - "Community 25"
Cohesion: 0.0
Nodes (1): add forecasting tables  Revision ID: 20260406_0001 Revises: Create Date: 2026-04

### Community 26 - "Community 26"
Cohesion: 0.0
Nodes (1): add quarterly fundamentals table  Revision ID: 20260406_0004 Revises: 20260406_0

### Community 27 - "Community 27"
Cohesion: 0.0
Nodes (1): add forecast evaluation tables  Revision ID: 20260406_0002 Revises: 20260406_000

### Community 28 - "Community 28"
Cohesion: 0.0
Nodes (1): add user onboarding fields  Revision ID: 20260406_0003 Revises: 20260406_0002 Cr

### Community 29 - "Community 29"
Cohesion: 0.0
Nodes (1): add performance indexes  Revision ID: 20260406_0005 Revises: 20260406_0004 Creat

## Knowledge Gaps
- **14 isolated node(s):** `Config`, `V3 Governance, Validation, Labeling, Ingestion & Audit Schemas`, `Explainability Service – V3 (3-Level) ====================================== Lev`, `Generate a single Turkish human-readable explanation sentence.`, `Generate a counterfactual hint: 'if this metric were X better, the score     wou` (+9 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Community 15`** (5 nodes): `main.jsx`, `ErrorBoundary`, `.constructor()`, `.getDerivedStateFromError()`, `.render()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 17`** (5 nodes): `SearchPage.jsx`, `CompanyCard()`, `CompanyRow()`, `parseAISectors()`, `SearchPage()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 18`** (5 nodes): `CompanyPage.jsx`, `CompanyPage()`, `fmt()`, `generateQuarters()`, `MetricCardGroup()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 19`** (5 nodes): `main.py`, `_ensure_backward_compatible_columns()`, `fundamentals_template()`, `health()`, `Hotfix for existing DBs created before new onboarding fields.     We still keep`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 21`** (4 nodes): `AdminPage.jsx`, `AdminPage()`, `ModelCard()`, `statusChipStyle()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 25`** (4 nodes): `20260406_0001_add_forecasting_tables.py`, `downgrade()`, `add forecasting tables  Revision ID: 20260406_0001 Revises: Create Date: 2026-04`, `upgrade()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 26`** (4 nodes): `20260406_0004_add_quarterly_fundamentals_table.py`, `downgrade()`, `add quarterly fundamentals table  Revision ID: 20260406_0004 Revises: 20260406_0`, `upgrade()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 27`** (4 nodes): `20260406_0002_add_forecast_evaluation_tables.py`, `downgrade()`, `add forecast evaluation tables  Revision ID: 20260406_0002 Revises: 20260406_000`, `upgrade()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 28`** (4 nodes): `20260406_0003_add_user_onboarding_fields.py`, `downgrade()`, `add user onboarding fields  Revision ID: 20260406_0003 Revises: 20260406_0002 Cr`, `upgrade()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 29`** (4 nodes): `20260406_0005_add_performance_indexes.py`, `downgrade()`, `add performance indexes  Revision ID: 20260406_0005 Revises: 20260406_0004 Creat`, `upgrade()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.