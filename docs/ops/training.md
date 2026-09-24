# Training: corpus, framework, and configs

## Framework choice: axolotl

Considered: **axolotl**, **torchtune**, raw **TRL + FSDP**.

**Decision: axolotl.** It wraps FSDP and DeepSpeed under one YAML-driven
interface (see `training/configs/*.yaml`), has direct Qwen3 architecture
support, and its config format is easy to diff and keep in version control —
important here since every crew needs its own config (per-crew adapters, see
[ADR 0003](../architecture/0003-qwen3-base-models.md)) and those configs
should read as data, not as a Python training script duplicated 12 times.
torchtune is comparably capable but younger and less battle-tested for the
LoRA+full-SFT+multi-GPU combination this project needs from day one; raw
TRL+FSDP would mean hand-rolling the config-driven layer axolotl already
provides, for no benefit specific to this project's needs.

## Pipeline

```
training/data/taxonomy.py       10 seed ideas x category x quality-band
        ↓
training/data/generate.py       cross seeds x targets (agent_registry.py),
                                 call the FALLBACK provider (never selfhosted
                                 -- see the module docstring for why),
                                 validate, drop failures, write JSONL
        ↓
training/data/filter.py         MinHash near-dup removal (per target),
                                 length bounds
        ↓
training/data/splits.py         train/val/test split BY SEED IDEA, never by row
        ↓
training/data/to_chat_format.py flat rows -> axolotl's messages[] shape
        ↓
accelerate launch -m axolotl.cli.train training/configs/<model>-<method>.yaml
```

Concretely, for one crew:

```bash
python -m training.data.generate --out training/data/corpus/idea_validation/raw.jsonl
python -m training.data.filter   --in  training/data/corpus/idea_validation/raw.jsonl \
                                  --out training/data/corpus/idea_validation/filtered.jsonl
python -m training.data.splits   --in  training/data/corpus/idea_validation/filtered.jsonl \
                                  --out-dir training/data/corpus/idea_validation/
python -m training.data.to_chat_format --in training/data/corpus/idea_validation/train.jsonl \
                                        --out training/data/corpus/idea_validation/train.chat.jsonl
python -m training.data.to_chat_format --in training/data/corpus/idea_validation/val.jsonl \
                                        --out training/data/corpus/idea_validation/val.chat.jsonl
accelerate launch -m axolotl.cli.train training/configs/qwen3-32b-lora.yaml
```

## Corpus design principle: teach form, not facts

Training data teaches each agent its output schema, reasoning shape, and
calibration. Market sizes, competitors, and prior art arrive at inference
time from retrieval ([ADR 0005](0005-grounding-layer.md)) and are never
baked into weights, where they go stale and resurface as confident
hallucination. Concretely: a training target's `citations` field references
`[src:N]`-style provenance from the prompt's supplied research bundle
snippets, never a real company/paper name the model wasn't given.

This is also why a fine-tuned 32B can plausibly match a 70B on this specific
task shape (see [ADR 0003](../architecture/0003-qwen3-base-models.md)): the
job is structured extraction over supplied context, not recall.

## Quality gates (never train on repaired/salvaged output)

`generate.py` **drops** any example that fails schema validation — it never
retries with the gateway's repair loop
([ADR 0001](../architecture/0001-llm-gateway.md)) to salvage a bad
generation into a training example. A repaired example's "fix" may have been
mechanical (e.g. clamping an out-of-range number) rather than a genuinely
better answer, and training on it would teach the model to reproduce that
same mechanical pattern rather than get the reasoning right the first time.

`filter.py` additionally drops near-duplicates (the fallback provider tends
toward similar phrasing across seed ideas in the same category) and
length-outliers.

## Corpus size

The current `training/data/taxonomy.py` has 10 seed ideas across 8
categories. **This is a starting scaffold, not a production-sized corpus** —
scale up the seed set (more ideas per category, deliberately adversarial
fragments, non-English submissions if the product needs them) before
expecting a real fine-tune to generalize. Track corpus size and diversity
metrics in `docs/ops/eval.md`'s promotion record once real training begins.

## Configs

| File | Model | Method | Hardware |
|---|---|---|---|
| `training/configs/qwen3-32b-lora.yaml` | Qwen3-32B | LoRA (r=32) | 8xB200, DDP |
| `training/configs/qwen3-8b-lora.yaml` | Qwen3-8B | LoRA (r=16) | 8xB200, DDP |
| `training/configs/qwen3-32b-full.yaml` | Qwen3-32B | Full SFT | 8xB200, FSDP full-shard |
| `training/configs/qwen3-8b-full.yaml` | Qwen3-8B | Full SFT | 8xB200, FSDP full-shard |

**LoRA is the recommended default** for both models — see the comment at the
top of `qwen3-32b-full.yaml` for when full-SFT is actually worth its
materially higher compute/iteration cost.

Each config currently targets `training/data/corpus/idea_validation/` as a
worked example — copy per crew, changing the dataset paths and
`lora_out_dir`/`output_dir`.

### Resource envelope (see each config file's own comments for the derivation)

| Config | Approx. VRAM | Effective batch |
|---|---|---|
| qwen3-8b-lora | small fraction of one B200 | 128 |
| qwen3-32b-lora | ~70GB/GPU (DDP-replicated) | 128 |
| qwen3-8b-full | ~128GB total, FSDP-sharded | 128 |
| qwen3-32b-full | ~512GB total, FSDP-sharded across 8 GPUs | 128 |

**None of these numbers are validated against a real run yet** — see
[dgx-runbook.md](dgx-runbook.md)'s "known unknowns." Update this table with
real measurements from the first actual training job.
