# `documentation-and-adrs` — MADR Decisions, API Docs & Prose Review

## Provenance & Attribution
- Adapted from [`addyosmani/agent-skills/skills/documentation-and-adrs`](https://github.com/addyosmani/agent-skills/blob/main/skills/documentation-and-adrs/SKILL.md).

## Cluster & Context Budget Rationale
- **Cluster:** Cluster 2 — Project-Scoped JIT Domain Skill (Included in `--pack arch`)
- **Why Project JIT:** Loaded on demand when recording architectural trade-offs, documenting public APIs/ADK tools, or editing technical docs so its MADR templates and examples only consume tokens during documentation work.

## Directory Contents
- [`SKILL.md`](SKILL.md): Agent-facing MADR lifecycle rules, why-not-what code comment discipline, typed API docstring standards, and fact-preserving prose review protocol.
- [`templates/madr-template.md`](templates/madr-template.md): Markdown Architectural Decision Record (MADR) template.

## JIT Attachment Command
```bash
python3 /path/to/fde-agent-kit/skills/sync/scripts/sync_skills.py --project . --skills documentation-and-adrs
```
