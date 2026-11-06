# Blinded Multi-Persona Verification Rubrics

Apply these rubrics in Stage 2, only after `verify_static.py` exits `0` and the project's own test suite passes. Each persona grades every applicable criterion `PASS` or `FAIL` with a `file:line` or command-output citation. Mark a criterion `N/A` only when the artifact type makes it impossible (for example, IAM criteria on a resume), and say why.

## Persona 1: Principal Cloud / Systems Architect

| Criterion | PASS Requires |
| :--- | :--- |
| Simplicity & concept count | No component, flag, or layer can be removed without losing a stated requirement. |
| Failure paths | Behavior on timeout, `429`, malformed JSON, missing files, and partial writes is explicit and tested. |
| Idempotency | Re-running the command or deployment produces no duplicate resources, files, or symlinks. |
| Trust boundaries | Untrusted input (CLI args, file paths, LLM output, webhooks) is validated before reaching shell, SQL, or filesystem calls. |
| Sovereignty (cloud artifacts) | Regional endpoints, CMEK keys, VPC-SC perimeters, and least-privilege IAM (no `roles/owner`, `roles/editor`, `allUsers`) are enforced where the contract requires them. |

## Persona 2: Skeptical Staff QA & Security Engineer

| Criterion | PASS Requires |
| :--- | :--- |
| Adversarial inputs | Tried at least: empty input, non-ASCII text, path traversal (`../`), duplicate names, and an oversized payload. |
| Destructive operations | Deletes and overwrites are guarded (dry-run, exclusive create, backup, or ownership check). |
| Test strength | A mutation (inverted condition) in the core logic turns at least one test red. |
| Concurrency & reruns | Two parallel runs or a rerun after a crash cannot corrupt state. |
| Secrets | No credentials in code, URLs, logs, or committed config. |

## Persona 3: Target End-User / Customer Executive

| Criterion | PASS Requires |
| :--- | :--- |
| Contract coverage | Every requirement in the original prompt or spec maps to visible evidence in the artifact. |
| Signal-to-noise | The decision, answer, or impact metric appears in the first 3 lines. |
| Copy-paste accuracy | Every command in the artifact runs as written from the stated directory (placeholders are obvious `<like-this>`). |
| Typography hygiene | Bold limited to lead-ins and headline numbers; narrative paragraphs free of inline-code clutter. |
| Honest trade-offs | Limitations, costs, and rejected alternatives are stated without promotional language. |

## Verdict Rules

- Any `FAIL` blocks completion: fix the artifact, re-run Stage 1, then re-grade only the affected criteria plus any criteria the fix could have touched.
- A `PASS` without a citation counts as `FAIL`.
- If two personas disagree (for example, Architect wants fewer layers but QA wants an extra validation step), record both and resolve in favor of the written contract.
