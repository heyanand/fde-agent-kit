# `image-gen` — Visual Asset & Architecture Diagram Generator

## Provenance & Attribution
- Inspired by [`ksprashu/agent-skill-forge/skills/image-gen`](https://github.com/ksprashu/agent-skill-forge/tree/main/skills/image-gen), hardened with `x-goog-api-key` header authentication, Vertex AI / Gemini Enterprise Agent Platform `location="global"` ADC routing, and validated Gemini Native Image (`gemini-nano-banana-2.1`, `gemini-3-pro-image`, `gemini-3.1-flash-lite-image`, `gemini-2.5-flash-image`) payload controls.

## Cluster & Context Budget Rationale
- **Cluster:** Cluster 2 — Project-Scoped JIT Domain Skill (Included in `--pack arch` and `--pack devrel`)
- **Why Project JIT:** Attached on demand when generating conceptual architecture illustrations, README hero banners, executive infographics, or app icons from the CLI across corp and off-corp environments.

## Directory Contents
- [`SKILL.md`](SKILL.md): Agent-facing art direction presets (`arch`, `hero`, `infographic`, `icon`), model families, and prompt engineering rules.
- [`scripts/image_gen.py`](scripts/image_gen.py): Zero-dependency CLI supporting `--style`, `--ar`, `--model`, `--seed`, `--negative-prompt`, `--reference-image`, and `--dry-run`.

## JIT Attachment Command
```bash
python3 /path/to/fde-agent-kit/skills/sync/scripts/sync_skills.py --project . --skills image-gen
```
