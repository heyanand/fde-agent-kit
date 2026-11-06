---
name: work
description: >-
  Executes a specification's Milestone DAG (M1..Mn) autonomously in verified
  vertical slices with zero-mock gates, git worktree isolation for parallel
  milestones, 3-strike failure escalation, and persistent tasks/handoff.md
  state. Use when implementing an approved spec from grill-and-spec or resuming
  a multi-session build. Don't use before a written spec or task plan exists
  (run grill-and-spec first).
---

# Autonomous Milestone DAG Execution Engine (`work`)

See [references/orchestration-patterns.md](references/orchestration-patterns.md) for the rules governing direct execution vs. parallel subagent fan-out.

---

## 1. Pre-Flight & Session Resume Protocol

Before writing a single line of implementation code:
1. **Check for Active State (`tasks/handoff.md` & `tasks/todo.md`):**
   - If `tasks/handoff.md` exists, read it first to identify completed milestones, the last verified commit SHA, active blockers, and the next ready milestone.
   - Run `git status` and `git log -n 5 --oneline` to confirm the working tree matches the recorded handoff state.
2. **Locate the Approved Spec:**
   - Read `docs/specs/<feature>.md` or `tasks/plan.md`. If no spec or milestone list exists for non-trivial work, stop and run `grill-and-spec` first.
3. **Initialize `tasks/handoff.md`:**
   - If starting fresh, copy [templates/handoff.md](templates/handoff.md) to `tasks/handoff.md` and populate the Milestone DAG status table.

---

## 2. The Per-Milestone Execution Loop

Execute ready milestones (whose dependencies are all `[x] DONE`) one vertical slice at a time:

```text
Select Ready Milestone -> Implement (Zero Mocks) -> Run Verification Command -> Static Gate -> Atomic Commit -> Update handoff.md
```

### Step 2.1: Strict Scope & Zero-Mock Implementation
- Touch **only** the files listed in the milestone's scope (`1–5 files`).
- **Zero-Mock Production Rule:** Never leave `TODO`, `FIXME`, `NotImplementedError`, `pass # placeholder`, or hardcoded mock payloads in production code paths. Before committing, run:
  ```bash
  { git diff --name-only --diff-filter=d HEAD; git ls-files --others --exclude-standard; } \
    | sort -u | xargs -r grep -nE "(TODO|FIXME|NotImplementedError|HACK|XXX)" || true
  ```
  Any match in production source files blocks milestone completion.

### Step 2.2: Deterministic Verification & 3-Strike Escalation Protocol
Run the milestone's declared verification command (unit tests, integration tests, `verify_static.py`).
- **If verification passes:** Proceed to Step 2.3.
- **If verification fails (The 3-Strike Rule):**
  1. **Strike 1:** Diagnose root cause (using `debugging-and-error-recovery`), apply targeted fix, re-run verification.
  2. **Strike 2:** Re-read the spec contract and surrounding callers, isolate the minimal failing case, apply fix, re-run verification.
  3. **Strike 3:** If the milestone still fails after 3 attempts, **STOP**. Do NOT thrash, delete tests, or pile hacks onto broken state. Park the uncommitted milestone edits without destroying them (`git stash push -u -m "wip/<milestone>-strike3"` or commit to a `wip/<milestone>` branch; never `git checkout -- .`, which silently discards unrelated work), record the exact failure output and attempted fixes in `tasks/handoff.md` under `Active Blockers`, and escalate to the human.

### Step 2.3: Atomic Save-Point Commit & Handoff Update
Once tests and `verify_static.py` exit `0`:
1. Stage and secret-scan the diff (`git diff --staged -i -G'password|secret|api_key|token' --name-only`).
2. Create an atomic Conventional Commit (`feat(m1): ...`) explaining *why*.
3. Update `tasks/handoff.md` (and `tasks/todo.md`) with the new commit SHA, verification output summary, and next ready milestone.

---

## 3. Parallel Milestone Execution (`[PARALLEL]` Tag)

When two or more ready milestones are explicitly marked `[PARALLEL]` in the spec and touch **completely disjoint file sets**:
1. Create an isolated git worktree per parallel milestone (never run concurrent write agents in the same directory):
   ```bash
   git worktree add ../<repo>-m2 -b feat/m2
   git worktree add ../<repo>-m3 -b feat/m3
   ```
2. Dispatch one subagent per worktree (see [references/orchestration-patterns.md](references/orchestration-patterns.md)).
3. Once each subagent passes its milestone verification command, merge the branches back into the main working branch sequentially, run the full test suite, and remove the temporary worktrees (`git worktree remove ../<repo>-m2`).

## Common Rationalizations

| Rationalization | Reality |
| :--- | :--- |
| "I'll implement Milestones 1, 2, and 3 together before running tests" | Batching milestones destroys fault isolation. When tests fail across 15 modified files, you waste hours untangling why. |
| "I'll stub out the parser with a `TODO` and finish it in Milestone 4" | Unfinished stubs masquerading as `[x] DONE` milestones corrupt downstream tasks. Every slice must work end-to-end. |
| "The test failed 3 times, I'll relax the assertion so I can keep moving" | Weakening a test to force a green build hides a real bug. Follow the 3-Strike Rule and escalate. |
| "I don't need to update `tasks/handoff.md` until the end of the session" | Context compaction or timeouts can happen on any turn. Update `tasks/handoff.md` at every milestone commit boundary. |

## Red Flags

- Coding across multiple milestones without committing or running verification between them
- Leaving `TODO`, `FIXME`, `NotImplementedError`, or mocked return values in production code
- Modifying or deleting a failing test without proving the test itself contradicted the spec
- Looping 4+ times on the same failing milestone without stopping to escalate
- Running parallel write-enabled subagents in the same working tree without `git worktree` isolation

## Verification

- [ ] Every `[x] DONE` milestone has a dedicated atomic git commit and passing verification command output
- [ ] Zero `TODO` / `FIXME` / `NotImplementedError` markers exist in modified production files
- [ ] `tasks/handoff.md` accurately reflects the current git `HEAD` SHA and remaining DAG state
- [ ] Session concludes with the 3-part Scope Summary (`CHANGES MADE`, `THINGS INTENTIONALLY UNTOUCHED`, `POTENTIAL CONCERNS`)
