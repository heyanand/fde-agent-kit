---
name: verify
description: >-
  Executes Expectation-Grounded Alignment (EGA) verification combining
  deterministic static AST/regex checks (verify_static.py) with blinded
  multi-persona adversarial evaluation. Use when verifying any completed code
  slice, architecture spec, ADR, Terraform module, ADK agent, codelab, or
  narrative document before claiming completion. Don't use as a substitute for
  running the project's unit/integration test suite, or for reviewing someone
  else's PR against code-health axes (use code-review-and-quality).
---

# Expectation-Grounded Alignment & Verification (`verify`)

Never claim a task is complete based on *"seems right"* or self-congratulatory review. Verification runs in two mandatory stages: **Stage 1 (Deterministic Static Gate)** followed by **Stage 2 (Blinded Multi-Persona Evaluation)**.

---

## Stage 1: Deterministic Static Gate (`verify_static.py`)

Run `<skill-dir>/scripts/verify_static.py` before spending tokens on LLM rubric evaluation. `<skill-dir>` is the directory containing this `SKILL.md` (for example `~/.gemini/config/skills/verify`, `~/.gemini/skills/verify`, `~/.claude/skills/verify`, or `skills/verify` inside the `fde-agent-kit` clone). The script uses only the Python 3.9+ standard library.

Exit codes: `0` means every target is clean; `1` means at least one `[FAIL]` finding was printed. Fix every finding before proceeding; do not hand-wave a finding as a false positive without changing the artifact or the check.

### Supported Static Verification Modes

```bash
# 1. Narrative Prose Mode (Resumes, Executive Readouts, Customer Narratives)
# Enforces <=3 bold spans/line, <=3 inline code backticks/line, no AI-slop terms,
# closed fences, and Mermaid rules
python3 <skill-dir>/scripts/verify_static.py --mode prose --profile narrative path/to/narrative.md

# 2. Technical Prose Mode (READMEs, Specs, ADRs, Design Docs)
# Enforces closed fences, Mermaid diagram types + quoted labels, no AI-slop terms,
# and no Unicode dashes in code blocks
python3 <skill-dir>/scripts/verify_static.py --mode prose --profile technical path/to/doc.md

# 3. Skill Authoring Mode (one skill directory, one SKILL.md, or a whole skills/ root)
# Enforces kebab-case dir name, frontmatter name match, 50..800 line bounds,
# 'Use when' / 'Don't use' triggers, relative links in SKILL.md and README.md,
# a non-empty README.md next to SKILL.md, no provenance text in SKILL.md,
# and no em-dashes in code blocks
python3 <skill-dir>/scripts/verify_static.py --mode skill path/to/skills/

# 4. Google ADK Agent Mode (Python package dir or agent.py)
# Enforces __init__.py, AST-assigned root_agent, and docstrings + type hints on sync/async tools
python3 <skill-dir>/scripts/verify_static.py --mode adk path/to/agent_pkg/

# 5. Terraform / Sovereign Cloud Mode (Terraform root module directory)
# Recursively scans *.tf (ignoring comments) for roles/owner, roles/editor, allUsers,
# allAuthenticatedUsers, and checks main.tf, variables.tf, outputs.tf, versions.tf
python3 <skill-dir>/scripts/verify_static.py --mode terraform path/to/tf_module/

# 6. Codelab & OKF Modes
python3 <skill-dir>/scripts/verify_static.py --mode codelab path/to/codelab.md
python3 <skill-dir>/scripts/verify_static.py --mode okf path/to/INDEX.okf.md
```

### Finding Codes and Fixes

| Code | Mode | Fix |
| :--- | :--- | :--- |
| `UNCLOSED_FENCE` | prose, skill | Add the closing fence with the same character and at least the same length as the opener. |
| `CODE_UNICODE_DASH` | prose, skill | Replace an em/en-dash inside a non-Markdown code fence with `--` or `-`. |
| `MERMAID_TYPE` / `MERMAID_UNQUOTED_LABEL` | prose, skill | Use a supported diagram type; quote labels with parentheses: `id["Label (Info)"]`. |
| `PROSE_BOLD_OVERUSE` / `PROSE_BACKTICK_CLUTTER` | prose (narrative) | Cut to at most 3 bold or 3 inline-code spans per line (see the `unslop` skill). |
| `PROSE_SLOP_TERM` | prose (both profiles) | Replace high-confidence slop (*delve*, *seamless*, *cutting-edge*, *synergy*, *spearhead*, *it is worth noting*, ...) with the concrete mechanism or metric. Terms inside inline code, italics, quotes, tables, blockquotes, and fences count as mentions and are skipped. |
| `FRONTMATTER*` / `ROUTING` | skill | Add `name` (kebab-case, matches the directory, at most 64 chars) and a `description` (at most 1024 chars) containing `Use when` and `Don't use`. |
| `SKILL_TOO_SHORT` / `SKILL_SIZE` | skill | Keep `SKILL.md` between 50 and 800 lines; move depth into `references/`. |
| `SKILL_MISSING_README` | skill | Add a non-empty `README.md` with provenance, cluster rationale, and directory contents. |
| `SKILL_PROVENANCE_IN_BODY` | skill | Move `Inspired by` / `Adapted from` / `Synthesizes ... from` / `Provenance` lines from `SKILL.md` into `README.md`. |
| `SKILL_MISSING_SKILL_MD` | skill | A non-hidden directory in a skills root lacks `SKILL.md`; add one or move the directory out. |
| `BROKEN_LINK` | skill | Fix the relative link in `SKILL.md` or `README.md`, or create the missing file. |
| `ADK_*` | adk | Add `__init__.py`, assign `root_agent`, and give public tools docstrings plus type hints. |
| `TF_*` | terraform | Add the standard root files; replace primitive roles and public principals with scoped bindings. |

