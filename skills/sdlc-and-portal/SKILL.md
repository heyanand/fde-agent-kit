---
name: sdlc-and-portal
description: >-
  Authors structured SDLC documents (PRDs, Technical Design Docs, Executive
  Readouts) and compiles multi-file Markdown directories into standalone,
  single-file interactive HTML presentation portals. Use when generating
  customer deliverables, architecture readouts, or offline-capable HTML doc
  portals. Don't use for single MADR decision records, inline code comments, or
  API docstrings (use documentation-and-adrs) or step-by-step hands-on labs (use
  codelab).
---

# SDLC Documentation Suite & Interactive HTML Portal Compiler (`sdlc-and-portal`)

Provides structured templates for enterprise SDLC documentation and a zero-build compiler (`<skill-dir>/scripts/compile_portal.py`) that packages multiple Markdown files (with Mermaid diagrams and Light/Dark themes) into a single portable `.html` file.

---

## 1. Bundled SDLC Document Templates

Select the right template from `<skill-dir>/templates/` based on the audience and stage:

| Deliverable Type | Template Path | Target Audience | Prose Verification Profile |
| :--- | :--- | :--- | :--- |
| **Product Requirements (PRD)** | [templates/prd-template.md](templates/prd-template.md) | Product, Eng Leads, Stakeholders | `--profile narrative` |
| **Technical Design Doc (TDD)** | [templates/design-doc-template.md](templates/design-doc-template.md) | Principal/Staff Architects, SecOps | `--profile technical` |
| **Executive Readout** | [templates/exec-readout-template.md](templates/exec-readout-template.md) | Customer Execs, CISO, VP Eng | `--profile narrative` |
| **Interactive HTML Portal** | [templates/portal.html](templates/portal.html) | Offline / Air-Gapped Customer Handover | Compiled via `compile_portal.py` |

### Authoring Rules for Customer & Executive Deliverables
1. **Lead with Falsifiable Numbers:** State latency percentiles (`p50`, `p95`, `p99`), throughput (`QPS`), accuracy on golden sets, and unit cost in Section 1.
2. **Enforce Typography Restraint (`unslop`):** In PRDs and Executive Readouts, restrict bolding to bullet lead-in titles and primary headline metrics, and avoid inline backtick clutter (`Roboto Mono`) in narrative paragraphs.
3. **Quote Mermaid Labels:** Always wrap Mermaid node labels containing parentheses or brackets in double quotes (`Gateway["API Gateway (Regional)"]`) so diagrams never fail to render in the portal.

---

## 2. Compiling an Interactive Single-File HTML Portal

When delivering a suite of Markdown documents (e.g., `PRD.md`, `TDD.md`, `docs/adr/`, and `EXEC_READOUT.md`) to a customer or stakeholder who wants a clean, browsable web experience without running a local server:

```bash
# Compile specific Markdown files or entire directories into one standalone HTML file
# <skill-dir> is the directory containing this SKILL.md (any harness link, or skills/sdlc-and-portal in the kit)
python3 <skill-dir>/scripts/compile_portal.py \
  --title "Sovereign AI Platform - Architecture Portal" \
  --output dist/architecture-portal.html \
  docs/PRD.md docs/TDD.md docs/adr/
```

### Security & Offline Resilience Features Built Into `compile_portal.py`
- **XSS & `<script>` Breakout Prevention:** Encodes every `<`, `>`, and `&` as `\u003c` / `\u003e` / `\u0026` inside `<script id="portal-data" type="application/json">` (blocks both `</script>` breakout and `<!--<script>` parser-state attacks), strips `<script>`, `<iframe>`, `<object>`, `<embed>`, `<form>`, `<base>`, `<meta>`, `<link>`, `<style>`, `on*=`/`style`/`srcdoc` attributes, and `javascript:` / non-image `data:` URLs before DOM insertion. External links open in a new tab with `rel="noopener noreferrer"`.
- **Air-Gapped / VPC-SC Fallback:** Includes a built-in zero-dependency Markdown parser fallback (`fallbackMarkdown`) so the portal remains readable even on air-gapped workstations with no internet/CDN access.
- **Live Light / Dark Theme Re-Rendering:** Toggling Light/Dark mode dynamically re-initializes and re-renders all Mermaid diagrams (`data-mermaid-src`).
- **Directory & Duplicate Stem Support:** Accepts directory paths (recursively collecting `*.md` / `*.markdown`, skipping hidden dirs, `node_modules`, `venv`, and `__pycache__`), de-duplicates files passed twice, and disambiguates duplicate filenames (`docs/api/README.md` vs. `docs/infra/README.md`).
- **Navigation & Titles:** Section titles come from the first `# Heading` outside YAML front matter and code fences (falling back to the filename); front matter is stripped before rendering. Every section is deep-linkable via `#<section-id>`, and arrow keys (or `j` / `k`) page between sections.
- **Fail-Fast Errors:** Missing paths, non-Markdown files, non-UTF-8 files, and an `--output` that is a directory exit non-zero with a specific message; a non-`.html` output path prints a warning.

---

## 3. Mandatory Verification Gate

Before compiling or delivering documentation, run the sibling `verify` skill (`<skill-dir>` is the directory containing this `SKILL.md`; sibling kit skills such as `verify` and `sdlc-and-portal` resolve as `<skill-dir>/../<skill>` because every harness links skills from the same `fde-agent-kit` clone.):
```bash
# 1. Verify narrative documents (PRDs, Executive Readouts)
python3 <skill-dir>/../verify/scripts/verify_static.py --mode prose --profile narrative docs/EXEC_READOUT.md

# 2. Verify technical design documents
python3 <skill-dir>/../verify/scripts/verify_static.py --mode prose --profile technical docs/TDD.md
```

## Common Rationalizations

| Rationalization | Reality |
| :--- | :--- |
| "I'll write the Design Doc without an Alternatives Considered table" | A design doc that only presents one option looks like post-hoc justification, not engineering analysis. |
| "I'll hand-craft an HTML file from scratch instead of running `compile_portal.py`" | Hand-rolled HTML often introduces raw `</script>` breakout bugs or broken theme switching. Use `compile_portal.py`. |
| "I don't need to quote Mermaid labels in Markdown" | Unquoted parentheses (`Node[Service (v2)]`) crash Mermaid's parser inside the compiled HTML portal. |

## Red Flags

- PRDs or Design Docs missing an explicit **Non-Goals (Out of Scope)** section
- Executive readouts cluttered with inline backticks or bolded sentences that fail `--mode prose --profile narrative`
- Mermaid diagrams using unsupported diagram types or unquoted parentheses in labels
- Raw unescaped JSON interpolated directly into `<script>` tags

## Verification

- [ ] Document uses the appropriate template from `templates/` (`prd-template.md`, `design-doc-template.md`, or `exec-readout-template.md`)
- [ ] All Markdown source files pass `verify_static.py --mode prose` (`narrative` or `technical` profile)
- [ ] `compile_portal.py` exits `0` and produces a self-contained `.html` file
