# Training plan — autoresearch-mlx (M1 Max 64GB)

This repo prepares data + rules only. **No training is run here.** You train
locally later.

## Base models (start small)
| model | size | use |
|---|---|---|
| Qwen2.5-1.5B-Instruct | 1.5B | first instruction tune (fast, cheap) |
| Qwen2.5-3B-Instruct | 3B | main candidate |
| Llama 3.2 3B Instruct | 3B | alternative |
| Phi-3 Mini / Phi-4 Mini | ~3.8B | alternative |
| (optional) a 7B-Instruct | 7B | only after the small pipeline works end-to-end |

## Why not train from scratch
A capstone has neither the data (hundreds of examples, not billions of tokens)
nor the budget. The job is **style + safety alignment**, not learning language.
Instruction-tune an already-capable instruct model with **LoRA** — small adapters,
fast on an M1 Max, no full-weight updates, easy to discard/redo.

## Dataset
- `make research-agent-dataset` writes `instruction_dataset.jsonl` (regenerable)
  and commits `sample_instruction_dataset.jsonl`.
- Size: **≥1k** examples minimum; **5k–20k** better (raise generator `--n`, vary
  tickers/wording). Every target obeys `prompt_policy.md`; numbers come only from
  real reports.
- Split train/val ~90/10. Keep a held-out hand-written eval set for the rubric.

## Stages
1. **Prompt-only baseline** — run a base instruct model with `SYSTEM_PROMPT`,
   score against `evaluation_rubric.md`. Establish the floor before tuning.
2. **LoRA instruction tune** a 1.5B/3B model on the JSONL (format: instruction +
   JSON input → JSON output).
3. **Evaluate** against the rubric (automatic gates first, then manual).
4. **Only if needed**, try a 7B model. Stop when the rubric passes.

## Wiring back
Point the backend at the trained model:
```bash
export RESEARCH_LLM_PROVIDER=lmstudio        # or ollama
export RESEARCH_LLM_BASE_URL=http://localhost:1234/v1/chat/completions
export RESEARCH_LLM_MODEL=your-finetuned-model
```
The service already validates/clamps the model's JSON and falls back to the
deterministic path on any error — so a weak model can never break the pipeline.

## Eval metrics (gate before deploy)
no hallucinated numbers · required limitations present · no investment advice ·
score ∈ [0,1] · mentions benchmark-missing when relevant · mentions frozen data
when relevant · concise professional style.
