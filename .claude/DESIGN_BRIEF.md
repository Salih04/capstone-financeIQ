# FinanceIQ Page Redesign — Design System Brief

Use the current implemented FinanceIQ visual language as the source of truth.

Read these files first:
- 1.frontend/src/pages/DashboardPage.jsx
- 1.frontend/src/components/layout/Sidebar.jsx
- 1.frontend/src/components/layout/Topbar.jsx
- 1.frontend/src/pages/LoginPage.jsx
- 1.frontend/index.html

The app now has a strong “Signal from noise / research terminal” visual system:
- deep ink / graphite background
- subtle grain and scanlines
- muted emerald, antique gold, oxidized copper accents
- sharp instrument-like panels
- thin hairline borders
- monospaced micro-labels
- dense institutional research terminal feeling
- honest weak-signal language
- research-only tone

Completed Fable 5 page concepts:
- `/dashboard` — particle field / weak signal overview; "A weak signal, reported honestly."
- `/research-agent` — query instrument; "Query the signal. Distrust the answer."; five intent selectors and custom free-text query using `POST /research/ask`
- `/research/companies` and `/companies` — research map; "The universe, laid flat."; research score × coverage, sector-colored nodes, dimming filters, map/table toggle
- `/experiments` — seismograph; walk-forward traces around zero and flat IC as the finding
- `/research` — Score Explorer dissection table; composite score unfolds into feature/category detail
- `/data-quality` — specimen archive; accepted/rejected features with `LEAKAGE`, `FROZEN`, and `ALL-NULL` stamps
- `/benchmark` — tide chart; BIST100 vs model water bodies, 2022 +196% sign-preserving log scale, small IC markers
- `/forecasting` — experimental signal tuner; options/train/run/explain preserved, feature weights as spectrum, inference-only rows pulse amber

Mock/demo data is fallback only where implemented; preserve real API calls. Keep
walk-forward IC ≈ 0 visible when relevant.

Your job is to redesign ONE requested page at a time so it feels like part of the same FinanceIQ research terminal.

## Scope

Only edit the page explicitly requested in the user prompt.

Allowed by default:
- the requested page file only

Do not edit:
- backend
- API clients
- routing
- DashboardPage.jsx
- Sidebar.jsx
- Topbar.jsx
- AppShell.jsx
- LoginPage.jsx
- other pages

Only touch shared shell/global files if the user explicitly allows it.

## Design goals

Make the requested page feel like the same FinanceIQ research terminal.

The page should not feel like:
- generic SaaS
- admin template
- crypto dashboard
- random card grid
- AI-generated UI

It should feel like:
- an institutional research instrument
- a diagnostic terminal
- a calibrated data surface
- a serious weak-signal research tool

## Visual language

Use:
- deep ink / graphite surfaces
- muted emerald
- antique gold
- oxidized copper
- subtle grain
- scanline-like texture where appropriate
- thin instrument borders
- monospaced labels
- compact hierarchy
- careful hover/focus states
- dense but readable data layout

Avoid:
- neon colors
- random gradients
- huge empty hero sections
- over-rounded generic cards
- childish animations
- fake decorative charts
- investment-advice language
- price-target or guaranteed-return language

## Technical constraints

Use existing dependencies only.
Do not install packages.
Do not run build.
Do not run lint.
Do not run tests.
Do not run long verification commands.

Preserve existing behavior.
Preserve existing API calls.
Preserve existing user flows.
Preserve existing route behavior.
Do not introduce fake API calls.
Do not replace real data with mock data.
No backend changes.
No dead code.
No unused imports.
No TODOs.
No broken exports.

## Data and behavior rules

If the page already fetches real data, keep that data flow.
If the page has forms, preserve form logic.
If the page has loading/error/empty states, preserve them and redesign them.
If the page has buttons or actions, preserve their behavior.
If the page exposes public stocks, keep the public universe limited to the selected 40 BIST companies.

## Copy rules

Use careful research language.

Allowed:
- research terminal
- research signal
- diagnostic score
- weak signal
- historical evaluation
- inference-only
- model evidence
- not investment advice
- no reliable predictive edge

Avoid:
- trading action verbs
- target-price claims
- guaranteed
- unearned edge promises

## Delivery

Do not ask questions.
Make a decision and build only the requested page.

Final response:
1. Files changed.
2. What changed visually.
3. How to view.
4. What I should manually verify.
