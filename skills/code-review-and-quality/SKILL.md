---
name: code-review-and-quality
description: >-
  Conducts a rigorous 5-axis code review (Correctness, Readability & Simplicity,
  Architecture, Security, Performance) with severity labels, structural
  remedies, test mutation checks, and dependency discipline. Use when reviewing
  any PR or diff before merge, after completing a feature or bug fix, or when
  evaluating code written by yourself, another agent, or a human. Don't use for
  early-stage feature ideation or specification writing before code exists (use
  idea-refine or grill-and-spec), for prose or comment de-slopping (use unslop),
  or as the final completion gate (use verify).
---

# Code Review and Quality

Every change gets reviewed across five axes before merge — no exceptions.

**The Approval Standard:** Approve a change when it definitely improves overall code health, even if it isn't perfect. Do not rubber-stamp (`LGTM` without evidence helps no one), and do not soften real production bugs into polite suggestions.

---

## The Five-Axis Review

### 1. Correctness
- Does the implementation match the spec and task acceptance criteria?
- Are edge cases handled (`None`/`null`, empty collections, boundary numbers, non-ASCII strings, numbering gaps)?
- Are error paths handled explicitly (no bare `except: pass` or swallowed HTTP errors)?
- Do tests verify behavior at module boundaries rather than tautological mock assertions?

### 2. Readability & Simplicity
- Are names descriptive and consistent with repository conventions?
- Could this be written in significantly fewer lines without losing clarity?
- Are abstractions earning their complexity (wait until the 3rd use case before generalizing)?
- Are there dead code artifacts (`_unused`, commented-out blocks, backwards-compat shims for internal callers)?
- Is a new conditional bolted onto an unrelated flow instead of extracted into a clear policy or helper?

### 3. Architecture
- Does the change maintain clean module boundaries with one-way dependency flow?
- **Does a refactor reduce complexity or merely relocate it?** Count the concepts a reader must hold in mind. If a "cleaner" version leaves that count unchanged, prefer a restructuring where whole branches or layers disappear.
- Is feature-specific logic leaking into a shared utility module?
- Are type boundaries explicit (no gratuitous `Any` / `unknown` / silent fallback masking a broken invariant)?

### 4. Security
See [references/security-checklist.md](references/security-checklist.md) for the full OWASP Web + LLM Top 10 checklist:
- Are external inputs, CLI arguments, file paths, and **LLM outputs** validated and sanitized at boundaries?
- Are secrets kept out of source code, logs, and URL query strings (use HTTP headers like `x-goog-api-key`, never `?key=`)?
- Are destructive or mutating file operations guarded by `Path.resolve()`, allowlisted roots, and exclusive creation (`open(..., "x")`)?
- Are SQL/BigQuery queries parameterized and HTML/JSON `<script>` payloads escaped (`</` -> `<\/`)?

### 5. Performance
See [references/performance-checklist.md](references/performance-checklist.md):
- Any N+1 queries, unbounded loops, or unpaginated list fetches?
- Any blocking synchronous I/O inside `async def` functions?
- Are SDK clients and connection pools reused per process rather than recreated per request?

---

## Structural Remedies (Propose the Move, Not Just the Problem)

When flagging a structural issue, always name the concrete remedy:
- **Replace a chain of conditionals** with a typed dispatch table or data structure.
- **Collapse duplicate branches** into a single normalized flow.
- **Separate orchestration from pure domain logic** so business rules can be unit-tested without I/O.
- **Move feature-specific logic** out of shared utilities into the owning package.
- **Reuse the canonical helper** instead of introducing a near-duplicate.
- **Delete a pass-through wrapper** that adds indirection without narrowing the contract.

---

## Step-by-Step Review Protocol

### Step 1: Understand Context & Sizing
- Target diff size: `~100 lines` (ideal), `~300 lines` (acceptable single logical change), `>1000 lines` (request split before reviewing).
- Watch total file size (~800–1000 lines): if a diff pushes an already large file past healthy bounds, recommend decomposing first.
- Never mix refactoring with feature work in the same change.

### Step 2: Review Tests First & Run the Mutation Check
Inspect tests before reading implementation code. Verify that tests catch real regressions by performing a **Mutation Check**:
1. Mentally or locally invert one condition added by the change (drop a `not`, swap `and`/`or`, change `<` to `<=`).
2. Run the focused test suite.
3. If the suite stays green, flag the missing test case as a required finding.
4. Revert the mutation (`git restore -- <file>` or `git stash drop` if you stashed the original) and confirm `git diff` is back to the author's change before writing the report.

