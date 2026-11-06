---
name: documentation-and-adrs
description: >-
  Authors Markdown Architectural Decision Records (MADR), inline 'why-not-what'
  code comments, typed API docstrings, READMEs, and fact-preserving technical
  prose reviews. Use when recording significant architectural trade-offs,
  changing public APIs, onboarding engineers/agents, or editing technical docs.
  Don't use for authoring PRDs/TDDs/Executive Readouts or compiling multi-doc
  HTML portals (use sdlc-and-portal) or generating step-by-step workshop labs
  (use codelab).
---

# Documentation and ADRs

Code shows *what* was built; high-leverage documentation captures *why* it was built that way, *what constraints applied*, and *which alternatives were rejected*.

## When to Use

- Making or revising an architectural decision that is expensive to reverse (database choice, auth model, VPC-SC boundary, agent orchestration pattern, SDK selection)
- Adding or modifying a public API, CLI flag, or tool schema
- Onboarding engineers or AI agents (`README.md`, `AGENTS.md`)
- Reviewing and editing technical prose to improve clarity without losing factual precision
- **Don't use for:** authoring PRDs, Technical Design Docs, or Executive Readouts, or compiling standalone HTML presentation portals (use `sdlc-and-portal`), or authoring interactive workshop labs (use `codelab`).

---

## 1. Architecture Decision Records (ADRs)

### Step 1.1: Match the Repository's Existing Convention First
Before creating an ADR, inspect the repository for existing conventions:
- Check `docs/adr/`, `docs/decisions/`, `doc/adr/`, `.gemini/knowledge/ADRs/`, or `.adr-dir`.
- Continue the existing numbering sequence (`max(existing) + 1`) and filename pattern (`0004-title.md` or `ADR-0004-title.md`) — never restart at `0001` or overwrite an existing file.
- Use `distill_session.py --project . --new-adr "<Title>"` (from `continuous-alignment`) or [templates/madr-template.md](templates/madr-template.md).

### Step 1.2: MADR Structure & Lifecycle
```text
PROPOSED -> ACCEPTED -> (SUPERSEDED BY ADR-XXXX | DEPRECATED)
```
Every ADR must document:
1. **Status & Date:** Default new ADRs to `Proposed` until reviewed and approved by the human architect.
2. **Context and Problem Statement:** The technical, business, or sovereign compliance forces driving the decision.
3. **Decision Drivers:** Quantified constraints (e.g., p95 latency `< 300ms`, CMEK requirement, zero external SaaS egress).
4. **Considered Options (Minimum 2–3):** Genuine alternatives — never list strawmen just to make the chosen option look good.
5. **Pros, Cons & Rejection Rationale:** Why each rejected option failed the decision drivers.
6. **Consequences:** Both positive outcomes and negative trade-offs / operational follow-ups.

**Immutability Rule:** Never delete an older ADR when architecture changes. Mark the old ADR `Superseded by ADR-XXXX` and create a new ADR recording the new context.

---

## 2. Inline Code Documentation (Comment *Why*, Never *What*)

### When to Comment
Write comments only for non-obvious intent, algorithmic invariants, security constraints, or known platform gotchas:
```python
# BAD: Restates what the code visibly does
# Increment retry counter by 1
retries += 1

# GOOD: Explains non-obvious constraint and links to ADR
# Vertex AI Imagen :predict rejects requests when both seed and addWatermark=True
# are set simultaneously (returns HTTP 400). Disable watermark whenever a
# deterministic seed is requested. See ADR-0004.
if seed is not None:
    params["seed"] = seed
    params["addWatermark"] = False
```

### When NOT to Comment
- Self-explanatory code (`calculate_total(items)`) — rename variables/functions instead of explaining poor names.
- Commented-out code blocks — delete them; `git log` preserves history.
- Stale `TODO` comments for trivial checks you should implement right now.

---

## 3. Public API & Agent Tool Docstrings

Every public function, REST/gRPC endpoint, and **LLM Agent Tool Function** (ADK / MCP) must document its contract, parameters, return schema, and failure modes:
```python
def query_compliance_ledger(
    tenant_id: str,
    start_date: str,
    limit: int = 100,
) -> dict[str, list[dict[str, str]]]:
    """Fetch immutable audit ledger entries for a tenant within a date window.

    Args:
        tenant_id: Lowercase alphanumeric tenant identifier (e.g. 'emea-bank-01').
        start_date: Inclusive ISO-8601 start date ('YYYY-MM-DD').
        limit: Maximum rows to return (1..500, default 100).

    Returns:
        A dict containing 'entries' (list of ledger records) and 'next_page_token'.

    Raises:
        ValueError: If start_date is not valid ISO-8601 or limit is outside 1..500.
        PermissionError: If the caller lacks 'ledger.entries.list' on tenant_id.
    """
```

---

## 4. Fact-Preserving Technical Prose Review

When editing an ADR, README, or architecture document for clarity:
1. **Inventory Load-Bearing Facts First:** Mark all numbers, units, SLAs, CLI commands, file paths, version bounds, caveats, and unresolved risks.
2. **Strip Promotional Fluff, Not Caveats:** Replace stock AI introductions and marketing adjectives with direct technical statements, while strictly preserving every engineering qualifier (*"under read-heavy workloads"*, *"tested up to 10k QPS"*, *"requires VPC-SC ingress rule"*).
3. **Diff Against Source:** Compare the edited text against the original and run `python3 <skill-dir>/../verify/scripts/verify_static.py --mode prose <file>` (`<skill-dir>` is the directory containing this `SKILL.md`; sibling kit skills such as `verify` and `sdlc-and-portal` resolve as `<skill-dir>/../<skill>` because every harness links skills from the same `fde-agent-kit` clone.) to confirm zero lost qualifiers and clean formatting.

## Common Rationalizations

| Rationalization | Reality |
| :--- | :--- |
| "The code is self-documenting" | Code shows *what* runs today; it never shows *why* an alternative was rejected or what production trap it avoids. |
| "We'll write the ADR after the project ships" | Post-hoc ADRs forget the constraints and rejected alternatives that mattered at decision time. Write it when deciding. |
| "Nobody reads documentation" | AI agents read `AGENTS.md`, `SKILL.md`, and `docs/adr/` on every session. Missing docs cause agents to repeat mistakes. |
| "I'll polish the prose by making the guarantees sound stronger" | Removing qualifiers or caveats during copy-editing turns accurate engineering documentation into a false claim. |

## Red Flags

- Significant infrastructure, schema, or dependency choices committed with no ADR
- Creating `0001-*.md` in `docs/adr/` when the repository already stores ADRs in `docs/decisions/`
- Deleting or overwriting an existing ADR instead of superseding it
- Commented-out code blocks or comments that merely restate the next line of code
- Public functions or ADK tool functions missing parameter/return type annotations or docstrings
- Editing prose in a way that drops metric units, failure caveats, or security prerequisites

## Verification

- [ ] ADR matches the repository's existing directory and numbering sequence and uses [templates/madr-template.md](templates/madr-template.md)
- [ ] At least 2–3 genuine options with pros, cons, and rejection reasons are recorded
- [ ] Inline comments explain *why* (invariants/gotchas) with zero commented-out code left behind
- [ ] Prose passes `python3 <skill-dir>/../verify/scripts/verify_static.py --mode prose --profile technical <file>`
