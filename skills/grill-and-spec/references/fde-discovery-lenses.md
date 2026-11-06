# FDE Enterprise & Agentic Discovery Lenses

When running Socratic pre-flight (`/grill`) for cloud architectures, AI agents, or customer PoCs, cross-examine the plan against these five lenses:

## 1. Security, Sovereignty & Data Boundaries
- **Data Residency & Sovereignty:** Which region(s) must data-at-rest and model inference stay pinned to (`europe-west3`, `europe-west2`, `us-central1`)? Are Assured Workloads or EU/UK sovereign controls required?
- **Encryption & Network Isolation:** Does the workload require CMEK (Cloud KMS), VPC Service Controls (VPC-SC) perimeters, Private Service Connect (PSC), and zero public IPs?
- **Identity & Least Privilege:** How are service accounts separated (build vs. runtime vs. tool execution)? Are there any overly broad roles (`roles/editor`, `roles/owner`)?

## 2. Agentic AI & LLM Runtime Resilience
- **Model Routing & Fallbacks:** Which model tier handles high-volume routing vs. deep reasoning? What happens on `429 RESOURCE_EXHAUSTED`?
- **Tool Ergonomics & Determinism:** What should be a deterministic Python/Go tool vs. an LLM prompt instruction? Are tool outputs bounded so they cannot overflow the context window?
- **Safety & Guardrails:** How is untrusted input sanitized against prompt injection (e.g., Model Armor, schema validation, output grounding)?

## 3. Evaluation & Quality Flywheel
- **Golden Dataset:** What are the 10–20 representative test cases (happy path, adversarial, boundary) that define "working"?
- **Trajectory & Rubric Metrics:** How do we measure tool-call accuracy, groundedness, and latency regression on every prompt/code change?

## 4. FinOps, Latency & Quota Ceilings
- **Latency Budget:** What is the end-to-end p50/p95 latency target (TTFT vs. total turn completion)?
- **Token & Cost Ceiling:** What is the expected cost per 1,000 requests or sessions? Are context caching or smaller models needed?

## 5. Day-2 Operations & Handoff
- **Observability:** Are Cloud Trace / OpenTelemetry spans, structured JSON logs, and error rates wired from day 1?
- **Customer Ownership:** Can the customer's engineering team deploy and operate this via standard CI/CD and Terraform without manual console clicks?
