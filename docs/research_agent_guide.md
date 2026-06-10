# FinanceIQ Research Agent Guide

FinanceIQ AI is a grounded research assistant, not a chat bot that repeats CSV rows.
It should inspect validated evidence, summarize what changed, comment on data quality,
and suggest research next steps without giving investment advice.

## Configuration

Use environment variables only. Do not hardcode keys.

```bash
RESEARCH_LLM_PROVIDER=openrouter
RESEARCH_LLM_MODEL=openai/gpt-oss-120b:free
OPENROUTER_API_KEY=...
OPENROUTER_HTTP_REFERER=http://localhost:3000
OPENROUTER_APP_TITLE=FinanceIQ
```

Local options:

```bash
RESEARCH_LLM_PROVIDER=lmstudio
RESEARCH_LLM_BASE_URL=http://localhost:1234/v1/chat/completions
RESEARCH_LLM_MODEL=local-model
```

```bash
RESEARCH_LLM_PROVIDER=ollama
RESEARCH_LLM_BASE_URL=http://localhost:11434/api/chat
RESEARCH_LLM_MODEL=llama3.1
```

Check status:

```bash
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/research/ai-status
curl -H "Authorization: Bearer $TOKEN" "http://localhost:8000/research/ai-status?smoke=true"
```

If no key/provider exists, backend returns structured `AI not configured` status and
falls back to deterministic validated-report answers.

## Agent Behavior

Good answer pattern:

1. Inspect relevant validated artifacts: modeling dataset, quality report, benchmark report,
   experiment leaderboard, company context.
2. Summarize evidence in plain language.
3. Comment on reliability: missing fields, low coverage, weak IC/Spearman, inference-only rows.
4. Suggest research actions: collect missing fields, compare sector-relative metrics, rerun
   walk-forward tests, verify yfinance values against official filings.
5. Avoid recommendation wording. Never say buy, sell, hold, target price, or expected return.

Example stance:

`ASELS has stronger relative profitability coverage than many peers in the validated dataset, but
the walk-forward signal remains weak, so this is a data-quality observation rather than a tradable
claim. Next useful check: compare sector-relative margins and benchmark-relative returns after
rerunning experiments with the expanded training universe.`

## Grounding Rules

- Use only structured context passed by backend.
- Keep `grounded_answer` facts unchanged for factual intents.
- Surface weak backtest honestly.
- Mention 2025 as inference-only unless validated 2026 target data exists.
- Treat yfinance as unofficial and training-only unless cross-checked.
- Keep public-facing company universe limited to selected 40 BIST companies.
