# Definition of Done

A standing, project-wide bar that every change must clear before it counts as done. Unlike acceptance criteria (which vary per task and answer "did we build the right thing?"), the Definition of Done is fixed and answers "is this finished to our standard?".

## Definition of Done vs. Acceptance Criteria

| Dimension | Acceptance Criteria | Definition of Done |
| :--- | :--- | :--- |
| **Scope** | Specific to one task or milestone | Applies to every increment |
| **Answers** | "Did we build *this thing*?" | "Is it *ready to ship*?" |
| **Example** | "User can compile a multi-doc HTML portal" | "Tests pass, `verify_static.py` exits 0, no regressions, docs updated" |

## The Standing Checklist

### 1. Correctness
- [ ] All acceptance criteria for the task/milestone are met
- [ ] Code runs and behaves as intended, verified at runtime (not just compiled or type-checked)
- [ ] New behavior is covered by automated tests that fail without the change and pass with it
- [ ] Existing tests pass with zero regressions
- [ ] Edge cases, malformed inputs, and error paths are handled explicitly

### 2. Quality & Simplicity
- [ ] Code reveals intent through naming and structure; comments explain *why*, not *what*
- [ ] Zero mocks, `TODO`, `FIXME`, `NotImplementedError`, or placeholder stubs left in production paths
- [ ] Changes are strictly scoped to the task; no unrelated refactors snuck in
- [ ] Static verification (`verify_static.py`) and project linters pass with 0 findings

### 3. Security & Sovereignty
- [ ] External and LLM inputs validated at boundaries; no secrets in code, URLs, or logs
- [ ] Cloud/Terraform changes pass `verify_static.py --mode terraform` (CMEK, VPC-SC, least-privilege IAM)

### 4. Documentation & Handoff
- [ ] Public interfaces, CLI flags, and architectural decisions (ADRs) are documented in timeless present tense
- [ ] Multi-file changes end with a `CHANGES MADE / THINGS INTENTIONALLY UNTOUCHED / POTENTIAL CONCERNS` summary
