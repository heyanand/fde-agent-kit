# Milestone Handoff Checkpoint (`tasks/handoff.md`)

- **Last Updated:** YYYY-MM-DD HH:MM
- **Active Spec:** `docs/specs/<feature>.md` (or `tasks/plan.md`)
- **Current Milestone:** `M2`
- **Last Verified Commit:** `<sha>`

## 0. Milestone DAG Status

| Milestone | Title | Depends On | Tag | Status | Commit |
| :--- | :--- | :--- | :--- | :--- | :--- |
| M1 | [Title] | - | - | [x] DONE | `<sha>` |
| M2 | [Title] | M1 | - | [ ] IN PROGRESS | - |
| M3 | [Title] | M1 | [PARALLEL] | [ ] READY | - |
| M4 | [Title] | M2, M3 | - | [ ] BLOCKED | - |

## 1. Completed Milestones
- [x] **M1: [Title]**
  - **Commit:** `<sha>`
  - **Verification Output:** `[Command & PASS summary]`

## 2. In-Progress / Next Milestone
- [ ] **M2: [Title]** (`Depends on: M1`)
  - **Target Files:** `...`
  - **Remaining Steps:** `...`
  - **Verify Command:** `...`
  - **Strike Count:** `0/3`

## 3. Active Blockers
- [None, or: **M2 failed Strike 3.** Exact failing command + output excerpt, the three attempted fixes, where the WIP edits are parked (`git stash list` entry or `wip/m2` branch), and the decision needed from the human.]

## 4. Discovered Constraints & Decisions
- [Any non-obvious invariant discovered during execution that downstream milestones must respect; link an ADR in `docs/adr/` for architectural trade-offs]
