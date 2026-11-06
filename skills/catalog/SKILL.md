---
name: catalog
description: >-
  Routes tasks to the right skill or preset pack in fde-agent-kit and compiles
  Open Knowledge Format (OKF v0.2) indexes for agentic discovery. Use when
  inspecting which domain skills or packs exist in the forge, when starting work
  in a new repository that needs Just-In-Time (JIT) skills attached, or when
  indexing a documentation directory for progressive disclosure. Don't use for
  executing the actual symlink operations directly (use sync).
---

# Skill Catalog & Open Knowledge Format (OKF) Router

## 1. Resolving the `fde-agent-kit` Root From Any Directory

Because `catalog` and `sync` are symlinked into every global harness directory, you can invoke the sync engine from any working directory without knowing where the repository is cloned. Each harness uses a different global directory, so locate the first one that exists:

```bash
# Find the global skills directory used by this harness (Antigravity, Gemini CLI, Claude Code, or Codex)
for d in ~/.gemini/config/skills ~/.gemini/skills ~/.claude/skills ~/.codex/skills; do
  if [ -f "$d/sync/scripts/sync_skills.py" ]; then SKILLS_HOME="$d"; break; fi
done
echo "Using ${SKILLS_HOME:?No global sync skill found - run sync_skills.py --fix from the fde-agent-kit clone}"

# Attach JIT skills or a preset pack into the current project
python3 "$SKILLS_HOME/sync/scripts/sync_skills.py" --project . --skills gcp-sovereign-arch,sdlc-and-portal
python3 "$SKILLS_HOME/sync/scripts/sync_skills.py" --project . --pack arch
```

`sync_skills.py` resolves its own symlink back to the `fde-agent-kit` clone (it walks up to `skills.manifest.json`), so every harness path above runs the same canonical script.

---

## 2. Complete `fde-agent-kit` Skill Inventory

### Cluster 1: Global Core Skills (Always Active Globally)

| Skill | Primary Trigger | Core Deliverable / Gate |
| :--- | :--- | :--- |
| `catalog` | Task routing, JIT skill discovery, OKF v0.2 indexing | Recommends `--skills` / `--pack` or compiles `INDEX.okf.md` |
| `sync` | Auditing symlinks, corp/off-corp switching, JIT linking | Runs `sync_skills.py` (`--fix`, `--prune`, `--project`, `--detach`) |
| `idea-refine` | Vague concept needing 5–8 divergent lenses + convergence | `docs/ideas/<name>.md` with a **Not Doing** list |
| `grill-and-spec` | Socratic pre-flight (`>=95%` confidence) -> Capability Map -> Spec | `docs/specs/<feature>.md` + vertical-slice Milestone DAG |
| `code-review-and-quality` | Pre-merge 5-axis code review & mutation check | Severity-labeled review report (`Critical:`, `Required:`, `Nit:`) |
| `git-workflow-and-versioning` | Atomic commits, splitting dirty trees, worktrees, SemVer | Clean commit history, secret scan, 3-part scope summary |
| `verify` | Expectation-Grounded Alignment (EGA) & static verification | `verify_static.py` exit `0` + blinded multi-persona rubric |
| `unslop` | Stripping AI prose tropes, backtick clutter & code bloat | De-slopped narrative/code passing `--mode prose` |

### Cluster 2: Project-Scoped JIT Domain Skills (Attach on Demand)

Attach any of these into the current workspace via `python3 "$SKILLS_HOME/sync/scripts/sync_skills.py" --project . --skills <name>` (see Section 1 for `$SKILLS_HOME`):

| Skill | When to Attach | Bundled Scripts / Templates |
| :--- | :--- | :--- |
| `documentation-and-adrs` | Recording MADR architecture decisions, API docstrings, prose review | `templates/madr-template.md` |
| `sdlc-and-portal` | Authoring PRDs/Design Docs/Readouts or compiling single-file HTML portals | `scripts/compile_portal.py`, `templates/portal.html`, `templates/*.md` |
| `image-gen` | Generating architecture diagrams, hero banners, icons via Gemini/Imagen | `scripts/image_gen.py` |
| `continuous-alignment` | Distilling session transcripts, enforcing 200-line `AGENTS.md` budget | `scripts/distill_session.py` |
| `work` | Executing a multi-milestone spec DAG with `tasks/handoff.md` state | `templates/handoff.md`, `references/orchestration-patterns.md` |
| `codelab` | Building interactive step-by-step customer workshops & labs | `templates/codelab-template.md` |
| `gcp-sovereign-arch` | Authoring Terraform (CFF), VPC-SC, CMEK, Assured Workloads, WIF | `references/sovereign-controls.md` |
| `google-oss` | Preparing a repo for Google Open Source release (Apache-2.0, hygiene) | `templates/CONTRIBUTING.md`, `templates/SECURITY.md` |
| `skill-forge` | Authoring, refactoring, or evaluating a new portable `SKILL.md` | `templates/SKILL-template.md` |

### Cluster 3: Preset Packs (`--pack <name>`)

