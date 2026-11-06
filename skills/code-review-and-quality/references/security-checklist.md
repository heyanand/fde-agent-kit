# Security Checklist

Quick reference for application, cloud infrastructure, and AI agent security. Use alongside `code-review-and-quality`.

## Threat Modeling (Start Here)

- [ ] Trust boundaries mapped (HTTP requests, CLI flags, file uploads, webhooks, third-party APIs, LLM output, and local values written by untrusted processes)
- [ ] Assets named (credentials, PII, KMS keys, admin actions, tenant data)
- [ ] STRIDE run per boundary (Spoofing, Tampering, Repudiation, Info disclosure, DoS, Elevation)
- [ ] Abuse cases written next to use cases ("how would I misuse this?")

## Pre-Commit & Secret Hygiene

- [ ] No secrets in code (`git diff --cached -i -G'(password|secret|api[_-]?key|token|PRIVATE KEY)' --name-only` prints no files, or every listed file was inspected)
- [ ] API keys passed via HTTP headers (`x-goog-api-key`, `Authorization: Bearer`), never in URL query strings (`?key=`)
- [ ] `.gitignore` covers `.env`, `.env.*`, `*.pem`, `*.key`, and local corp overlays (`skills.manifest.local.json`)

## Authentication & Authorization

- [ ] Every protected endpoint checks authentication
- [ ] Every resource access checks ownership/tenant isolation (prevents IDOR)
- [ ] Cloud IAM bindings follow least privilege (no `allUsers`, `allAuthenticatedUsers`, `roles/owner`, `roles/editor`, or project-wide authoritative `google_project_iam_binding` on shared roles)
- [ ] Rate limiting active on auth and expensive inference endpoints

## Input Validation, XSS & Path Containment

- [ ] All external input validated at system boundaries with explicit schemas
- [ ] SQL/BigQuery queries parameterized (never string concatenation or f-strings)
- [ ] HTML/JSON embedding escapes `</` as `<\/` inside `<script>` blocks and sanitizes untrusted Markdown before DOM insertion
- [ ] Server-side URL fetches allowlisted; private/reserved IPs (`169.254.169.254`, loopback, RFC1918) blocked (prevent SSRF)
- [ ] Destructive or mutating file operations resolve symlinks first (`Path.resolve()`), validate names against `^[a-z0-9-]+$`, and use exclusive creation (`open(..., "x")`) where overwrite must be prevented

## AI / LLM Security (OWASP LLM Top 10)

- [ ] **LLM01 Prompt Injection:** System prompt is not treated as a security boundary; tool permissions enforced in code
- [ ] **LLM02 / LLM07 Sensitive Disclosure:** Secrets and cross-tenant data kept out of context windows and error traces
- [ ] **LLM05 Improper Output Handling:** Model output and external error logs treated as untrusted data — never passed into `eval`, SQL, `shell=True`, or raw `innerHTML`
- [ ] **LLM06 Excessive Agency:** Destructive or state-mutating tools require human confirmation or `--dry-run` preview
- [ ] **LLM10 Unbounded Consumption:** Token budgets, timeouts, and max iteration bounds enforced