---

## Stage 2: Blinded Multi-Persona Adversarial Evaluation

Once Stage 1 passes with `0` findings (and the project's native test suite passes), evaluate the artifact against its contract using **blinded context**:

### Step 2.1: Strip Authorial Reasoning (Extract Artifact + Contract Only)
Prepare an evaluation packet containing **only**:
1. **THE CONTRACT:** The user's original prompt, confirmed Statement of Intent, or spec acceptance criteria.
2. **THE ARTIFACT:** The exact file contents or `git diff` being verified.
**Do NOT include** your chain-of-thought, excuses, or claims that *"this works"*.

### Step 2.2: Evaluate Across 3 Independent Adversarial Personas
In environments supporting subagents, spawn a fresh-context reviewer subagent that receives only the evaluation packet from Step 2.1; otherwise execute a strict zero-justification pass across all three personas yourself. Detailed per-persona criteria live in [references/rubrics.md](references/rubrics.md):

1. **Persona 1 — Principal Cloud / Systems Architect:**
   - Checks failure modes, idempotency, security/trust boundaries, sovereignty (CMEK/VPC-SC/IAM), and module coupling.
2. **Persona 2 — Skeptical Staff QA & Security Engineer:**
   - Attempts to break the artifact with malformed inputs, numbering gaps, symlink/path traversal, race conditions, and XSS/injection payloads.
3. **Persona 3 — Target End-User / Customer Executive:**
   - Checks cognitive load, copy-paste CLI accuracy, typography hygiene, and whether every stated requirement in the Contract is demonstrably met.

### Step 2.3: Evidence-Backed Verdict Schema
Every criterion must be graded `PASS` or `FAIL` with an exact `file:line` or command-output citation:

```markdown
| Persona | Criterion | Verdict | Concrete Evidence (`file:line` or command output) |
| :--- | :--- | :---: | :--- |
| Architect | Least-privilege IAM & path safety | PASS | `sync_skills.py:<line>` resolves symlinks before comparison |
| Staff QA | Handles gaps in ADR numbering | PASS | `distill_session.py:<line>` uses `max(existing_nums) + 1` and `open("x")` |
| End-User | Narrative formatting compliance | PASS | `verify_static.py --mode prose` exited 0 (0 findings) |
| Staff QA | `--detach all` preserves user-owned links | FAIL | `test_scripts.py` has no case with a hand-made symlink; mutation left suite green |
```
Replace `<line>` with the real line number you inspected; never cite a line you did not open.
Any `FAIL` requires fixing the artifact and re-running Stage 1 + Stage 2 before declaring completion.

## Common Rationalizations

| Rationalization | Reality |
| :--- | :--- |
| "I just wrote the code carefully, I don't need to run `verify_static.py`" | Subtle syntax bugs (unquoted Mermaid parens, em-dashes in CLI flags, missing type hints) slip past visual inspection every time. |
| "I'll tell the reviewer subagent why I made these trade-offs" | Explaining your excuses primes the reviewer to agree with you. Pass only `ARTIFACT` + `CONTRACT`. |
| "Stage 1 passed, so the architecture is sound" | Static checks catch structural invariants; Stage 2 catches semantic gaps against the user's actual contract. |

## Red Flags

- Claiming completion without running `verify_static.py` on the modified artifact
- Passing authorial rationalizations or conclusions into a blinded review prompt
- Marking a rubric row `PASS` without a specific `file:line` or command output citation
- Ignoring a `[FAIL]` from `verify_static.py` as a "false positive" without fixing the underlying violation

## Verification

- [ ] `verify_static.py` executed in the appropriate `--mode` and exited `0`
- [ ] Project unit/integration tests executed and passed
- [ ] Blinded 3-persona evaluation completed with `PASS` and `file:line` evidence on all criteria
