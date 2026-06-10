# research_agent_training/

Training-preparation assets for the research-support LLM layer. **No model is
trained here** — this only produces instruction data, the prompt policy, a schema,
and an evaluation rubric. Production can use OpenRouter; local adapters can be
trained later with autoresearch-mlx.

## Files
| file | purpose |
|---|---|
| `generate_instruction_dataset.py` | builds JSONL examples from real project reports + `research_agent` contexts |
| `sample_instruction_dataset.jsonl` | small committed sample (the full set is regenerable, gitignored) |
| `schema.json` | JSON schema every training example must satisfy |
| `prompt_policy.md` | the safety/constraint rules (mirrors `SYSTEM_PROMPT`) |
| `evaluation_rubric.md` | automatic + manual acceptance criteria |
| `mlx_training_plan.md` | how to LoRA-tune on M1 Max, base-model choices, stages |

## Generate
```bash
make research-agent-dataset
# or: PYTHONPATH=. python research_agent_training/generate_instruction_dataset.py --n 2000
```

## Rules
- Numbers come only from validated reports — no fabricated financial facts.
- Targets obey `prompt_policy.md`: no buy/sell/hold, no price target, score in
  [0,1], required limitations surfaced.
- LLM-generated text is **never** written back into the modeling dataset.

The LLM is a decision-support layer, not the numerical predictor. The structured
ML pipeline remains primary. Outputs are research-support, not investment advice.