| Pack Name | Command | Included Local Skills | Included Upstream Skills (Auto-Synced via `npx`) |
| :--- | :--- | :--- | :--- |
| **`adk`** | `--pack adk` | `gcp-sovereign-arch` | `google-agents-cli-workflow`, `google-agents-cli-adk-code`, `google-agents-cli-deploy`, `google-agents-cli-eval`, `google-agents-cli-observability`, `google-agents-cli-publish`, `google-agents-cli-scaffold` (pinned to `google/agents-cli@v0.4.0`) |
| **`arch`** | `--pack arch` | `gcp-sovereign-arch`, `documentation-and-adrs`, `sdlc-and-portal`, `image-gen`, `continuous-alignment` | *(none — 100% local)* |
| **`devrel`** | `--pack devrel` | `codelab`, `google-oss`, `sdlc-and-portal`, `image-gen` | *(none — 100% local)* |
| **`audit`** | `--pack audit` | `verify`, `code-review-and-quality` | `debugging-and-error-recovery`, `doubt-driven-development`, `security-and-hardening` (from `addyosmani/agent-skills`) |

`skills.manifest.json` is the source of truth for pack contents; if this table and the manifest disagree, trust the manifest and fix this table.

### Routing Examples (Request -> Skill)

| User Request | Route To | Why Not the Neighbor |
| :--- | :--- | :--- |
| "I have a rough idea for an agent governance tool" | `idea-refine` | No direction chosen yet, so `grill-and-spec` would lock in a premature spec. |
| "Spec out the ticket summarizer we agreed on" | `grill-and-spec` | Direction is chosen; divergent ideation would waste turns. |
| "Review this PR before I merge" | `code-review-and-quality` | `verify` gates *your own* completion claim; review judges a diff against code-health axes. |
| "Is this task actually done?" | `verify` | Needs Stage 1 `verify_static.py` plus blinded evidence, not a style review. |
| "Commit this messy working tree" | `git-workflow-and-versioning` | Splitting and secret-scanning are VCS mechanics, not review. |
| "This readout sounds like AI wrote it" | `unslop` | Fact-preserving prose cleanup; `code-review-and-quality` does not touch narrative. |
| "Write Terraform for a VPC-SC perimeter" | Attach `gcp-sovereign-arch` (or `--pack arch`) | Domain conventions live in the JIT skill; do not improvise from memory. |
| "Record why we chose Spanner over AlloyDB" | Attach `documentation-and-adrs` | Single architectural decision record (MADR) or API docstring, not a multi-file customer portal. |
| "Draft a PRD/Executive Readout and package the docs into a single HTML file" | Attach `sdlc-and-portal` | Covers SDLC deliverable templates (`prd`, `design-doc`, `exec-readout`) and `compile_portal.py`. |
| "Build a hands-on workshop for the customer" | Attach `--pack devrel` | Bundles `codelab`, `sdlc-and-portal`, `google-oss`, and `image-gen` together. |
| "Why are my skills missing after switching networks?" | `sync` | Symlink health and corp overlays are `sync`'s job; `catalog` only routes. |

If a request spans two rows (for example, "refine this idea and then spec it"), run the skills in sequence and hand off explicitly rather than blending them.

---

## 3. Open Knowledge Format (OKF v0.2) Indexing Protocol

When asked to index a repository's documentation or knowledge base for AI agents (full schema and a complete example in [references/okf-spec.md](references/okf-spec.md)):
1. Scan target Markdown files and extract their primary purpose, positive triggers (`Use when`), negative boundaries (`Don't use for`), and relative path. Skip generated, vendored, and `node_modules/` content.
2. Generate `INDEX.okf.md` at the root of the indexed directory, starting with YAML frontmatter (`okf_version: "0.2"`, `generated_at`, `scope`) followed by one `## Cluster:` table per topic mapping intent to file paths. Keep it under 100 lines; split into per-cluster sub-indexes beyond that.
3. Use paths relative to `INDEX.okf.md` so links survive moving or cloning the repository.
4. Validate the generated index (the `verify` skill sits next to `catalog` in the same global skills directory):
   ```bash
   python3 <skill-dir>/../verify/scripts/verify_static.py --mode okf INDEX.okf.md
   ```
   `<skill-dir>` is the directory containing this `SKILL.md`; the `..` hop works whether `<skill-dir>` is the global symlink or the repository path.

## Common Rationalizations

| Rationalization | Reality |
| :--- | :--- |
| "I'll just link all 17 skills globally so I never have to route" | Loading all domain skills globally bloats every session's system prompt and causes trigger collisions. Keep Cluster 2 JIT. |
| "I don't know where `fde-agent-kit` is cloned on this machine" | Use the `$SKILLS_HOME` loop in Section 1; `sync_skills.py` resolves its own symlink back to `fde-agent-kit` automatically. |
| "I can Improvise the Terraform / ADK / Codelab structure without attaching the skill" | Improvised outputs miss deterministic gates (`verify_static.py`, CFF standards, checkpoint blocks). Attach the JIT skill first. |

## Red Flags

- Guessing domain conventions (VPC-SC Terraform, ADK `root_agent`, MADR numbering, HTML portals) instead of attaching the corresponding Cluster 2 JIT skill
- Copying skill files into a customer repository instead of symlinking via `sync_skills.py --project`
- Generating an OKF index without `Use when` / `Don't use for` routing boundaries
- Recommending a pack or skill name that does not appear in `skills.manifest.json` (check the manifest before routing)

## Verification

- [ ] Identified the minimal set of Cluster 2 skills or Cluster 3 pack needed for the active task
- [ ] Attached JIT skills via `sync_skills.py --project <dir>` (which auto-updates `.git/info/exclude`)
- [ ] If an `INDEX.okf.md` was generated, it passed `verify_static.py --mode okf`
