---
name: grill-and-spec
description: >-
  Conducts a Socratic pre-flight interview (one question at a time with an
  attached hypothesis and confidence score) and compiles a verified technical
  specification and milestone DAG before coding. Use when starting a new
  feature, system architecture, or customer PoC where requirements, boundaries,
  or task decomposition are not yet locked. Don't use for vague brainstorming
  where the user has not chosen a concept yet (use idea-refine) or for
  single-line bug fixes with obvious scope.
---

# Grill and Spec (Socratic Interview -> Capability Map -> Spec & Milestone DAG)

Conducts a structured Socratic pre-flight interview, decomposes multi-capability initiatives into a Capability Map, and compiles a verified technical specification and vertical-slice Milestone DAG before coding begins.

## When to Use

- Starting a new project, customer PoC, cloud architecture, or multi-file feature
- Requirements are missing who benefits, what success looks like (with numbers), or what the binding constraint is
- A large requirement spans multiple independently testable capabilities that need a Capability Map
- **Don't use for:** open-ended brainstorming across many concepts (use `idea-refine`), or trivial single-file fixes.

---

## Stage 1: The Socratic Pre-Flight ("Grill Me")

Never dump a 10-question questionnaire or silently invent requirements.

### Step 1.1: State Hypothesis + Confidence Score
Write a one-sentence hypothesis of what the user actually wants, plus an honest confidence score (`0%–100%`). Whenever confidence is `<70%`, state what is missing on the same line:
```text
HYPOTHESIS: You want a VPC-SC compliant Vertex AI agent gateway for EU customer data, with Terraform deployment modules.
CONFIDENCE: ~45% -- missing: target compliance regime, authentication identity flow, and latency/throughput SLOs.
```

### Step 1.2: Ask One Question at a Time with an Attached Guess
```text
Q: <one focused, high-leverage question>
GUESS: <your concrete default hypothesis and why you inferred it>
```
Wait for the user's response before asking the next question.

### Step 1.3: Probe "Want vs. Should Want" & FDE Production Lenses
When an answer uses buzzwords ("make it scalable", "clean microservices", "multi-agent swarm"), ask:
> *"If you didn't have to justify this architecture to anyone, what is the simplest outcome you actually need?"*

For Google Cloud / Enterprise AI workloads, explicitly probe (full question bank in [references/fde-discovery-lenses.md](references/fde-discovery-lenses.md)):
1. **Data Residency & Sovereignty:** VPC Service Controls (VPC-SC), CMEK (`google_kms_crypto_key`), Assured Workloads region constraints, and zero public IPs.
2. **Identity & Least Privilege:** Workload Identity Federation (WIF), dedicated service accounts per workload, and resource-scoped IAM bindings.
3. **Scale, Latency & Cost Ceiling:** Expected QPS, p95 latency target, token/slot budget, and batch vs. streaming boundaries.
4. **Failure Modes & Rollback:** Circuit breakers, dead-letter handling, idempotency keys, and database/Terraform rollback strategy.

### Step 1.4: The 95% Confidence Restate & Explicit Gate
Once you can predict the user's answers to the next three questions (`>=95%` confidence), present the **Confirmed Statement of Intent**:
```text
Here is what I now understand we are building:
- Outcome:      <one line>
- User:         <one line -- who benefits>
- Why now:      <one line -- trigger>
- Success:      <one line -- measurable acceptance target>
- Constraint:   <one line -- binding technical/compliance limit>
- Out of scope: <one line -- what we are explicitly NOT building>

Confirm with an explicit "yes" (or tell me what to refine) before I draft the spec.
```
Do not accept *"whatever you think"* as confirmation — frame two concrete options instead.

### Worked Example: One Grill Turn

```text
HYPOTHESIS: You want a Cloud Run service that summarizes support tickets with Gemini for the EU support team.
CONFIDENCE: ~60% -- missing: data residency regime, ticket volume, and who consumes the summaries.

Q: Must ticket text and model inference stay inside an EU region (for example europe-west4), or is a global endpoint acceptable?
GUESS: EU-only, because the tickets contain customer PII and the team sits under GDPR; that implies regional Vertex AI endpoints and CMEK.
```
The user answers; you update `CONFIDENCE`, then ask the next single question. Stop asking once the next three answers are predictable.

### Edge Cases

- **User refuses the interview** ("just build it"): State your top three assumptions as `ASSUMPTION:` lines, flag the riskiest one, and ask for a single yes/no on all three before drafting. Never silently invent requirements.
- **User answers several questions at once:** Accept them, restate what changed in `CONFIDENCE`, and continue one question at a time for whatever is still missing.
- **Answers contradict earlier answers:** Quote both answers side by side and ask which one wins before moving on.
- **An existing spec already covers the request:** Read it first, grill only the deltas, and update the existing file instead of creating a parallel spec.

---

## Stage 2: Phase 0 Scope Check (Capability Map)

