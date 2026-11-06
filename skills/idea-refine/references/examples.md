# Ideation Session Examples

These examples demonstrate what strong ideation sessions look like across early-stage concepts, codebase-aware features, and engineering workflows.

---

## Example 1: Vague Early-Stage Concept (3-Phase Session)

**User invokes:** "I want to help enterprise platform teams govern AI agent tool access across multi-cloud environments"

### Phase 1: Understand & Expand (Divergent)

> **How might we** give enterprise security and platform teams deterministic visibility and policy control over which tools AI agents can invoke, without slowing down developer velocity?

Sharpening questions:
1. **Which layer of governance is the acute pain?** Pre-deployment static policy checks, runtime MCP/tool gateway enforcement, or post-hoc audit logging?
2. **Who is the primary buyer/operator?** The Cloud CISO / SecOps team, or the AI developer building ADK/LangGraph agents?
3. **What is the binding constraint?** Must it run air-gapped inside a customer VPC-SC perimeter, or can it be a SaaS control plane?

Once the user clarifies ("Runtime tool gateway + audit logging inside the customer's GCP VPC"), generate 6 variations across lenses:
1. **Simplification:** Sidecar Envoy/MCP proxy that evaluates Cedar/OPA policies on tool call payloads before forwarding.
2. **Inversion:** Capability-token minting — agents have zero standing permissions and request short-lived, task-scoped tokens signed by the user's OIDC identity.
3. **Constraint Removal:** Dry-run shadow mode that records every tool call and auto-synthesizes least-privilege allowlists from 7 days of staging traffic.
4. **Audience Shift:** Developer-first local emulator that catches policy violations in `pytest` before code ever reaches staging.
5. **Combination:** Merge tool-call authorization with DLP redaction so PII never enters or leaves an untrusted MCP server.
6. **Expert Lens:** Focus on **excessive agency (OWASP LLM06)** — require human-in-the-loop Slack/Webhook approval only for mutating or destructive tool calls while auto-approving read-only queries.

### Phase 2: Evaluate & Converge
Cluster into 2–3 distinct directions (e.g., **Direction A: Policy-as-Code MCP Gateway + Auto-Policy Generator** vs. **Direction B: Full SaaS Agent Observability Platform**), stress-test against User Value, Feasibility, and Differentiation, and surface hidden assumptions (e.g., whether teams standardize on MCP vs. native SDK tool functions).

### Phase 3: Sharpen & Ship
Produce `docs/ideas/agent-tool-governance.md` with Problem Statement, Recommended Direction, Key Assumptions to Validate, MVP Scope, and an explicit **Not Doing (and Why)** list (e.g., not building a custom LLM router, not building a dashboard UI in v1).

---

## Example 2: Codebase-Aware Feature Ideation

When invoked inside an existing repository:
1. Scan the existing architecture (`skills.manifest.json`, `src/`, `pyproject.toml`, `terraform/`) before proposing variations.
2. Ground variations in real files and constraints (e.g., "Your existing service uses Cloud Run with Pub/Sub push subscriptions; Variation 1 reuses that dead-letter queue rather than introducing Kafka").
3. Push back on variations that duplicate existing infrastructure or violate module boundaries.

---

## Example 3: Pushing Back on an Over-Engineered Idea

**User invokes:** "Let's build a multi-agent swarm with a vector database and a fine-tuned model to answer questions about our 40-page internal runbook."

### Phase 1: Understand & Expand (Divergent)

> **How might we** let on-call engineers get correct runbook answers in under 30 seconds during an incident?

The sharpening questions reveal: 12 engineers, one 40-page runbook that changes monthly, and answers must cite the runbook section.

Variations include the **Simplification** lens: put the whole runbook in a single long-context prompt with a "cite the section heading" instruction. At roughly 20k tokens, it fits comfortably in one Gemini context window with no retrieval layer at all.

### Phase 2: Evaluate & Converge

Honest pushback, tied to the rubric:
- **Feasibility:** A vector database, an orchestrator, and a fine-tuning pipeline add three systems to operate for a corpus that fits in one prompt.
- **User Value:** The pain is answer latency and trust, both of which the single-prompt version addresses with citations.
- **Hidden assumption:** "The runbook will grow 100x" - unvalidated; revisit if it passes ~200 pages.

### Phase 3: Sharpen & Ship

**Recommended Direction:** Single long-context prompt with mandatory section citations, evaluated against 15 real incident questions.
**Not Doing (and Why):** no vector database (corpus fits in context), no fine-tuning (monthly edits would force retraining), no multi-agent orchestration (single-hop questions).
