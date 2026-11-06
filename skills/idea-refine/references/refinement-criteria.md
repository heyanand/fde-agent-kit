# Refinement & Evaluation Criteria

Use this rubric during Phase 2 (Evaluate & Converge) to stress-test candidate directions.

## 1. User & Business Value (Painkiller vs. Vitamin)
- **Painkiller:** Solves an acute, frequent bottleneck. Users have built brittle workarounds and will actively switch.
- **Vitamin:** Nice-to-have polish that rarely justifies migration cost or operational ownership.

## 2. Feasibility (Technical, Operational & Compliance)
- Does the core capability work deterministically today?
- What is the hardest technical or regulatory hurdle (e.g., data residency, latency budget, IAM boundary)?
- Can an MVP deliver measurable value in days rather than months?

## 3. Differentiation
1. **New capability:** Enables something previously impossible.
2. **10x improvement:** Order-of-magnitude reduction in latency, cost, or manual toil.
3. **New operating boundary:** Runs inside a sovereign, air-gapped, or regulated boundary where alternatives fail.
4. **Better UX/DX:** Same capability, dramatically simpler developer or user workflow.

## 4. Assumption Audit Tiers
- **Must Be True (Dealbreakers):** If false, the architecture fails. Validate before writing production code.
- **Should Be True (Important):** Impacts performance or adoption; requires mitigation plan.
- **Might Be True (Nice to Have):** Defer until the core path is proven.

## 5. Prioritization Matrix

| | High Feasibility | Low Feasibility |
| :--- | :--- | :--- |
| **High Value** | **Build First (MVP)** | Validate riskiest assumption via spike |
| **Low Value** | Only if trivial | **Cut (Add to Not Doing list)** |
