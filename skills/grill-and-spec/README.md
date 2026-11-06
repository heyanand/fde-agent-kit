# `grill-and-spec` — Socratic Pre-Flight, Capability Map & Milestone DAG

## Provenance & Attribution
- Synthesizes `interview-me`, `spec-driven-development`, and `planning-and-task-breakdown` from [`addyosmani/agent-skills`](https://github.com/addyosmani/agent-skills) with `grill-me`, `write-a-spec`, and `spec-to-plan` from [`ksprashu/agent-skill-forge`](https://github.com/ksprashu/agent-skill-forge).

## Cluster & Context Budget Rationale
- **Cluster:** Cluster 1 — Global Core (Always Active Everywhere)
- **Why Global Core:** Merging Socratic requirements discovery, Capability Mapping, and vertical-slice Milestone DAG specification into a single Global Core skill eliminates routing ambiguity and ensures every non-trivial feature starts with a verified contract.

## Directory Contents
- [`SKILL.md`](SKILL.md): Agent-facing 3-stage specification protocol with FDE sovereign/IAM/latency lenses and terminal stop gate.
- [`templates/spec-template.md`](templates/spec-template.md): 8-section technical specification and Milestone DAG template.
- [`references/definition-of-done.md`](references/definition-of-done.md): 4-category standing Definition of Done checklist (Correctness, Quality & Simplicity, Security & Sovereignty, Documentation & Handoff).
- [`references/fde-discovery-lenses.md`](references/fde-discovery-lenses.md): 5-lens enterprise and agentic AI question bank for the Socratic pre-flight (sovereignty, LLM runtime resilience, evaluation, FinOps, Day-2 operations).
