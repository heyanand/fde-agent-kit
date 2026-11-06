# `sync` — Skill Synchronization & Environment Manager

## Provenance & Attribution
- Inspired by [`ksprashu/agent-skill-forge/skills/sync`](https://github.com/ksprashu/agent-skill-forge/tree/main/skills/sync), extended for multi-harness support (Google Antigravity, Gemini CLI, Claude Code, and OpenAI Codex) and conditional corp vs. off-corp overlays.

## Cluster & Context Budget Rationale
- **Cluster:** Cluster 1 — Global Core (Always Active Everywhere)
- **Why Global Core:** Always active globally so that from any working directory on the machine, the agent or engineer can audit symlink health, prune broken corp symlinks when working off-corp, or JIT-attach domain skills into the current project via `sync_skills.py`.

## Directory Contents
- [`SKILL.md`](SKILL.md): Agent-facing workflow instructions for auditing, fixing, pruning, and JIT-linking skills.
- [`scripts/sync_skills.py`](scripts/sync_skills.py): Canonical symlink and manifest synchronization CLI (`find_repo_root()` resolves symlinks back to `fde-agent-kit`). The repo-root `scripts/sync_skills.py` is a thin wrapper that delegates to this file.

## Usage
```bash
# Audit symlinks across all harnesses
python3 ~/.gemini/config/skills/sync/scripts/sync_skills.py

# Link Global Core skills, sync global AGENTS.md rules, and prune dead links (preview first)
python3 ~/.gemini/config/skills/sync/scripts/sync_skills.py --fix --prune --sync-rules --dry-run
python3 ~/.gemini/config/skills/sync/scripts/sync_skills.py --fix --prune --sync-rules
```
Claude Code and Codex users can substitute `~/.claude/skills/sync` or `~/.codex/skills/sync`; on a fresh machine, run `python3 scripts/sync_skills.py --fix` from the clone first.
