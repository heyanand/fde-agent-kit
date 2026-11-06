# `verify` — Expectation-Grounded Alignment (EGA) & Static Verifier

## Provenance & Attribution
- Inspired by [`ksprashu/agent-skill-forge/skills/verify`](https://github.com/ksprashu/agent-skill-forge/tree/main/skills/verify) and `doubt-driven-development` from [`addyosmani/agent-skills`](https://github.com/addyosmani/agent-skills).

## Cluster & Context Budget Rationale
- **Cluster:** Cluster 1 — Global Core (Always Active Everywhere) & included in `--pack audit`
- **Why Global Core:** Provides the universal completion gate across all code, docs, skills, ADK agents, and Terraform modules via Stage 1 deterministic checks (`verify_static.py`) and Stage 2 blinded multi-persona evaluation.

## Directory Contents
- [`SKILL.md`](SKILL.md): Agent-facing 2-stage EGA verification protocol and blinded 3-persona rubric.
- [`scripts/verify_static.py`](scripts/verify_static.py): Deterministic static verifier supporting `--mode prose` (`--profile narrative|technical`), `--mode skill`, `--mode adk`, `--mode terraform`, `--mode codelab`, and `--mode okf`. Skill mode also requires a non-empty `README.md` per skill (`SKILL_MISSING_README`), keeps provenance out of `SKILL.md` (`SKILL_PROVENANCE_IN_BODY`), and checks relative links in both files.
- [`references/rubrics.md`](references/rubrics.md): Per-persona Stage 2 criteria tables (Architect, Staff QA & Security, End-User) and verdict rules.
