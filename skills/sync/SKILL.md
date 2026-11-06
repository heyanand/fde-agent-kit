---
name: sync
description: >-
  Audits, prunes, and synchronizes global and project-scoped agent skill
  symlinks across Google Antigravity, Gemini CLI, Claude Code, and OpenAI Codex,
  and manages corp vs. off-corp skill overlays. Use when setting up a machine,
  switching between corp and off-corp networks, pruning broken symlinks, or
  attaching/detaching JIT skills and packs in a project workspace. Don't use for
  authoring new skills (use skill-forge) or for deciding which skill fits a task
  (use catalog).
---

# Skill Synchronization & Environment Manager (`sync`)

Wraps `<skill-dir>/scripts/sync_skills.py` to keep global and project-scoped skill symlinks clean across all agent harnesses without duplicating files.

## Supported Harnesses & Directory Layout

`sync_skills.py` reads `skills.manifest.json` (and optional gitignored `skills.manifest.local.json`) and manages:
- **Global Skill Targets:**
  - Google Antigravity: `~/.gemini/config/skills`
  - Gemini CLI: `~/.gemini/skills`
  - Claude Code: `~/.claude/skills`
  - OpenAI Codex: `~/.codex/skills`
- **Global Rule Targets (`--sync-rules`):**
  - `~/.gemini/GEMINI.md` -> `rules/AGENTS.md` (an existing regular file is backed up to `.bak`; if a `.bak` already exists, a timestamped `.bak.<YYYYmmdd-HHMMSS>` is written instead, so no earlier backup is ever overwritten)
  - `~/.claude/CLAUDE.md` -> `rules/AGENTS.md`
  - `~/.codex/AGENTS.md` -> `rules/AGENTS.md`
