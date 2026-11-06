---
name: codelab
description: >-
  Authors interactive, visual-first technical workshops, customer enablement
  labs, and step-by-step tutorials with duration metadata, unified environment
  variable blocks, per-step verification checkpoints, and mandatory resource
  teardown. Use when creating hands-on training labs, PoC walkthroughs, or
  developer workshops. Don't use for static architecture decision records (use
  documentation-and-adrs) or PRDs and HTML portals (use sdlc-and-portal).
---

# Interactive Technical Workshop & Codelab Generator (`codelab`)

Generates high-craft, copy-paste-safe technical labs following a **7-Phase Visual-First Pedagogical Structure** using [templates/codelab-template.md](templates/codelab-template.md).

---

## 1. The 7-Phase Codelab Pedagogical Workflow

Every codelab must guide the learner through progressive, self-verifying stages:

1. **Phase 1 — Architectural Hook & Mental Model (`Overview`):**
   - Open with a concrete outcome statement (*"In 45 minutes, you will deploy and stress-test..."*) and a Mermaid `flowchart` or `sequenceDiagram` (with quoted labels) showing how the components fit together.
2. **Phase 2 — Single-Source Environment Setup (`Environment Setup`):**
   - Define **all** shared environment variables (`export PROJECT_ID=...`, `export REGION=...`) in one top-level setup block.
   - Every subsequent command in the lab must reference `${PROJECT_ID}`, `${REGION}`, etc., rather than mixing `<YOUR_PROJECT>` placeholders midway through the tutorial.
3. **Phase 3 — Concept -> Action -> Checkpoint Rhythm (`Steps 1..N`):**
   - Structure every lab step into three parts:
     - **Concept (Why):** 2–3 sentences explaining the architectural reason for the step.
     - **Action (Do):** Copy-pasteable commands or complete file blocks (never partial diffs with `...` that fail when pasted).
     - **Checkpoint (Verify):** A deterministic command and expected output snippet proving the step succeeded before the learner moves on.
4. **Phase 4 — Intentional Failure & Troubleshooting Callout:**
   - Include at least one realistic troubleshooting callout (*"If you see `PERMISSION_DENIED` on KMS key..."*) teaching the learner how to diagnose real-world errors.
5. **Phase 5 — End-to-End Integration Verification:**
   - Provide a final integration test or curl/pytest command that exercises the entire deployed system.
6. **Phase 6 — Mandatory Resource Teardown (`Cleanup`):**
   - Every lab that provisions cloud resources, containers, or background processes **must** end with a copy-pasteable `Cleanup & Resource Teardown` section so learners never incur surprise billing.
7. **Phase 7 — Optional Interactive HTML Export:**
   - If the workshop is delivered as a self-paced web portal, compile it with `python3 <skill-dir>/../sdlc-and-portal/scripts/compile_portal.py --output dist/codelab.html <codelab.md>` (works whether or not `sdlc-and-portal` is attached to the project, because it resolves through this skill's link into the kit).

---

## 2. Copy-Paste & Typography Safety Rules

- **Zero Unicode Dashes in Code Fences:** Never use em-dashes (`—`) or en-dashes (`–`) inside fenced bash/python/hcl blocks (`--flag` corrupted to `—flag` breaks CLI execution).
- **No Unlabeled Placeholders in Commands:** Prefer `${ENV_VAR}` over `<replace-me>` inside bash blocks so learners only edit variables once in Section 2.
- **Sequential Section Numbering:** Keep top-level headings sequentially numbered (`## 1.`, `## 2.`, ..., `## N. Cleanup`).

---

## 3. Mandatory Static Verification Gate

Before delivering any codelab, run `verify_static.py --mode codelab` (`<skill-dir>` is the directory containing this `SKILL.md`; sibling kit skills such as `verify` and `sdlc-and-portal` resolve as `<skill-dir>/../<skill>` because every harness links skills from the same `fde-agent-kit` clone.):
```bash
python3 <skill-dir>/../verify/scripts/verify_static.py --mode codelab path/to/codelab.md
```
This verifies:
- Presence of `Duration:` metadata.
- Presence of `Checkpoint` verification blocks.
- Presence of a `Cleanup` / `Teardown` section.
- Closed code fences, valid Mermaid syntax, and zero Unicode dashes inside code blocks.

## Common Rationalizations

| Rationalization | Reality |
| :--- | :--- |
| "Learners can figure out how to edit snippets with `// ... existing code ...`" | Partial snippets cause copy-paste syntax errors during live workshops. Provide complete, runnable blocks or `cat <<'EOF'` commands. |
| "It's just a sandbox lab, so a Cleanup section isn't necessary" | Leftover Cloud Run services, GKE clusters, or Vertex endpoints rack up hundreds of dollars in forgotten charges. Always include `Cleanup`. |
| "I don't need a Checkpoint after every step" | Without per-step checkpoints, a typo in Step 1 only surfaces as a mysterious failure in Step 5. |

## Red Flags

- Commands that mix `${PROJECT_ID}`, `YOUR_PROJECT_ID`, and `<project-id>` across different steps
- Steps that mutate state without a `### Checkpoint` verification block
- Missing `Duration:` header or missing `Cleanup & Resource Teardown` section
- Unicode em-dashes (`—`) inside bash or Python code blocks

## Verification

- [ ] Lab follows [templates/codelab-template.md](templates/codelab-template.md) with sequential headings
- [ ] All shared variables are exported in `## 2. Environment Setup` and referenced via `${VAR}` throughout
- [ ] Every step includes `Concept`, `Action`, and `Checkpoint`
- [ ] Passes `python3 <skill-dir>/../verify/scripts/verify_static.py --mode codelab <file.md>` with 0 findings
