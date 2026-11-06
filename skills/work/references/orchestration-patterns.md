# Orchestration Patterns

Reference catalog of multi-agent orchestration patterns endorsed by `fde-agent-kit`, adapted from `addyosmani/agent-skills`.

The governing rule: **the main session (or user) is the orchestrator. Specialist subagents do not spawn nested subagents.**

## Endorsed Patterns

### 1. Direct Invocation (Default)
Single perspective on a single artifact in the current context. Always prefer this when the task fits comfortably in one turn and requires no context isolation.

### 2. Parallel Fan-Out with Merge (`[PARALLEL]` Milestones)
Multiple independent subagents operate concurrently on disjoint slices or review lenses, and the main orchestrator merges their outputs.
- **When to use in `work`:** Two milestones in the DAG have no shared file mutations and no data dependency.
- **Isolation requirement:** Each parallel coding subagent must work in its own `git worktree add ../<repo>-<milestone-id> -b feat/<milestone-id>` so file writes and test runs never collide.
- **Validation checklist before fanning out:**
  - [ ] Are the file sets touched by each milestone completely disjoint?
  - [ ] Can all subagents run simultaneously without ordering dependencies?
  - [ ] Will the merge and verification step fit cleanly in the main context?

### 3. Research Isolation (Context Preservation)
When a task requires reading dozens of files or large logs that would pollute the main implementation context, delegate to a read-only research subagent that returns a compact digest (<500 words) with exact `file:line` citations.

### 4. Adversarial Fresh-Context Review (`verify` / `doubt-driven-development`)
When verifying a completed milestone or high-stakes architectural claim, pass only the **ARTIFACT** (diff/file) and **CONTRACT** (spec acceptance criteria) to a fresh-context reviewer without your authorial rationalizations.

## Anti-Patterns to Avoid

1. **Meta-Router Subagents:** Never spawn a subagent whose only job is to decide which other subagent to call.
2. **Subagent-Calls-Subagent Chains:** Subagents must never spawn nested subagents; keep orchestration depth at most 1.
3. **Shared-Working-Tree Parallel Edits:** Never run two write-enabled subagents concurrently in the same working directory without `git worktree` isolation.
4. **Paraphrasing Pipelines:** Do not chain sequential subagents that summarize each other's prose; pass concrete artifacts on disk (`docs/specs/<feature>.md`, `tasks/handoff.md`, git commits).