- **Project JIT Targets (`--project <dir>`):**
  - `<dir>/.gemini/skills`, `<dir>/.claude/skills`, `<dir>/.codex/skills`, and `<dir>/.agents/skills` (automatically added to the repository's `info/exclude` so symlinks never pollute `git status`; linked worktrees and submodules whose `.git` is a file are resolved to the shared git directory).
- **Isolated Upstream Cache:**
  - `~/.cache/fde-agent-kit/upstream/skills` (isolated from `~/.agents/skills` so Gemini CLI and Codex do not globally auto-load upstream pack skills).

---

## Core Workflows & Commands

In all commands below, `<skill-dir>` is the directory containing this `SKILL.md` (e.g., `~/.gemini/config/skills/sync` or `skills/sync` inside `fde-agent-kit`).

### 1. Audit Environment & Symlink Health (Read-Only)
```bash
python3 <skill-dir>/scripts/sync_skills.py
```
Reports corp mount status (`MOUNTED` vs. `OFF-CORP`), active skills per harness tagged `[CORE]`, `[JIT]`, or `[EXT/CORP]`, and any dangling symlinks.

### 2. Repair Global Core Links, Prune Broken Links & Sync Rules
```bash
# Preview changes first without modifying disk
python3 <skill-dir>/scripts/sync_skills.py --fix --prune --sync-rules --dry-run

# Apply changes
python3 <skill-dir>/scripts/sync_skills.py --fix --prune --sync-rules
```
- Links all 8 **Cluster 1 Global Core** skills into every global harness target.
- If a corp mount is configured in `skills.manifest.local.json` and mounted on disk, links configured corp skills (`gdocs`, `gdrive`, `gsheets`, `gslides`, and optional `ai_fde` skills).
- If off-corp, `--prune` cleanly removes dangling corp symlinks so agent discovery never stalls on unreachable network paths.

### 3. Attach or Detach Project-Scoped JIT Skills & Packs
```bash
# Attach a preset pack (adk | arch | devrel | audit) into a project workspace
python3 <skill-dir>/scripts/sync_skills.py --project /path/to/workspace --pack arch

# Attach specific Cluster 2 JIT skills
python3 <skill-dir>/scripts/sync_skills.py --project /path/to/workspace --skills gcp-sovereign-arch,sdlc-and-portal

# Detach specific JIT skills (or 'all') when finished
python3 <skill-dir>/scripts/sync_skills.py --project /path/to/workspace --detach gcp-sovereign-arch,sdlc-and-portal
python3 <skill-dir>/scripts/sync_skills.py --project /path/to/workspace --detach all
```
- `--detach all` removes only symlinks that point into this kit's `skills/` directory or the upstream cache; symlinks you created by hand are reported as `[SKIP]` and left in place. Naming a skill explicitly (`--detach sdlc-and-portal`) removes that symlink regardless of its target.
- Add `--dry-run` to any attach or detach command to preview it first.

### 4. Configure Local Corp Overlay (`skills.manifest.local.json`)
Internal corp paths must never be committed to `skills.manifest.json`. To enable automatic corp skill linking on a corp workstation, copy `skills.manifest.local.example.json` to `skills.manifest.local.json` (which is gitignored) and populate `mount_check_paths` and `skills`.
- Each `corp_layer.skills` entry needs a `name` matching `^[a-z0-9][a-z0-9_-]*$` (underscores allowed, as in `fde_charter`; no `/`, `..`, or leading dot) and a `path`. Malformed entries are skipped with a `[WARN]` instead of aborting the run.
- Set `FDE_LOCAL_MANIFEST=/path/to/overlay.json` to point at an overlay stored outside the repository (for example, in a dotfiles repo).

### 5. Pull / Update Pinned Upstream Pack Skills
```bash
python3 <skill-dir>/scripts/sync_skills.py --pull-upstream
```
Note: When attaching `--pack adk` or `--pack audit` via `--project`, `sync_skills.py` automatically checks `~/.cache/fde-agent-kit/upstream/skills` and pulls any missing upstream skills via `npx -y skills add <repo>@<ref> --skill <name>` on demand. `--pull-upstream` replaces any cached copy with the freshly pulled pinned ref, so re-run it after bumping a `ref` in `skills.manifest.json`.

---

## Troubleshooting

- **`[CONFLICT] Existing non-symlink at ...`:** A real directory or file already exists at the destination path. `sync_skills.py` never deletes real directories; inspect and remove or move the directory manually if you want it replaced by a symlink.
- **`Error: Skill(s) not found ...`:** Verify the skill name matches `^[a-z0-9-]+$` and exists in `skills/` or `upstream_sources` in `skills.manifest.json`.
- **`[ERROR] 'npx' not found on PATH`:** Install Node.js 18+ (which provides `npx`), or attach only local skills with `--skills` until Node.js is available.
- **`Error: Malformed JSON in ... (line N, column M)`:** Fix the reported position in `skills.manifest.json` or `skills.manifest.local.json` (a trailing comma is the usual cause).
- **`[INFO] Replacing existing symlink ~/.gemini/GEMINI.md -> ...`:** `--sync-rules` found a rules symlink pointing somewhere else (for example, a dotfiles repo). The old target is printed so you can restore it if needed.

## Common Rationalizations

| Rationalization | Reality |
| :--- | :--- |
| "I'll `cp -r` the skill folder into the customer project" | Copying forks the skill, pollutes customer git status, and misses upstream bug fixes. Always symlink via `--project`. |
| "I'll put internal corp paths directly in `skills.manifest.json`" | Tracked internal paths fail `google-oss` sanitization and leak internal structure when pushed to GitHub. Use `skills.manifest.local.json`. |
| "I'll delete an existing directory in `~/.gemini/skills` automatically" | Automatically `rmtree`-ing a non-symlink directory risks destroying user-authored local skills. Report `[CONFLICT]` and skip. |

## Red Flags

- Running `cp -r` or `ln -s` manually instead of `sync_skills.py`
- Committing `.gemini/skills/` or `.claude/skills/` symlinks into a customer repository
- Leaving broken corp symlinks in `~/.gemini/config/skills` when working off-corp
- Passing `--skills` or `--pack` without `--project <path>`

## Verification

- [ ] `python3 <skill-dir>/scripts/sync_skills.py` reports `Broken Symlinks: 0 (Clean)` across all global harnesses
- [ ] All 8 Global Core skills are active in `~/.gemini/config/skills`, `~/.gemini/skills`, `~/.claude/skills`, and `~/.codex/skills`
- [ ] Project JIT links are listed in `<project>/.git/info/exclude`
