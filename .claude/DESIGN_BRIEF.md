# FinanceIQ Shell + Login — Fable 5 Brief

Use the current `/dashboard` visual language as the source of truth.

The dashboard now has a strong "Signal from noise / research terminal" visual system:
- deep ink / graphite background
- subtle grain and scanlines
- muted emerald, antique gold, oxidized copper accents
- dense institutional research instrument feeling
- non-generic terminal-like surfaces
- honest weak-signal language
- research-only tone

Now extend this same visual system to the app shell and login experience.

## Scope

You are working only on:
- left navigation sidebar
- horizontal topbar
- login page

Allowed files:
- 1.frontend/src/components/layout/Sidebar.jsx
- 1.frontend/src/components/layout/Topbar.jsx
- 1.frontend/src/components/layout/AppShell.jsx
- 1.frontend/src/pages/LoginPage.jsx
- 1.frontend/src/pages/DashboardPage.jsx only if a tiny alignment fix is necessary

Do not touch:
- backend
- API clients
- routing unless absolutely necessary
- Forecasting
- Research
- Company Detail
- Research Agent
- Experiments
- Data Quality
- Benchmark
- other pages

## Design goals

Make the whole app feel like one FinanceIQ research terminal.

The sidebar should not feel like a generic SaaS menu.
It should feel like an instrument/channel selector.

The topbar should not feel like a generic admin search bar.
It should feel integrated into the research terminal.

The login page should feel like entering the FinanceIQ research terminal.
It should be cinematic, but still clear and usable.

## Requirements

Sidebar:
- Keep it vertical.
- Preserve existing navigation behavior.
- Preserve active route highlighting.
- Use dashboard-like graphite surfaces, faint borders, muted gold/emerald accents.
- Active item should feel like a selected research channel, not a rounded pill.
- Keep labels readable.
- Preserve icons if already used.
- Keep collapse/logout behavior if present.

Topbar:
- Keep it horizontal.
- Preserve existing search/user/settings behavior.
- Make search field feel like terminal input / research query field.
- Match dashboard visual language.
- Do not overfill with decoration.

Login:
- Preserve all existing auth behavior and form logic.
- Preserve email/password or magic-link flows exactly as currently implemented.
- Make the page feel like entering a research terminal.
- Use subtle noise/scanline/terminal styling.
- Keep form accessible and clear.
- Do not make it hard to read.

## Visual language

Use:
- deep ink / graphite
- muted emerald
- antique gold
- oxidized copper
- subtle grain
- thin instrument-like borders
- monospaced micro-labels
- dense but readable hierarchy
- careful hover/focus states

Avoid:
- neon crypto look
- generic SaaS cards
- random gradients
- huge empty hero
- over-rounded AI-looking components
- childish animation
- investment-advice language

## Technical constraints

Use existing dependencies only.
Do not install packages.
Do not run build.
Do not run lint.
Do not run tests.
Do not run long verification commands.

Preserve existing behavior.
No fake API calls.
No backend changes.
No dead code.
No unused imports.
No TODOs.
No broken exports.

## Copy rules

Allowed:
- research terminal
- research signal
- diagnostic
- weak signal
- historical evaluation
- research only
- not investment advice

Avoid:
- buy
- sell
- hold
- recommendation
- price target
- guaranteed
- alpha promise

## Delivery

Do not ask questions.
Make the changes directly.

Final response:
1. Files changed.
2. What changed visually.
3. How to view.
4. What I should manually verify.
