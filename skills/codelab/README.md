# `codelab` — Interactive Technical Workshop & Codelab Generator

## Provenance & Attribution
- Inspired by [`ksprashu/agent-skill-forge/skills/codelab`](https://github.com/ksprashu/agent-skill-forge/tree/main/skills/codelab).

## Cluster & Context Budget Rationale
- **Cluster:** Cluster 2 — Project-Scoped JIT Domain Skill (Included in `--pack devrel`)
- **Why Project JIT:** Attached on demand when building step-by-step customer enablement labs, developer workshops, or PoC tutorials.

## Directory Contents
- [`SKILL.md`](SKILL.md): Agent-facing 7-phase pedagogical structure (`Concept -> Action -> Checkpoint`) and copy-paste safety rules.
- [`templates/codelab-template.md`](templates/codelab-template.md): Complete codelab template verified by `verify_static.py --mode codelab`.

## JIT Attachment Command
```bash
python3 /path/to/fde-agent-kit/skills/sync/scripts/sync_skills.py --project . --skills codelab
```