If the confirmed request bundles several independently testable capabilities (e.g., `ingestion`, `agent-runtime`, `eval-harness`, `terraform-infra`), propose a **Capability Map** before writing a monolithic spec:

```markdown
# Capability Map: [Initiative Name]

| Module ID | Responsibility | Depends On |
| :--- | :--- | :--- |
| `infra-foundation` | VPC-SC perimeter, KMS keys, IAM service accounts | — |
| `agent-runtime` | ADK root_agent, tool definitions, session store | `infra-foundation` |
| `eval-harness` | Golden dataset runner and trajectory assertions | `agent-runtime` |

Build order: infra-foundation -> agent-runtime -> eval-harness
```
Module IDs must be stable kebab-case with acyclic dependencies (`->`).

---

## Stage 3: Technical Specification & Milestone DAG

Once intent is confirmed, generate the specification using [templates/spec-template.md](templates/spec-template.md) and save to `docs/specs/<feature>.md` (or `tasks/plan.md`).

### Required Spec Sections
The template's 8 numbered sections map to these requirements:
1. **Objective & Non-Goals (template §1-2):** Problem statement, target user, measurable success metrics, and explicit **Out of Scope / Not Doing** list.
2. **Architecture & Data Flow (template §3):** Component diagram (Mermaid `flowchart` or `sequenceDiagram` with quoted labels), API/schema contracts, and state model.
3. **Commands & Project Structure (template §4-5):** Full executable `Build`, `Test`, `Lint`, and `Verify` commands plus directory layout.
4. **Three-Tier Boundaries (template §6):**
   - **Always do:** Run tests and `verify_static.py` before committing, validate inputs at boundaries.
   - **Ask first:** Schema changes, new third-party dependencies, IAM permission expansions.
   - **Never do:** Commit secrets, use mocks/stubs in production code paths, edit vendor/lockfiles by hand.
5. **Vertical-Slice Milestone DAG (`M1`..`Mn`, template §7) and Open Questions (template §8):**
   - Slice vertically (end-to-end testable capability per milestone), never horizontally ("build all schemas, then all APIs, then all tests").
   - Size each milestone to **1–5 files** (`XS`/`S`/`M`). Break down any `L`/`XL` milestone (`8+` files).
   - Every milestone must declare: `Dependencies`, `Parallelizable` (`[SEQUENTIAL]` or `[PARALLEL]`), `Files Touched`, `Acceptance Criteria`, and an executable `Verification Command`.
   - Never overwrite an existing `tasks/plan.md` or `tasks/todo.md` that still has unchecked tasks for different work without asking the user first.

See [references/definition-of-done.md](references/definition-of-done.md) for the standing quality bar every milestone must clear.

**Terminal Stop Rule:** After saving `docs/specs/<feature>.md`, summarize the spec and open questions, ask for human approval, and **STOP YOUR TURN IMMEDIATELY**. Never write spec and implementation code in the same turn.

---

## Common Rationalizations

| Rationalization | Reality |
| :--- | :--- |
| "The ask is clear enough, I'll skip the interview" | If you cannot state the measurable success target and non-goals in one sentence, the ask is ambiguous. |
| "I'll ask 8 questions at once to save turns" | Batched questions cause skim-reading and lock in wrong framing. Ask one question at a time with a guess attached. |
| "They said 'whatever you think,' so I'll decide" | "Whatever you think" is delegation without alignment. Present two concrete options with trade-offs instead. |
| "This is simple, I don't need a written spec" | Simple tasks need short specs, not zero specs. Writing acceptance criteria before code prevents rework. |
| "I'll write the spec after I code it" | Post-hoc specs are documentation, not specification. The spec's value is catching design errors before code exists. |
| "I'll slice horizontally (all DB, then all API)" | Horizontal slices leave the system untestable until the final step. Slice vertically so every milestone is verifiable. |
| "I'll write the spec and start coding in this turn" | Violates the gated workflow. Always stop after writing the spec so the human can course-correct cheaply. |

## Red Flags

- Asking more than one question in a single message, or asking a question without an attached `GUESS:`
- Confidence `<70%` with no explanation of what is missing
- Skipping the `Out of scope` line in the intent restate
- Starting implementation code in the same turn the spec is drafted
- Overwriting an existing `tasks/plan.md` or `tasks/todo.md` that has unchecked tasks
- Milestones that touch `8+` files or have no executable verification command
- Monolithic spec covering multiple independent subsystems without a Phase 0 Capability Map

## Verification

- [ ] Explicit `HYPOTHESIS` + `CONFIDENCE` score was stated up front
- [ ] Questions were asked one at a time with an attached `GUESS`
- [ ] User explicitly confirmed the 6-line Statement of Intent (including `Out of scope`)
- [ ] Spec covers all 8 sections in [templates/spec-template.md](templates/spec-template.md)
- [ ] Every milestone in the DAG is vertically sliced (`<=5` files) with an executable verification command
- [ ] Turn stopped immediately after saving the spec to await user approval
