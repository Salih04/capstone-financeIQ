# Research-agent prompt policy

The single source of truth is `SYSTEM_PROMPT` in
`2.backend/app/services/research_agent.py`. Training targets must obey it.

## Must
- Use ONLY the supplied structured context.
- Distinguish the ML score (primary, structured) from `llm_research_score` (bounded support, [0,1]).
- Always surface relevant limitations present in context: `small_sample`,
  `benchmark_missing`, `frozen_features`, `no_real_valuation_profitability_features`,
  `weak_backtest`.
- State it is research-support, not an investment recommendation.
- Output a single JSON object matching `schema.json`.

## Must NOT
- Invent any financial number/fact/price/return not in the context.
- Output investment advice or buy / sell / hold / al / sat / tut.
- Output a price target or an exact expected return unless that exact value is in the model output.
- Use external knowledge or external data.
- Write anything back into datasets.

## Output JSON
```json
{"llm_research_score": 0.0, "llm_confidence": "low|medium|high",
 "summary": "...", "reasoning": "...", "positive_signals": [],
 "negative_signals": [], "warnings": [], "limitations": []}
```
`llm_research_score` is clamped to [0,1] (or null when no numeric judgment applies).
