# `skill-forge` — Portable Agent Skill Authoring & Evaluation Guide

## Provenance & Attribution
- Synthesizes `skill-creator` and `upskill` with the portable multi-harness architecture of [`ksprashu/agent-skill-forge`](https://github.com/ksprashu/agent-skill-forge) and [`addyosmani/agent-skills`](https://github.com/addyosmani/agent-skills).

## Cluster & Context Budget Rationale
- **Cluster:** Cluster 2 — Project-Scoped JIT Domain Skill
- **Why Project JIT:** Attached when authoring, refactoring, or evaluating a new portable `SKILL.md` across Google Antigravity, Gemini CLI, Claude Code, and OpenAI Codex.

## Directory Contents
- [`SKILL.md`](SKILL.md): Agent-facing 7 laws of portable skill authoring (including the separation between `README.md` human provenance and `SKILL.md` agent functionality) and trigger boundary evaluation protocol.
- [`templates/SKILL-template.md`](templates/SKILL-template.md): Starter `SKILL.md` scaffold.

## JIT Attachment Command
```bash
python3 /path/to/fde-agent-kit/skills/sync/scripts/sync_skills.py --project . --skills skill-forge
```
