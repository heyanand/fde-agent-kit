# Ideation Frameworks Reference

Use these frameworks selectively. Pick the lens that fits the idea — don't mechanically run every framework. The goal is to unlock thinking, not to follow a checklist.

## SCAMPER

- **Substitute:** What component, model, or process could you swap out?
- **Combine:** What if you merged this with another service or workflow?
- **Adapt:** What parallel exists in another industry or domain?
- **Modify (Magnify/Minimize):** What if you made it 10x bigger or stripped it to a single CLI command?
- **Put to other uses:** What adjacent persona or problem could this solve?
- **Eliminate:** What happens if you remove configuration or state entirely?
- **Reverse/Rearrange:** What if you inverted the control flow or data flow?

## How Might We (HMW)

Reframe pain points as opportunities: *"How might we [desired outcome] for [specific user] without [key constraint]?"*
- Narrow enough to be actionable, broad enough to allow multiple architectures, and anchored on a real tension.

## First Principles Thinking

1. **What do we know is provably true?** (Hard physics, quota limits, regulatory law)
2. **What are we merely assuming?** (Legacy conventions, habitual architectures)
3. **Which assumptions can we challenge?**
4. **Rebuild from the ground truths.**

## Jobs to Be Done (JTBD)

Format: *"When I [situation], I want to [motivation], so I can [expected outcome]."*
- Distinguish the **functional job**, **operational/reliability job**, and **stakeholder/compliance job**.

## Constraint-Based Ideation

- **Time constraint:** What if we had to ship a working PoC in 48 hours?
- **Feature constraint:** What if it could expose only one API endpoint or tool?
- **Zero-trust constraint:** What if no external network egress or persistent database were allowed?

## Pre-Mortem

Imagine it is 6 months from now and the system failed in production. Work backwards:
1. List every plausible technical, operational, security, or adoption failure mode.
2. Identify which failure modes are preventable by design right now.
