# `code-review-and-quality` — 5-Axis Code Review & Mutation Gate

## Provenance & Attribution
- Adapted from [`addyosmani/agent-skills/skills/code-review-and-quality`](https://github.com/addyosmani/agent-skills/blob/main/skills/code-review-and-quality/SKILL.md), folding in `code-simplification` and `dependency-management` hygiene.

## Cluster & Context Budget Rationale
- **Cluster:** Cluster 1 — Global Core (Always Active Everywhere) & included in `--pack audit`
- **Why Global Core:** Code review across Correctness, Readability, Architecture, Security, and Performance applies to every code change on-corp and off-corp, including workspaces where no dedicated code-review tooling or reviewer agent is available.

## Directory Contents
- [`SKILL.md`](SKILL.md): Agent-facing 5-axis review protocol, structural remedies, mutation check, and severity labels.
- [`references/security-checklist.md`](references/security-checklist.md): OWASP Web & LLM Top 10 security review checklist.
- [`references/performance-checklist.md`](references/performance-checklist.md): Database, async I/O, memory, and LLM token/latency checklist.
