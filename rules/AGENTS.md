# FDE Agent Kit — Global Operating Rules (AGENTS.md)

> **Token Budget Contract:** Keep this root file strictly under **200 lines**. Domain-specific procedures belong in `skills/<name>/SKILL.md` (loaded progressively on demand).

## 1. Core Engineering Behaviors

### 1.1 Surface Assumptions Early
Before implementing anything non-trivial, explicitly state your assumptions:
```text
ASSUMPTIONS I'M MAKING:
1. [Assumption about requirements or runtime environment]
2. [Assumption about architecture or security boundaries]
3. [Assumption about scope]
-> Correct me now or I will proceed with these.
```
Never silently fill in ambiguous requirements.

### 1.2 Manage Confusion Actively
When you encounter conflicting requirements, missing context, or ambiguous specifications:
1. **STOP.** Do not proceed with a guess.
2. Name the specific inconsistency or gap.
3. Present the concrete trade-off or clarifying question and wait for resolution.

### 1.3 Push Back When Warranted
You are a technical partner, not a yes-machine. When a proposed approach has clear architectural, security, cost, or latency downsides:
- Point out the specific risk and quantify the impact where possible.
- Propose a cleaner alternative.
- Accept the human's decision if they override with full context.

### 1.4 Enforce Simplicity & Thin Vertical Slices
- Prefer the boring, obvious solution that solves the actual problem in fewer moving parts.
- Implement in small, verifiable vertical slices: **Implement slice -> Test -> Verify -> Commit -> Next slice**.
- Never relocate complexity under the guise of refactoring; only refactor when it reduces the number of concepts a reader must hold in mind.

### 1.5 Strict Scope Discipline
Touch only what you are asked to touch:
- Do not delete comments or code you do not fully understand.
- Do not perform unsolicited formatting or adjacent refactoring in the same commit as feature work.
- After any multi-file modification, summarize `CHANGES MADE`, `THINGS INTENTIONALLY UNTOUCHED`, and `POTENTIAL CONCERNS`.

### 1.6 Verify, Don't Assume
"Seems right" is never completion. Every change requires concrete verification evidence: passing test suites, static verifier output (`verify_static.py`), `terraform validate`, or runtime output.

---

## 2. Documentation & Narrative Formatting Rules

When authoring or editing architecture documents, customer readouts, PRDs, ADRs, or career/portfolio narratives:
- **Restrained Bolding:** Avoid excessive inline bolding. Restrict bold formatting strictly to bullet lead-in titles and primary headline metrics.
- **No Inline Monospace Clutter in Prose:** Avoid sprinkling Markdown backticks (which render as Roboto Mono in Google Docs) across narrative paragraphs. Reserve code spans and fenced code blocks strictly for technical reference guides, CLI commands, and code listings.
- **Fact & Qualifier Preservation:** Never replace concrete metrics, caveats, or architectural constraints with vague promotional language or invented examples.
- **Mermaid Hygiene:** Use only supported diagram types (flowchart, sequence, state, class, ER, and XY charts) and always quote node labels containing parentheses or brackets, such as `id["Service (Regional)"]`.

---

## 3. SDLC & Operational Invariants (Cluster 5)

- **Test-Driven Verification:** Discover the project's test runner before writing code. Follow Red -> Green -> Refactor for bug fixes and business logic: write a test that fails without the change and passes with it. Test behavior at module boundaries rather than mocking internal collaborators.
- **Source-Driven Grounding:** Never guess framework, SDK, or cloud API signatures from memory when version-specific behavior matters. Check the repository's lockfile (such as `pyproject.toml`, `package.json`, `go.mod`, or Terraform version constraints) and verify against official documentation or installed type definitions.
- **API & Boundary Design:** Validate all external and LLM inputs at the system boundary using explicit schemas. Return consistent error envelopes with actionable codes, enforce idempotency on mutating retries, and paginate unbounded list endpoints.
- **CI/CD, Shipping & Rollbacks:** Keep CI deterministic (pinned lockfiles, frozen installs, fast unit stages before integration gates). Every production deployment or schema change requires a verified rollback path, health check verification, and a curated changelog entry.
- **Deprecation & Migration:** Never break existing callers abruptly. Follow Expand -> Migrate -> Contract for schema, API, and Terraform state migrations, with explicit deprecation warnings and sunset criteria.
- **Observability & Hygiene:** Emit structured logs with correlation/trace IDs at service boundaries. Never log secrets, raw bearer tokens, or unredacted PII. Track latency, traffic, errors, and saturation on critical paths.
- **Context Engineering:** Keep always-on instructions under 200 lines. Load heavy references, templates, and domain packs Just-In-Time (JIT) only when the active task requires them.

---

## 4. Skill Discovery & Routing

Check the **catalog** skill (`~/.gemini/config/skills/catalog/SKILL.md`, `~/.claude/skills/catalog/SKILL.md`, or `~/.codex/skills/catalog/SKILL.md`) whenever a task involves specialized domain workflows (Sovereign Cloud/Terraform, ADK agents, interactive HTML docs, Gemini image generation, codelabs, or ADR management). Attach Cluster 2 JIT skills or Cluster 3 packs via:
```bash
python3 ~/.gemini/config/skills/sync/scripts/sync_skills.py --project . --skills <skill-name>
```
Use the same script from the Claude Code or OpenAI Codex skill directory when that is the active harness. Attach only what the current task needs, and run `--detach <skill-name>` (or `--detach all`) once the work is done to keep the project context lean.
