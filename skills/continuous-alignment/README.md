# `continuous-alignment` — Session Distillation & Context Budget Enforcer

## Provenance & Attribution
- Synthesizes `continuous-alignment` and `distill-session` from [`ksprashu/agent-skill-forge`](https://github.com/ksprashu/agent-skill-forge) with `context-engineering` from [`addyosmani/agent-skills`](https://github.com/addyosmani/agent-skills).

## Cluster & Context Budget Rationale
- **Cluster:** Cluster 2 — Project-Scoped JIT Domain Skill (Included in `--pack arch`)
- **Why Project JIT:** Invoked at session wrap-up or when rule files approach the 200-line ceiling to distill transcripts into MADR records (`docs/adr/`) and keep `AGENTS.md`, `CLAUDE.md`, and `GEMINI.md` within budget.

## Directory Contents
- [`SKILL.md`](SKILL.md): Agent-facing 5-step session distillation and token budget enforcement workflow.
- [`scripts/distill_session.py`](scripts/distill_session.py): Multi-harness JSONL transcript analyzer, gap-safe ADR scaffolder (`--new-adr`), and 200-line budget enforcer (`--check-budget`).

## JIT Attachment Command
```bash
python3 /path/to/fde-agent-kit/skills/sync/scripts/sync_skills.py --project . --skills continuous-alignment
```
