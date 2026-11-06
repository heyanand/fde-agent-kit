---
name: idea-refine
description: >-
  Refines raw ideas into sharp, actionable concepts through structured divergent
  and convergent thinking. Use when an idea is still vague, when you need to
  stress-test assumptions before committing to a plan, or when you want to
  expand options before converging on one. Triggers on "ideate", "refine this
  idea", or "stress-test my concept". Don't use when a direction is already
  chosen and needs a formal technical specification or milestone DAG (use
  grill-and-spec).
---

# Idea Refine

Refines raw ideas into sharp, actionable concepts worth building through structured divergent and convergent thinking.

## When to Use

- An idea is still vague and needs shaping before it can become a specification
- You need to explore alternative angles before committing to an architecture or product direction
- You want to expand options via structured lenses before converging on an MVP
- **Don't use when:** the direction is already chosen and ready for a technical spec and milestone breakdown (use `grill-and-spec`), or for mechanical bug fixes.

## Optional Workspace Setup

```bash
# Optional: run from the project root to initialize ./docs/ideas
# <skill-dir> is the directory containing this SKILL.md
# (e.g. ~/.gemini/config/skills/idea-refine or ~/.claude/skills/idea-refine)
bash <skill-dir>/scripts/idea-refine.sh            # creates ./docs/ideas
bash <skill-dir>/scripts/idea-refine.sh notes/ideas # or a custom directory
```

## Philosophy

- **Simplicity is the ultimate sophistication.** Push toward the simplest version that still solves the real problem.
- **Start with the user experience, work backwards to technology.**
- **Say no to 1,000 things.** Focus beats breadth.
- **Challenge every assumption.** "How it's usually done" is not a reason.
- **Be honest, not a yes-machine.** If an idea is weak or over-engineered, say so with specificity and kindness.

## The 3-Phase Process

Guide the user through three distinct phases. Do not jump straight to Phase 3 without running Phases 1 and 2.

### Phase 1: Understand & Expand (Divergent)

1. **Restate the idea** as a crisp *"How Might We"* problem statement to force clarity on what is actually being solved.
2. **Ask 3–5 sharpening questions** (no more) before generating solutions:
   - Who is this for, specifically?
   - What does success look like?
   - What are the real constraints (time, tech, compliance, budget)?
   - What has been tried before, and why now?
   Wait for the user's answers before moving to variations.
   - **If the user declines questions** ("just give me ideas"): write each unanswered question as an explicit `ASSUMPTION:` line, then proceed. The assumptions carry forward into Phase 2's hidden-assumption audit.
3. **If running inside a codebase:** Scan existing architecture, manifests, and modules first so your variations respect real constraints and prior art.
4. **Generate 5–8 idea variations** using distinct lenses (see [references/frameworks.md](references/frameworks.md)):
   - **Inversion:** "What if we did the exact opposite?"
   - **Constraint Removal:** "What if budget, latency, or legacy systems weren't factors?"
   - **Audience Shift:** "What if this were built for a completely different persona?"
   - **Combination:** "What if we merged this with an adjacent capability?"
   - **Simplification (10x Simpler):** "What is the version that delivers 80% of the value in 10% of the code?"
   - **10x Scale Version:** "What would this look like at 100x scale?"
   - **Expert / FDE Lens:** "What would a production cloud/AI architect find obvious that outsiders miss?"

### Phase 2: Evaluate & Converge

After the user reacts to Phase 1:
1. **Cluster** the ideas that resonated into **2–3 meaningfully distinct directions**.
2. **Stress-test** each direction against the 3-axis rubric in [references/refinement-criteria.md](references/refinement-criteria.md):
   - **User Value:** Painkiller vs. vitamin — who benefits and how much?
   - **Feasibility:** Technical and operational cost; what is the hardest part?
   - **Differentiation:** Why switch from the status quo or existing tools?
3. **Surface hidden assumptions** for each direction:
   - What we are betting is true (but haven't validated)
   - What could kill this idea
   - What we are intentionally choosing to ignore for now

### Phase 3: Sharpen & Ship

Produce a concrete Markdown one-pager and ask the user before saving to `docs/ideas/<idea-name>.md`:

```markdown
# [Idea Name]

## Problem Statement
[One-sentence "How Might We" framing]

## Recommended Direction
[The chosen direction and why — 2-3 paragraphs max]

## Key Assumptions to Validate
- [ ] [Assumption 1 — concrete falsifiable test]
- [ ] [Assumption 2 — concrete falsifiable test]
- [ ] [Assumption 3 — concrete falsifiable test]

## MVP Scope
[The minimum version that tests the core assumption. What is in, what is out.]

## Not Doing (and Why)
- [Excluded feature/scope 1] — [specific reason]
- [Excluded feature/scope 2] — [specific reason]
- [Excluded feature/scope 3] — [specific reason]

## Open Questions
- [Question that needs answering before spec/implementation]
```

See [references/examples.md](references/examples.md) for end-to-end session examples.

### Handoff & Edge Cases

- **Handoff:** Once the user confirms the one-pager, offer `grill-and-spec` with the saved `docs/ideas/<idea-name>.md` as input. Do not start a technical spec, Capability Map, or code inside `idea-refine`.
- **File already exists:** If `docs/ideas/<idea-name>.md` exists, show a diff of the proposed changes and ask before overwriting; never clobber a prior session's one-pager.
- **User arrives with a chosen direction:** Skip Phase 1 variations, run only the Phase 2 stress-test on that direction, and hand off to `grill-and-spec`.
- **Idea is weak at the root** (no clear user, or a vitamin with high cost): Say so in Phase 2 with the specific rubric axis that fails, and offer one pivot direction rather than polishing the original.

## Common Rationalizations

| Rationalization | Reality |
| :--- | :--- |
| "I'll generate 20+ ideas to cover all bases" | 5–8 well-considered variations beat 20 shallow ones. Quality over quantity. |
| "The user just needs encouragement, not critique" | A yes-machine produces weak ideas. Push back on complexity and weak value propositions with specificity. |
| "Who this is for is obvious — no need to ask" | Every good idea starts with a specific person and their pain. Skipping it means designing for nobody. |
| "We'll surface assumptions once we start building" | Untested assumptions are the #1 killer of projects. Surface them before committing to code. |
| "A plan without a Not Doing list is fine" | The **Not Doing** list is the highest-leverage section in the one-pager. Focus requires explicit exclusions. |

## Red Flags

- Generating 20+ shallow bullet points instead of 5–8 reasoned variations
- Skipping the "who is this for" and "what does success look like" questions
- Committing to a direction with zero falsifiable assumptions surfaced
- Yes-machining weak or over-complicated ideas without pushback
- Producing a one-pager without a **Not Doing (and Why)** list
- Ignoring existing repository architecture when ideating inside a codebase
- Jumping straight to Phase 3 output in the first turn without running Phases 1 and 2

## Verification

- [ ] A crisp "How Might We" problem statement exists
- [ ] Target user, success criteria, and binding constraints are explicitly defined
- [ ] 5–8 variations across distinct lenses were explored before converging
- [ ] Hidden assumptions are listed with concrete validation tests
- [ ] A **Not Doing (and Why)** list makes scope trade-offs explicit
- [ ] User confirmed the direction before saving `docs/ideas/<idea-name>.md` or handing off to `grill-and-spec`
