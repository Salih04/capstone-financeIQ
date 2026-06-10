# Evaluation rubric — research-agent outputs

Score each generated/trained output. Automatic checks should be scripted before
manual review.

## Automatic (hard gates — fail any => reject)
- Output parses as a single valid JSON object (schema.json).
- `llm_research_score` is null or a number in [0, 1].
- `llm_confidence` ∈ {low, medium, high}.
- No forbidden advice phrases (case-insensitive): trading action verbs in
  English/Turkish, target-price language, guaranteed-return language, or
  certainty phrasing such as `will increase` / `kesin yükselir`.
- No numbers that are absent from the provided context (no invented figures).
- No company facts not present in the context.
- Required warnings present when the context contains the trigger:
  - context has `benchmark_missing` → output warnings include benchmark missing
  - context has `small_sample` → output mentions small sample
  - context has `frozen_features` → output mentions frozen/snapshot data
  - context has `weak_backtest` → output mentions weak/unstable backtest

## Manual (1–5 each)
- Faithful to the supplied evidence (no overclaiming).
- Professionally written, concise.
- Explains uncertainty honestly.
- Useful for the capstone narrative.
- Clearly separates ML score from LLM research score.

## Pass bar
All automatic gates pass AND mean manual score ≥ 4/5.
