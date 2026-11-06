# `idea-refine` — Structured Divergent & Convergent Ideation

## Provenance & Attribution
- Adapted from [`addyosmani/agent-skills/skills/idea-refine`](https://github.com/addyosmani/agent-skills/tree/main/skills/idea-refine).

## Cluster & Context Budget Rationale
- **Cluster:** Cluster 1 — Global Core (Always Active Everywhere)
- **Why Global Core:** Ideation and assumption stress-testing happen across every repository and off-corp workspace before any domain stack is chosen. Keeping `idea-refine` in Global Core ensures structured divergent-to-convergent thinking is always available prior to `grill-and-spec`.

## Directory Contents
- [`SKILL.md`](SKILL.md): Agent-facing 3-phase ideation protocol (`Understand & Expand` -> `Evaluate & Converge` -> `Sharpen & Ship`).
- [`scripts/idea-refine.sh`](scripts/idea-refine.sh): Optional workspace initializer for `./docs/ideas/` (accepts an alternative directory as its first argument and prints a JSON status line).
- [`references/frameworks.md`](references/frameworks.md): Thinking frameworks (SCAMPER, First Principles, Inversion, Jobs-to-be-Done, Pre-Mortem, 10x vs 10%).
- [`references/refinement-criteria.md`](references/refinement-criteria.md): Evaluation rubrics across User Value, Feasibility, and Differentiation.
- [`references/examples.md`](references/examples.md): Concrete worked examples of full ideation sessions.
