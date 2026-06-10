# FinanceIQ — Frontend Rebuild Brief
# For: Claude Opus 4.8 via Claude Code
# Design system prompt: loaded via .claude/skills/

---

## What this is

FinanceIQ is a capstone academic project: an honest, leakage-safe T→T+1
equity-research system for 40 BIST (Borsa Istanbul) companies (2020–2025).
It is NOT a trading platform, NOT investment advice. It is a rigorous research
pipeline with a transparent negative result (no reliable predictive edge at
~40 stocks/year) — and that honesty is a feature, not a weakness.

The frontend is being rebuilt from scratch. The existing React codebase is
functional but visually generic. The goal is to make it look and feel like
a professional, opinionated financial research terminal — Bloomberg meets
a well-designed developer tool.

---

## Audience

Academic capstone jury + international readers (MSc programs, internship
reviewers). They are technical, they respect rigor, and they will notice
if the UI looks like a default Tailwind template.

---

## Visual direction (COMMITTED — do not re-propose)

**Dark terminal. Bloomberg meets Linear.**

- Background: near-black, not pure black. `#0a0a0f` base, `#111118` surfaces.
- Accent: a single cold electric blue — `#2563eb` or tighter `#1d4ed8`. No warm tones.
- Text: high-contrast white `#f8fafc` for primary, `#94a3b8` for secondary, `#475569` for muted.
- Grid lines, table borders, chart axes: `#1e293b` — visible but never loud.
- Monospace for numbers, tickers, scores. `JetBrains Mono` or `IBM Plex Mono`.
- Sans for labels, headings: `Inter` or `DM Sans`.
- Density: high. This is a research tool, not a landing page. Data earns space.
- No gradients on data. No emoji. No rounded hero cards with drop shadows.
- Micro-animations only: state transitions (200ms ease), skeleton loaders, value
  changes (number tick-up on load). Nothing decorative.

---

## Language

**English throughout.** All labels, copy, empty states, tooltips, error messages.
API field names (Turkish tickers like ASELS, THYAO) stay as-is — they are data,
not UI copy.

---

## Pages to build (multi-page full app)

### 1. `/login`
- Minimal. Full-viewport dark. FinanceIQ wordmark + tagline.
- Tagline: "Equity research infrastructure for BIST. Honest signals, no fabrication."
- Single form: email + password. JWT → localStorage on success.
- No sign-up flow needed (capstone, not a product).