Edge cases:
- **No tests in the diff:** Treat missing coverage for new behavior as a **Required:** finding, not a **Nit:**.
- **Cannot run tests locally** (missing credentials, cloud-only dependencies): Say so explicitly in the verdict and perform the mutation check mentally against the assertions; never imply the suite was executed.

### Step 3: Categorize Findings by Severity & Leverage
Lead with highest-leverage issues (Correctness and Security first, then Architecture, then Readability). Label every finding:

| Prefix | Merge Impact | Typical Findings |
| :--- | :--- | :--- |
| **Critical:** | Blocks merge immediately | Security vulnerability, data loss, broken functionality, or credential leak |
| *(no prefix)* / **Required:** | Must be fixed before merge | Logic bug, missing test coverage, architectural violation, or broken edge case |
| **Optional:** / **Consider:** | Non-blocking; author decides | Cleaner abstraction or edge-case hardening worth considering |
| **Nit:** | Non-blocking polish | Formatting, naming preference, or minor wording tweak |
| **FYI:** | No action in this change | Future consideration or context for the author |

### Step 4: Dead Code & Dependency Hygiene
- **Dead Code:** Explicitly list any newly unreachable functions, constants, or imports and ask before deleting if external callers might exist.
- **Dependency Upgrades:** Require one dependency upgrade per change (no bulk "bump deps" PRs without changelog review), verify lockfile consistency, and check reachability of security advisories.

### Step 5: Write the Review Report

Cite `file:line` for every finding, state the concrete failure, and name the remedy. End with an explicit verdict:

```markdown
## Review: feat(sync): add --detach all

**Verdict:** Changes requested (1 Critical, 1 Required, 1 Nit)

- **Critical:** `skills/sync/scripts/sync_skills.py:452` - `--detach all` unlinks every symlink in
  `.gemini/skills/`, including links the user created by hand. Restrict removal to links whose
  target resolves into the kit's `skills/` dir or upstream cache.
- **Required:** `tests/test_scripts.py` - no test covers `--detach all` next to a user-owned link.
  Mutation check: deleting the ownership guard leaves the suite green.
- **Nit:** `sync_skills.py:447` - `invalid` is vague; rename to `invalid_names`.

**Evidence:** `python3 -m unittest discover -s tests` -> 36 passed; `verify_static.py --mode skill skills/` -> 0 findings.
```

**When the change is clean,** say so plainly and still cite evidence (`Verdict: Approve. Tests: 36 passed; mutation check on line 452 turned the suite red.`). An approval without evidence is a rubber stamp.

---

## Common Rationalizations

| Rationalization | Reality |
| :--- | :--- |
| "It works, that's good enough" | Working code that is insecure, unreadable, or architecturally tangled compounds into production incidents. |
| "I wrote it, so I know it's correct" | Authors are blind to their own unstated assumptions. Every change needs an adversarial pass. |
| "We'll clean it up in a follow-up PR" | Follow-up cleanup rarely happens. Require structural hygiene before merge unless mitigating a live outage. |
| "AI-generated code looks clean, so it's fine" | LLM output is maximally plausible even when subtly wrong. Scrutinize edge cases and error handling harder. |
| "The tests pass, so it's good" | Passing tests prove nothing if assertions only check the happy path or mock out the bug. Run the mutation check. |
| "The refactor makes it cleaner" | Moving complexity between files is not reducing it. Look for the design where branches and state disappear. |
| "It's just a version bump" | A dependency bump is third-party code execution you didn't write. Review the changelog and lockfile diff. |

## Red Flags

- Merging or approving with `"LGTM"` and zero file:line evidence
- Reviewing implementation without reading or running the tests
- Missing severity labels on review comments
- Security-sensitive changes (auth, IAM, HTML/script generation, file deletion, subprocess calls) reviewed without [references/security-checklist.md](references/security-checklist.md)
- A refactor that relocates complexity without reducing the number of concepts a reader must hold
- Feature-specific logic added to a shared module or a near-duplicate of an existing helper
- Silent `except Exception: pass` or fallback values that hide broken invariants
- Bulk dependency upgrades with no changelog inspection or lockfile verification

## Verification

- [ ] All **Critical:** and **Required:** findings are resolved
- [ ] Mutation check confirmed that tests fail when the core logic is inverted
- [ ] [references/security-checklist.md](references/security-checklist.md) and [references/performance-checklist.md](references/performance-checklist.md) were applied to relevant paths
- [ ] Dead code and unused imports introduced by the change are removed
- [ ] Verification evidence (test output, `verify_static.py`, build status) is recorded in the review verdict
