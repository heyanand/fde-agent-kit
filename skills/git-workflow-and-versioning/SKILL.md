---
name: git-workflow-and-versioning
description: >-
  Enforces trunk-based development, atomic save-point commits, splitting messy
  working trees into logical commits, git worktrees for parallel agent streams,
  pre-commit secret scanning, Semantic Versioning, and human-readable
  changelogs. Use when making any code change, committing, branching, resolving
  merge conflicts, opening PRs, or cutting releases in a Git repository. Don't
  use for non-Git version control systems, for reviewing code quality (use
  code-review-and-quality), or for architecture brainstorming.
---

# Git Workflow and Versioning

Treat commits as save points, branches as short-lived sandboxes, and git history as architectural documentation.

## Core Principles

### 1. Trunk-Based Development & Save-Point Commits
Keep `main` always deployable. Work in short-lived branches (`feat/<slug>`, `fix/<slug>`, `refactor/<slug>`, `docs/<slug>`, `chore/<slug>`) that merge within 1–3 days.
Follow the **Save-Point Pattern** on every slice:
```text
Implement vertical slice -> Run tests & verify_static.py -> Stage & scan diff -> Commit -> Next slice
```
Never accumulate massive uncommitted diffs across multiple features. If an experiment goes off the rails, roll back to the last verified save point with the narrowest command that works:
```bash
# Discard edits to specific files only
git restore -- <file> [<file> ...]

# Park the whole experiment instead of deleting it (recover later with `git stash pop`)
git stash push --include-untracked -m "experiment: <slug>"
```
Avoid `git reset --hard` and `git clean -fd` unless the user explicitly asks for them: both permanently destroy every uncommitted change in the tree, including edits made by other agents sharing the workspace.

### 2. Atomic Commits & Splitting Messy Working Trees
Each commit must do **one logical thing** (~100–300 lines max). Never mix formatting or refactoring with behavioral changes.

**When asked to commit a messy working tree containing multiple concerns:**
1. Run `git status` and `git diff` to inventory all modified and untracked files.
2. Group changes into ordered, self-contained logical commits:
   - Commit 1: Pure refactoring or foundational helper extraction
   - Commit 2: Core feature or bug fix + its unit/regression tests
   - Commit 3: Documentation, ADR, or configuration updates
3. Stage file-by-file (`git add <specific-paths>`) or hunk-by-hunk (`git add -p`), run tests to ensure the tree is green at each commit boundary, and commit each slice separately.

### 3. Conventional Commit Messages (Explain *Why*, Not *What*)
```text
<type>(<optional-scope>): <short imperative summary under 72 chars>

<body explaining WHY the change was made, key trade-offs, and constraints
not obvious from reading the diff>
```
Allowed types: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`, `perf`, `build`, `ci`, `revert`, `security`.
Mark breaking changes with `!` after the type/scope (`feat(cli)!: rename --pack to --preset`) and a `BREAKING CHANGE: <migration note>` footer; these map directly to a SemVer `MAJOR` bump.

- **Bad:** `update sync_skills.py` or `fix bug`.
- **Good:** `fix(adr): compute next ADR number from max prefix and use exclusive file creation`.

Pass multi-line messages through a file or repeated `-m` flags so shells never mangle quotes or backticks:
```bash
git commit -m "fix(sync): never clobber an existing GEMINI.md.bak" \
  -m "Earlier runs overwrote the first backup. Timestamped suffixes keep every user copy."
```

---

## Pre-Commit Secret & Hygiene Gate

Run these checks before **every** commit:
```bash
# 1. Inspect staged changes
git diff --staged --stat

# 2. Scan staged diff for secrets (prints matching filenames; empty output = clean)
git diff --staged -i -G'(password|secret|api[_-]?key|token|PRIVATE KEY|AKIA[0-9A-Z]{16}|ghp_[0-9A-Za-z]{36}|AIza[0-9A-Za-z_-]{35})' --name-only

