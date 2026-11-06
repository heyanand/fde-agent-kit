---
name: continuous-alignment
description: >-
  Distills session transcripts into durable rules and MADR Architecture Decision
  Records, enforces the 200-line token budget on AGENTS.md/CLAUDE.md/GEMINI.md,
  and routes domain-specific lessons into path-scoped rules or skills. Use when
  finishing a complex debugging/implementation session, when the user corrects
  the agent repeatedly, or when rule files approach 200 lines. Don't use during
  the middle of active firefighting before root cause is verified.
---

# Continuous Alignment & Session Distillation (`continuous-alignment`)

Every repeated correction or non-obvious failure mode discovered during a session is a signal that the repository's harness (`AGENTS.md`, `docs/adr/`, or `skills/`) is missing a guardrail.

---

## 1. The 5-Step Session Distillation Loop

Run `<skill-dir>/scripts/distill_session.py` (where `<skill-dir>` is the directory containing this `SKILL.md`, e.g. `~/.gemini/config/skills/continuous-alignment` on Google Antigravity, `~/.claude/skills/continuous-alignment` on Claude Code, `~/.codex/skills/continuous-alignment` on Codex, or `<project>/.gemini/skills/continuous-alignment` when JIT-linked) at the conclusion of a substantial task:

### Step 1: Summarize Transcript & Failed Tool Calls
```bash
python3 <skill-dir>/scripts/distill_session.py --transcript path/to/transcript.jsonl
```
`distill_session.py` supports both **Google Antigravity** (`USER_INPUT`, `tool_calls`) and **Claude Code / Gemini CLI** (`role: "user"`, `tool_use`, `tool_result` with `is_error: true`) JSONL transcripts. It extracts:
- Follow-up user prompts (where the human steered, corrected, or overrode the agent).
- Failed commands and tool errors (candidate gotchas). For Google Antigravity, failures are read from the tool-result step (`status: ERROR` or a non-zero `exited with code N` for shell calls) and attributed back to the originating command. For Claude Code, each `tool_result` error is matched to its `tool_use` by `tool_use_id`, so the report names the failing command (`terraform apply: Error: 403 ...`).
- Lists are capped at 10 items (with a `... and N more` note); malformed JSONL lines are counted and reported, never fatal.

### Step 2: Classify Candidate Learnings (Durable Signal vs. Session Noise)
Filter out transient typos or one-off exploratory steps. Classify verified, durable insights into one of three destinations:

| Learning Type | Destination | Why |
| :--- | :--- | :--- |
| **Repo-Wide Invariant** (applies to >80% of tasks) | Root `AGENTS.md` (1–2 concise lines) | Loaded in every session; must earn its permanent token cost |
| **Domain / Path-Scoped Rule** (applies only to `terraform/`, `src/api/`, etc.) | `.agents/rules/<domain>.md` or `skills/<skill>/SKILL.md` | Progressive disclosure — keeps root `AGENTS.md` under 200 lines |
| **Architectural Trade-off** (why Option A beat Option B) | `docs/adr/NNNN-<slug>.md` (or `docs/decisions/`) | Prevents future sessions from re-litigating settled decisions |

### Step 3: Scaffold & Link New ADRs Safely
```bash
python3 <skill-dir>/scripts/distill_session.py \
  --project . \
  --new-adr "Use VPC-SC Ingress Rules for Partner Webhooks" \
  --status Proposed
```
Safety guarantees built into `distill_session.py --new-adr`:
- Auto-detects existing ADR directories (`docs/adr/`, `docs/decisions/`, `doc/adr/`, `.gemini/knowledge/ADRs/`) before defaulting to `docs/adr/`.
- Computes `next_num = max(existing_numbers, default=0) + 1` (safe across numbering gaps) and opens the file with exclusive creation (`open("x")`) so an existing ADR can **never** be overwritten.
- Automatically appends the new ADR link to `<adr-dir>/README.md`.

### Step 4: Enforce the 200-Line `AGENTS.md` Token Budget
```bash
python3 <skill-dir>/scripts/distill_session.py --check-budget .
```
- Audits `AGENTS.md`, `GEMINI.md`, `CLAUDE.md`, and `rules/AGENTS.md` (deduplicating symlinks via `Path.resolve()`).
- Exits with code `1` (`[OVER_BUDGET]`) if any file exceeds **200 lines**; prints `[NEAR_BUDGET]` (exit `0`) between 181 and 200 lines as an early extraction signal.
- Running the script with no flags prints usage and exits `2`; a missing `--project` / `--check-budget` directory or an empty `--new-adr` title exits `1` with an actionable error.
- When `AGENTS.md` exceeds 180 lines, extract domain-specific sections into `.agents/rules/<domain>.md` or `skills/<name>/SKILL.md` and replace them with a one-line routing pointer.

### Step 5: Optional Harness Hook Integration
To run the budget check automatically at the end of every Claude Code / Gemini CLI session, configure a non-blocking `Stop` hook in `.claude/settings.json`:
```json
{
  "hooks": {
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/skills/continuous-alignment/scripts/distill_session.py --check-budget ."
          }
        ]
      }
    ]
  }
}
```

## Common Rationalizations

| Rationalization | Reality |
| :--- | :--- |
| "I'll just append 30 lines of Terraform rules to root `AGENTS.md`" | Root `AGENTS.md` is paid on every single turn (including Python and docs tasks). Put domain rules in `skills/` or `.agents/rules/`. |
| "I'll record this hypothesis as a rule right now while debugging" | Never record unverified hypotheses as permanent rules. Wait until the root cause and fix are verified. |
| "I'll manually create `0002-my-adr.md` with `write_file(Overwrite=True)`" | Manual numbering on gapped directories overwrites existing ADRs. Use `distill_session.py --new-adr`. |

## Red Flags

- Root `AGENTS.md`, `CLAUDE.md`, or `GEMINI.md` exceeding 200 lines (`[OVER_BUDGET]`)
- Recording speculative or unverified debugging theories into permanent rule files
- Duplicating the full content of `AGENTS.md` into `CLAUDE.md` and `GEMINI.md` instead of symlinking (`sync_skills.py --sync-rules`)
- Creating ADRs with `Status: Accepted` before the human architect has reviewed the trade-off

## Verification

- [ ] `python3 <skill-dir>/scripts/distill_session.py --check-budget .` exits `0` (`<= 200` lines per rule file)
- [ ] Any newly created ADR uses `max(existing) + 1`, defaults to `Proposed`, and is indexed in `<adr-dir>/README.md`
- [ ] Domain-specific workflows are placed in `skills/` or `.agents/rules/` rather than bloating root `AGENTS.md`
