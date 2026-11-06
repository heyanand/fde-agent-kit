# `git-workflow-and-versioning` — Atomic Git, Worktrees & SemVer

## Provenance & Attribution
- Adapted from [`addyosmani/agent-skills/skills/git-workflow-and-versioning`](https://github.com/addyosmani/agent-skills/blob/main/skills/git-workflow-and-versioning/SKILL.md).

## Cluster & Context Budget Rationale
- **Cluster:** Cluster 1 — Global Core (Always Active Everywhere)
- **Why Global Core:** Essential in every standard Git workspace (especially off-corp in standard Git workspaces) to enforce save-point commits, atomic splitting of dirty trees, pre-commit secret scanning, `git worktree` isolation, and SemVer changelogs.

## Directory Contents
- [`SKILL.md`](SKILL.md): Agent-facing Git workflow, secret-scanning regex gate, worktree commands, 3-part post-modification scope summary, and SemVer rules.