# 3. Verify no build artifacts, .env files, or local overrides are staged
git status --short
```
- The scan is case-insensitive and intentionally noisy (`token` matches `tokenizer`). Inspect each listed file with `git diff --staged -- <file>` rather than dismissing the whole list.
- Keep `-` as the last character inside a bracket expression (`[0-9A-Za-z_-]`); a mid-bracket hyphen such as `[A-Za-z-_]` is an invalid range and makes Git abort with `fatal: invalid regex`.
- If a listed match is a real credential, unstage it (`git restore --staged -- <file>`), move the value to an environment variable or secret manager, and re-run the scan.
**If a secret ever reaches a remote repository, rotate/revoke the credential immediately** — rewriting git history alone does not remediate a leaked key.

---

## Git Worktrees for Parallel Agent Execution

When running multiple agents or parallel milestone slices (`[PARALLEL]` in `work`), isolate each stream in its own git worktree so working directories and test runs never collide:
```bash
# Create an isolated worktree and branch for a parallel milestone
git worktree add ../<repo>-m2 -b feat/m2-portal-compiler

# List active worktrees and their branches
git worktree list

# After verification and merge back to main, remove the worktree
git worktree remove ../<repo>-m2
```
`git worktree remove` refuses to delete a worktree with uncommitted changes. Treat that refusal as a signal to commit or stash the stream's work; do not add `--force` without checking `git -C ../<repo>-m2 status` first.

---

## Post-Modification Scope Summary

After completing any multi-file change, always output this 3-part scope summary:
```text
CHANGES MADE:
- [file]: [concise description of what changed and why]

THINGS INTENTIONALLY UNTOUCHED:
- [adjacent file/module]: [why it was left alone to preserve scope discipline]

POTENTIAL CONCERNS:
- [any edge case, migration impact, or assumption the human should verify]
```

---

## Semantic Versioning & Consumer-Facing Changelogs

For any repository, CLI, or skill kit with downstream consumers:
- **`MAJOR` (`X.0.0`):** Incompatible API, CLI flag, or schema change requiring consumer updates (when in doubt, treat behavioral changes observable by callers as `MAJOR` per Hyrum's Law).
- **`MINOR` (`0.X.0`):** Backward-compatible new skill, feature, or CLI flag.
- **`PATCH` (`0.0.X`):** Backward-compatible bug fix or documentation improvement.
- **Tag as Source of Truth:** Create annotated tags (`git tag -a v1.2.0 -m "Release v1.2.0"`) and derive package versions from the tag.
- **Curated Changelog (`CHANGELOG.md`):** Maintain a human-written changelog grouped by `Added`, `Changed`, `Fixed`, `Deprecated`, `Removed`, and `Security` — written at the time of the change, never dumped raw from `git log`.

## Common Rationalizations

| Rationalization | Reality |
| :--- | :--- |
| "I'll commit everything when the whole feature is done" | Giant commits are impossible to bisect, review, or revert cleanly. Commit each verified vertical slice. |
| "The commit message doesn't matter" | Commit messages are the primary archaeological record for future engineers and AI agents. Explain *why*. |
| "I'll combine the refactor and feature in one commit" | Mixing refactors with behavioral changes hides bugs inside noisy diffs. Split them into separate commits. |
| "It's a tiny fix, so it's definitely a PATCH bump" | If callers relied on the previous behavior, changing it is a breaking (`MAJOR`) change regardless of line count. |
| "We'll generate the changelog from git log at release time" | Raw commit logs bury user impact under internal mechanics. Update `CHANGELOG.md` alongside the change. |

## Red Flags

- Uncommitted diffs spanning 10+ files across unrelated subsystems
- Commit messages like `"wip"`, `"fix"`, `"update"`, or `"misc changes"`
- Using `git add .` or `git add -A` blindly without checking `git status` and secret-scanning `git diff --staged`
- Committing `.env`, `*.pem`, `skills.manifest.local.json`, `__pycache__/`, or build outputs
- Running parallel write-enabled agents in the same working tree without `git worktree` isolation
- Force-pushing (`git push --force`) to `main` or shared branches (use `--force-with-lease` on your own feature branch only)
- Running `git reset --hard` or `git clean -fd` in a workspace shared with other agents or uncommitted user edits
- Omitting the `CHANGES MADE / THINGS INTENTIONALLY UNTOUCHED / POTENTIAL CONCERNS` summary after multi-file edits

## Verification

- [ ] Each commit represents one logical, tested change with a Conventional Commit message explaining *why*
- [ ] Staged diff passed the secret-scanning regex check with zero matches
- [ ] `.gitignore` excludes secrets, local corp overlays, and build artifacts
- [ ] Multi-file edits conclude with the 3-part Scope Summary
- [ ] User-facing changes include an updated `CHANGELOG.md` entry and appropriate SemVer classification
