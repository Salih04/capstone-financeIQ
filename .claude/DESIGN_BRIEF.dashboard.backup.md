# FinanceIQ Dashboard — Fable 5 Brief

Single page only. Everything else is handled separately.

Spend creativity on the visual system, not on touching many files.

You are working on ONE screen only: the FinanceIQ dashboard at /dashboard.

Do not redesign the whole app.
Do not touch login.
Do not touch backend/API wiring.
Do not touch Forecasting, Research, Company Detail, Research Agent, Experiments, or Data Quality pages.
Do not install new dependencies.
Do not run build, lint, tests, or any long verification commands.
I will verify manually.

Build the dashboard as a self-contained React component that can later be adapted into the real app.

---

## Context

FinanceIQ is a T→T+1 equity research system for 40 selected BIST stocks from 2020–2025.

The honest finding:
Walk-forward Spearman / IC is approximately 0.
There is no reliable predictive edge.

This is not a failure. This is the core story.

The dashboard must make the weak signal visible instead of hiding it.

This is research support only.
It is not investment advice.

---

## Data

For this screen only, use this realistic mock data.
API wiring comes later.

Do not invent extra fields unless they are purely visual and clearly derived from the mock data.

js const MOCK = {   dataset: {     tickers: 40,     features: 32,     years: [2020, 2021, 2022, 2023, 2024, 2025],     inferenceYear: 2025   },   benchmark: [     { year: 2020, bist100: 28.4, model_top10: 31.2, spearman: 0.08 },     { year: 2021, bist100: 19.1, model_top10: 14.7, spearman: -0.11 },     { year: 2022, bist100: 196.3, model_top10: 188.9, spearman: -0.14 },     { year: 2023, bist100: 43.8, model_top10: 51.2, spearman: 0.03 },     { year: 2024, bist100: 31.2, model_top10: 38.7, spearman: 0.12 }   ],   topTickers: [     { ticker: "ASELS", score: 78.4, ml: 0.81, confidence: 0.74, coverage: 0.94 },     { ticker: "THYAO", score: 71.2, ml: 0.68, confidence: 0.79, coverage: 0.97 },     { ticker: "EREGL", score: 69.8, ml: 0.72, confidence: 0.65, coverage: 0.89 },     { ticker: "SISE",  score: 65.1, ml: 0.61, confidence: 0.71, coverage: 0.92 },     { ticker: "KCHOL", score: 61.4, ml: 0.58, confidence: 0.68, coverage: 0.78 }   ],   bottomTickers: [     { ticker: "TTKOM", score: 28.1, ml: 0.24, confidence: 0.31, coverage: 0.61 },     { ticker: "DOHOL", score: 24.7, ml: 0.21, confidence: 0.28, coverage: 0.44 },     { ticker: "SMRTG", score: 19.3, ml: 0.17, confidence: 0.22, coverage: 0.38 }   ],   dataQuality: {     accepted: 32,     rejected: 15,     leakageGuarded: 8,     frozenExcluded: 7   } } 

---

## Creative direction

This dashboard should feel like nothing else.

Not Bloomberg.
Not Linear.
Not a generic SaaS dashboard.
Not a crypto terminal.
Not an admin panel.

It should feel like a cinematic institutional research instrument.

Break conventions, but preserve meaning.

Pick one direction and go all the way:

### A — Particle field

40 stocks as nodes on a canvas.

- X = ML score
- Y = confidence
- Size = data coverage
- Color = score / return signal
- Year control changes the field
- Nodes animate between states
- Hovering a node reveals detail in a dedicated panel
- The Spearman ≈ 0 result appears as a signal-strength indicator that never fully stabilizes

### B — Geological strata

Each year is a horizontal data stratum.

- 2025 at top, 2020 at bottom
- Scroll means moving through time
- Tickers sit inside each layer by score
- Outperformance emits upward glow into the next layer
- The random glow pattern visually explains why IC ≈ 0

### C — Signal emerging from noise

The page begins as static/noise.

- Data crystallizes from noise as it loads
- High-confidence tickers become crisp
- Low-coverage tickers remain grainy
- The Spearman chart never fully resolves
- The dashboard feels like tuning a weak research signal from market noise

Direction preference: C (Signal from noise) is the strongest fit 
for a system that honestly reports weak signal. But if you see 
something better, override this.

### Or your own direction

If you see a stronger idea, name it in one sentence and build it.

---

## Required content

The dashboard must show:

1. Dataset summary:
   - 40 BIST stocks
   - 32 accepted features
   - 2020–2025
   - 2025 inference-only

2. BIST100 vs Model Top 10 return comparison for 2020–2024

3. Spearman / walk-forward IC per year

4. Top 5 tickers by research score

5. Bottom 3 tickers by research score

6. Data quality:
   - 32 accepted
   - 15 rejected
   - 8 leakage guarded
   - 7 frozen excluded

7. Always-visible caveat:
   “Research only · Not investment advice”

8. Clear statement:
   “Walk-forward IC ≈ 0: weak predictive signal”

---

## Interaction requirements

The screen must be interactive.

Required:
- Hovering a ticker/node/stratum updates a dedicated detail panel.
- No floating tooltips.
- Detail must appear in a fixed panel, morphing panel, or dedicated overlay.
- Hover, active, and focus states for interactive elements.
- A year selector or time interaction if it fits the chosen direction.
- Loading-style entrance animation even though mock data is local.

Do not use interaction only for decoration.
Interaction should help the user understand weak signal, confidence, coverage, and research score.

---

## Visual requirements

Use a bold, non-generic visual system.

Acceptable ingredients:
- canvas-like field
- asymmetric layout
- deep ink / graphite background
- muted emerald / antique gold / oxidized copper accents
- subtle grain/noise
- scanlines
- custom SVG shapes
- unusual panels
- non-grid placement
- animated transitions
- dense data surfaces

Avoid:
- card grid dashboard
- generic KPI cards
- fake decorative charts
- random gradients
- neon crypto aesthetic
- huge empty hero
- investment-advice language
- buy/sell/hold wording
- price targets

---

## Technical requirements

Use React.

Use existing dependencies if available.
Recharts is acceptable if already installed.
SVG/CSS/canvas are acceptable.

Do not install packages.
Do not run build.
Do not run lint.
Do not run tests.
Do not run expensive verification.
Do not modify unrelated files.

No fake API calls.
No backend changes.
No unrelated pages.
No dead code.
No unused imports.
No TODOs.
No broken exports.

The component must be easy to move into the real dashboard route later.

Prefer:
- one main component file,
- local helper components inside the same file if needed,
- colocated CSS only if the current project already supports it.

If the repo already has a dashboard file, replace only that dashboard implementation.
If not, create a clear standalone component file and tell me where it belongs.

---

## Copy rules

Use careful research language.

Allowed:
- research signal
- diagnostic score
- ranking signal
- weak signal
- inference-only
- historical evaluation
- not investment advice
- no reliable predictive edge

Avoid:
- buy
- sell
- hold
- recommendation
- price target
- guaranteed
- alpha promise

---

## Delivery

Do not ask questions.
Make a decision and build.

Final response:
1. Direction chosen and why, in one sentence.
2. Files changed.
3. How to view the screen.
4. Anything I should manually verify.