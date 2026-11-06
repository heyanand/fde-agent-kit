# `sdlc-and-portal` — SDLC Documentation Suite & Interactive HTML Portal Compiler

## Provenance & Attribution
- Inspired by [`ksprashu/agent-skill-forge/skills/docs`](https://github.com/ksprashu/agent-skill-forge/tree/main/skills/docs), renamed to `sdlc-and-portal` to disambiguate SDLC deliverables and HTML portal compilation from `documentation-and-adrs`.

## Cluster & Context Budget Rationale
- **Cluster:** Cluster 2 — Project-Scoped JIT Domain Skill (Included in `--pack arch` and `--pack devrel`)
- **Why Project JIT:** Attached on demand when authoring PRDs, Technical Design Docs, or Executive Readouts, or when compiling multi-file Markdown directories into a standalone single-file HTML presentation portal (`compile_portal.py`).

## Directory Contents
- [`SKILL.md`](SKILL.md): Agent-facing SDLC document selection guide and HTML portal compilation instructions.
- [`scripts/compile_portal.py`](scripts/compile_portal.py): Compiles Markdown files and directories into a standalone `.html` portal with `<script>` breakout protection and offline fallback.
- [`templates/portal.html`](templates/portal.html): Interactive Light/Dark mode HTML shell with live Mermaid re-rendering.
- [`templates/prd-template.md`](templates/prd-template.md): Product Requirements Document (PRD) template.
- [`templates/design-doc-template.md`](templates/design-doc-template.md): Technical Design Document (TDD) template.
- [`templates/exec-readout-template.md`](templates/exec-readout-template.md): Executive Readout template.

## JIT Attachment Command
```bash
python3 /path/to/fde-agent-kit/skills/sync/scripts/sync_skills.py --project . --skills sdlc-and-portal
```
