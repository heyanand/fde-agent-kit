# `work` — Autonomous Milestone DAG Execution Engine

## Provenance & Attribution
- Synthesizes `work` from [`ksprashu/agent-skill-forge/skills/work`](https://github.com/ksprashu/agent-skill-forge/tree/main/skills/work) with `incremental-implementation` and `orchestration-patterns` from [`addyosmani/agent-skills`](https://github.com/addyosmani/agent-skills).

## Cluster & Context Budget Rationale
- **Cluster:** Cluster 2 — Project-Scoped JIT Domain Skill
- **Why Project JIT:** Attached when executing a multi-milestone specification produced by `grill-and-spec`, providing `tasks/handoff.md` session continuity, zero-mock gates, 3-strike failure escalation, and `git worktree` parallel fan-out.

## Directory Contents
- [`SKILL.md`](SKILL.md): Agent-facing per-milestone execution loop, zero-mock gate, and 3-strike escalation rules.
- [`templates/handoff.md`](templates/handoff.md): Persistent milestone DAG and session handoff state template.
- [`references/orchestration-patterns.md`](references/orchestration-patterns.md): Decision criteria for direct execution vs. parallel subagent fan-out across git worktrees.

## JIT Attachment Command
```bash
python3 /path/to/fde-agent-kit/skills/sync/scripts/sync_skills.py --project . --skills work
```