### 2. `/dashboard`
- The "nerve center." Shows the state of the entire research system at a glance.
- Key panels:
  - **Dataset status** — 40 tickers, 32 validated features, 2020–2025, walk-forward
    Spearman ≈ 0 (show this honestly — it's a feature of the system)
  - **Research signal** — latest hybrid scores (ML 0.65 + confidence 0.20 + LLM 0.15),
    top 5 and bottom 5 tickers for the most recent year
  - **Data quality badge** — features accepted vs rejected, frozen-snapshot columns
    excluded, leakage guards active
  - **Benchmark comparison** — BIST100 annual return vs top-10 model picks (small chart)
  - **Quick nav** — Research Agent, Forecasting, Companies, Data Health

### 3. `/research-agent`
- The most important page. This is the hybrid research agent.
- Layout: left panel = query/intent selector, right panel = structured result.
- Intents: "Benchmark outperformers", "Top-ranked by ML score", "Data quality overview",
  "Valuation screen", "Model diagnostics"
- Result panel shows:
  - Hybrid score breakdown (3 bars: ML / Confidence / LLM) — always decomposed
  - Decision-support verdict (never "buy/sell/hold" — use "Strong signal / Weak signal /
    Insufficient data")
  - Top features driving the score (ranked, with effect sizes)
  - Data quality warnings inline
  - "Not investment advice" disclaimer — small, always present, never intrusive

### 4. `/forecasting`
- CSV-backed pipeline (no DB required — reads modeling_dataset_public_2020_2025.csv).
- 3-step flow with clear state:
  - **Step 1: Configure training window** — year range selector, top_n parameter
  - **Step 2: Review feature weights** — horizontal bar chart of top parameters
    with weights. This is the "what the model learned" view.
  - **Step 3: Run forecast** — ranked ticker table for selected year. Score, confidence,
    top driving features per ticker. Click row → explainability panel slides in.
- Inference rows (2025) clearly flagged: "Inference only — no return target available"
- No buy/sell signals anywhere on this page.

### 5. `/companies`
- Searchable, filterable table of the 40-ticker public universe.
- Columns: Ticker, Sector, Latest Score, Score Trend (sparkline), Data Coverage %, BIST100 member
- Click row → `/companies/:ticker` detail page
- Detail page: financial metrics timeline (the 32 features), score history, feature
  contribution breakdown, data quality per field.

### 6. `/data-health`
- The "honesty page." Shows what the pipeline accepted, rejected, and why.
- Sections:
  - Feature registry: 32 accepted features, categorized (balance-sheet, growth,
    income/profitability, valuation), with source and year coverage
  - Rejected columns: frozen-snapshot list, leakage-rejected list — shown explicitly
  - Walk-forward results: Spearman per year, vs equal-weight baseline (honest chart,
    not hidden)
  - Data provenance: corrected yearly files, free valuation reconstruction, 2024
    balance-sheet correction

---

## API contract (existing backend — do not change)

The backend is FastAPI on `:8000`. These are the live endpoints to wire up:

```
GET  /forecasting/options          → trainable_years, feature_columns, ticker_count
POST /forecasting/train            → top_parameters [{name, weight, rank}]
POST /forecasting/run              → ranked items [{ticker, score, confidence, top_parameters}]
GET  /forecasting/explain/{ticker} → top_features, bottom_features, missing_features

GET  /research/summary             → dataset overview
GET  /research/company/{ticker}    → per-ticker research data
GET  /research/company/{ticker}/score → hybrid score breakdown
GET  /research/model-diagnostics   → walk-forward results
GET  /research/data-quality        → feature registry + rejected columns
POST /research/ask                 → {intent, ticker?, year?} → research response

GET  /companies                    → company list
GET  /companies/{id}               → company detail

POST /auth/login                   → {access_token}
```

Base URL from env: `VITE_API_URL` (default `http://localhost:8000`).

---

## Component system to establish first

Before any page, establish these tokens and components. Run `design-system-extract`
then `frontend-aesthetic-direction` to commit the system.

**Tokens needed:**
- Color scale (bg, surface, border, text-primary, text-secondary, text-muted, accent, accent-hover, positive, negative, warning)
- Type scale (mono-xs through mono-lg, sans-sm through sans-xl)
- Spacing scale (4px base)
- Border radius (2px only — this is a terminal, not a consumer app)

**Core components:**
- `<MetricCard>` — label + value + optional delta + optional sparkline
- `<ScoreBar>` — labeled horizontal bar, 0–100, with segment breakdown
- `<TickerTable>` — sortable, with inline sparklines and score chips
- `<FeatureWeight>` — horizontal bar for ML feature importance
- `<DataQualityBadge>` — accepted/rejected/warning with count
- `<ExplainPanel>` — slide-in from right, top/bottom features
- `<StepFlow>` — 3-step wizard with state (idle / loading / complete / error)
- `<HonestyBanner>` — "Research only. Not investment advice." — persistent, unobtrusive

---

## Skill chain to run (in order)

1. `frontend-aesthetic-direction` — commit the token system (do NOT re-propose directions; dark terminal is committed above, use this skill to formalize the token file)
2. `make-a-prototype` — build the full multi-page app with real navigation, loading states, and API wiring
3. `ai-slop-check` — this is critical; no gradients, no rounded hero cards, no generic AI aesthetics
4. `interaction-states-pass` — every button, every row, every input needs hover/focus/active/disabled
5. `polish-pass` — final gate before delivery

---

## What NOT to do

- No hero sections with large illustrations
- No "Why choose FinanceIQ?" marketing copy
- No donut charts for portfolio allocation
- No confetti or success animations
- No fake data — if the API isn't connected, show skeleton loaders and "—" values
- No fabricated tickers or scores in placeholder content
- Never present scores as investment recommendations
- Never hide the negative result (Spearman ≈ 0) — it's the honest finding; display it

---

## The one design principle for this project

**Confidence through restraint.** Every pixel that isn't earning its place is
undermining the credibility of the research. A capstone jury trusts a tool that
shows its limitations more than one that oversells its results. The UI should feel
like it was built by someone who understood the data deeply, not someone who
styled a dashboard template.