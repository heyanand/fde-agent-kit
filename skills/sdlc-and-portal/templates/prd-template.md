# Product Requirements Document (PRD): [Product / Initiative Name]

- **Owner:** [Name / Role]
- **Status:** Draft | In Review | Approved
- **Last Updated:** YYYY-MM-DD
- **Target Release:** [Milestone / Quarter]

---

## 1. Executive Summary & Problem Statement
[State the concrete customer or operational problem in 2–3 sentences, backed by baseline metrics (latency, error rate, cost, or manual toil hours).]

## 2. Target Users & Jobs-to-be-Done
| Persona | Current Pain Point | Desired Outcome |
| :--- | :--- | :--- |
| **[Primary Persona]** | [Specific bottleneck today] | [Measurable improvement] |
| **[Secondary Persona]** | [Specific bottleneck today] | [Measurable improvement] |

## 3. Success Metrics & Non-Goals

### Success Metrics (Falsifiable Targets)
- **Primary Metric:** [e.g., Reduce p95 document triage latency from 12m to <90s]
- **Quality / Guardrail Metric:** [e.g., Maintain >=98% citation accuracy on golden eval set]
- **Cost / Operational Ceiling:** [e.g., <=$0.04 per processed document]

### Explicit Non-Goals (Out of Scope)
- **[Non-Goal 1]:** [Reason excluded in this phase]
- **[Non-Goal 2]:** [Reason excluded in this phase]

## 4. Functional Requirements (P0 / P1 / P2)
| ID | Priority | Requirement | Acceptance Criteria |
| :--- | :---: | :--- | :--- |
| `FR-1` | **P0** | [Core capability] | [Testable condition] |
| `FR-2` | **P0** | [Core capability] | [Testable condition] |
| `FR-3` | **P1** | [Secondary capability] | [Testable condition] |

## 5. Security, Sovereignty & Compliance Constraints
- **Data Classification:** [Public / Internal / Confidential / Regulated PII]
- **Residency & Encryption:** [Target region, CMEK requirements, VPC-SC perimeter rules]
- **Access Control:** [Authentication mechanism and least-privilege authorization model]

## 6. Rollout & Risks
| Risk | Severity | Mitigation / Rollback Plan |
| :--- | :---: | :--- |
| [Risk 1] | High / Med / Low | [Concrete mitigation] |
