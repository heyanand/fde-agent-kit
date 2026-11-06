---
name: skill-forge
description: >-
  Authors, refactors, and evaluates portable Agent Skills (SKILL.md) across
  Google Antigravity, Gemini CLI, Claude Code, and OpenAI Codex using the Delta
  Principle, progressive disclosure, trigger boundary testing, and
  verify_static.py --mode skill. Use when creating a new skill, porting an
  external skill into fde-agent-kit, or auditing existing skills. Don't use for
  linking/symlinking already-authored skills (use sync).
---

# Portable Agent Skill Authoring & Evaluation Guide (`skill-forge`)

Start every new skill from [templates/SKILL-template.md](templates/SKILL-template.md) and document human-facing provenance, cluster rationale, and attribution in `skills/<name>/README.md`.

---

## 1. The 7 Laws of High-Leverage Portable Skills

1. **The Delta Principle (`Expert Knowledge - Base Model Weights`):**
   - Never waste tokens explaining standard syntax the LLM already knows (how to write a Python loop, basic Markdown syntax, what Git is).
   - Encode only **non-obvious procedural guardrails**, **deterministic CLI gates**, **domain-specific gotchas**, **`Common Rationalizations` tables**, and **`Red Flags` checklists**.
2. **Strict Progressive Disclosure (`50..800` Lines) & Separation of `README.md` vs. `SKILL.md`:**
   - `skills/<name>/SKILL.md` must be **between 50 and 800 lines** (ideally 80–250 lines) and contain **only operational instructions for the agent**.
   - Put human-facing metadata (upstream inspiration/provenance, cluster placement rationale, file inventory) in `skills/<name>/README.md` so it never consumes LLM context tokens when the skill triggers.
   - Move deep lookup tables, full code examples, and boilerplate templates into `references/`, `templates/`, and `scripts/` inside the skill folder, linked via relative Markdown links (`[templates/foo.md](templates/foo.md)`).
3. **Sharp Routing Boundaries in Frontmatter (`Use when` + `Don't use`):**
   - The `name:` field must be kebab-case (`^[a-z0-9-]+$`) and **exactly match** the parent directory name.
   - The `description:` field is the primary routing index loaded into global context. It **must** contain both positive triggers (`Use when ...`) and explicit negative boundaries (`Don't use for ... (use <other-skill>)`).
4. **Symlink-Safe Script Invocations (`<skill-dir>/scripts/...`):**
   - Skills are symlinked into `~/.gemini/config/skills/<name>`, `~/.gemini/skills/<name>`, `~/.claude/skills/<name>`, `~/.codex/skills/<name>`, or `<project>/.gemini/skills/<name>`.
   - **Never** write repo-root-relative paths like `python3 skills/foo/scripts/bar.py` inside `SKILL.md` — those fail outside the `fde-agent-kit` root! Always use `<skill-dir>/scripts/bar.py` for the skill's own scripts and `<skill-dir>/../<sibling>/scripts/...` (e.g. `<skill-dir>/../verify/scripts/verify_static.py`) for another kit skill. Never hardcode a harness-specific home such as `~/.gemini/config/skills/` or `~/.claude/skills/`; it breaks on every other harness.
5. **Deterministic Scripts Over Prose Instructions:**
   - Whenever a check can be expressed in Python (`AST`, regex, schema validation, file numbering), ship an executable `chmod +x` script in `scripts/` rather than hoping the LLM counts lines or checks regexes by eye.
6. **Copy-Paste & Typography Safety:**
   - Never place Unicode em-dashes (`—`) or en-dashes (`–`) inside fenced code blocks where they corrupt CLI flags (`--mode`).
   - Quote all Mermaid node labels containing parentheses or brackets (`Node["Label (Info)"]`).
7. **Anti-Rationalization Inoculation:**
   - Every behavioral skill must include a `## Common Rationalizations` table and a `## Red Flags` list to inoculate the agent against skipping steps under time pressure.

---

## 2. Trigger & Baseline-Delta Evaluation Protocol

Before registering a new skill in `skills.manifest.json`:

### Step 2.1: Static Verification Gate
```bash
python3 <skill-dir>/../verify/scripts/verify_static.py --mode skill skills/<new-skill-name>/
```
Must exit `0` (verifies kebab-case directory, frontmatter `name` match, `50..800` line bounds, `Use when` + `Don't use` triggers, no Unicode dashes in code blocks, and that all relative links `[...](references/...)` resolve to existing files).

### Step 2.2: Routing Boundary Test (2 Positive + 2 Negative Prompts)
Verify that the frontmatter `description:` cleanly separates this skill from its neighbors:
- **Positive Prompt 1 & 2:** Realistic user prompts that *must* trigger this skill.
- **Negative Prompt 1 & 2:** Adjacent user prompts that *must not* trigger this skill (routing to the named neighbor skill instead).

### Step 2.3: Baseline-Delta Check
Compare agent output on a representative task **without** the skill vs. **with** the skill loaded. Every section in `SKILL.md` that does not measurably change agent behavior or prevent a known failure mode should be deleted.

### Step 2.4: Register in `skills.manifest.json` & `catalog`
Add the skill to either `clusters.core.skills` (only if universally needed in every session) or `clusters.jit.skills` (default for domain skills) in `skills.manifest.json`, and add a row to `skills/catalog/SKILL.md`.

## Common Rationalizations

| Rationalization | Reality |
| :--- | :--- |
| "A 30-line summary is enough for this skill" | Sub-50-line summaries omit the `Common Rationalizations`, `Red Flags`, and concrete edge cases that actually alter LLM behavior. |
| "I'll write `python3 skills/my-skill/scripts/run.py` in `SKILL.md`" | That path fails the moment the skill is invoked from any project outside `fde-agent-kit`. Use `<skill-dir>/scripts/run.py`. |
| "I'll add this domain skill to Cluster 1 Global Core so it's always loaded" | Global Core is capped at ~8 meta-skills to protect the context window. Put domain skills in Cluster 2 (JIT). |

## Red Flags

- `SKILL.md` under 50 lines (`[SKILL_TOO_SHORT]`) or over 800 lines (`[SKILL_SIZE]`)
- Frontmatter `name:` that does not match the parent directory name (`[FRONTMATTER_MISMATCH]`)
- Missing `Use when` or `Don't use` in frontmatter `description:` (`[ROUTING]`)
- Broken relative Markdown links to `references/`, `templates/`, or `scripts/` (`[BROKEN_LINK]`)
- Repo-relative `python3 skills/...` commands that break when symlinked globally
- Harness-specific absolute paths (`~/.gemini/config/skills/...`, `~/.claude/skills/...`) in runnable commands
- Missing `## Common Rationalizations`, `## Red Flags`, or `## Verification` sections

## Verification

- [ ] `python3 <skill-dir>/../verify/scripts/verify_static.py --mode skill skills/<name>/` exits `0`
- [ ] All bundled scripts in `skills/<name>/scripts/` have `+x` permissions and unit test coverage in `tests/test_scripts.py`
- [ ] Skill is registered in `skills.manifest.json` and documented in `skills/catalog/SKILL.md`
