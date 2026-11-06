# `catalog` — Skill Router & Open Knowledge Format (OKF) Indexer

## Provenance & Attribution
- Inspired by [`ksprashu/agent-skill-forge/skills/catalog`](https://github.com/ksprashu/agent-skill-forge/tree/main/skills/catalog) and `using-agent-skills` from [`addyosmani/agent-skills`](https://github.com/addyosmani/agent-skills).

## Cluster & Context Budget Rationale
- **Cluster:** Cluster 1 — Global Core (Always Active Everywhere)
- **Why Global Core:** Keeping `catalog` permanently symlinked into `~/.gemini/config/skills`, `~/.gemini/skills`, `~/.claude/skills`, and `~/.codex/skills` lets the agent know the complete inventory of all 17 skills and 4 preset packs from any directory on the machine without paying the context window cost of loading every domain skill globally.

## Directory Contents
- [`SKILL.md`](SKILL.md): Agent-facing routing tables (Clusters 1–3), request-to-skill routing examples, and the Open Knowledge Format (`OKF v0.2`) indexing protocol.
- [`references/okf-spec.md`](references/okf-spec.md): `INDEX.okf.md` frontmatter schema, a complete example index, concept-file frontmatter, and edge cases.

## Sync & Invocation
```bash
# Globally linked (run once from the fde-agent-kit clone):
python3 scripts/sync_skills.py --fix
```
