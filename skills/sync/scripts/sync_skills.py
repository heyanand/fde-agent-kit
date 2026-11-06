#!/usr/bin/env python3
# Copyright 2026 Hemanand Rajendran
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Global & JIT Project Skill Synchronization Engine (sync_skills.py).

Manages global agent skill symlinks across harnesses (Google Antigravity,
Gemini CLI, Claude Code, OpenAI Codex), auto-detects corp vs. off-corp
environments via skills.manifest.local.json, prunes dangling symlinks,
optionally links global AGENTS.md rules, and bootstraps project-scoped JIT
skills or packs without file duplication.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
from typing import Any


SKILL_NAME_RE = re.compile(r"^[a-z0-9-]+$")
# Corp overlay and link names may also use underscores (e.g. fde_charter); still no '/', '..', or leading dot.
LINK_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")


def find_repo_root() -> Path:
    """Resolve the fde-agent-kit root even when invoked through a symlink."""
    current = Path(__file__).resolve().parent
    for candidate in [current, *current.parents]:
        if (candidate / "skills.manifest.json").is_file():
            return candidate
    return Path(__file__).resolve().parents[3]


REPO_ROOT = find_repo_root()
MANIFEST_PATH = REPO_ROOT / "skills.manifest.json"
LOCAL_MANIFEST_PATH = REPO_ROOT / "skills.manifest.local.json"
SKILLS_DIR = REPO_ROOT / "skills"
RULES_FILE = REPO_ROOT / "rules" / "AGENTS.md"


def get_global_targets(manifest: dict[str, Any]) -> list[Path]:
    raw = manifest.get("harnesses", {}).get(
        "global_skill_targets",
        [
            "~/.gemini/config/skills",
            "~/.gemini/skills",
            "~/.claude/skills",
            "~/.codex/skills",
        ],
    )
    return [Path(p).expanduser() for p in raw]


def get_global_rule_targets(manifest: dict[str, Any]) -> list[Path]:
    raw = manifest.get("harnesses", {}).get(
        "global_rule_targets",
        ["~/.gemini/GEMINI.md", "~/.claude/CLAUDE.md", "~/.codex/AGENTS.md"],
    )
    return [Path(p).expanduser() for p in raw]


def get_project_targets(manifest: dict[str, Any], project_root: Path) -> list[Path]:
    raw = manifest.get("harnesses", {}).get(
        "project_skill_targets",
        [".gemini/skills", ".claude/skills", ".codex/skills", ".agents/skills"],
    )
    return [project_root / rel for rel in raw]


def get_upstream_cache_dir(manifest: dict[str, Any]) -> Path:
    raw = manifest.get("harnesses", {}).get(
        "upstream_cache_dir",
        "~/.cache/fde-agent-kit/upstream/skills",
    )
    return Path(raw).expanduser()


def _read_json(path: Path) -> dict[str, Any]:
    """Read a JSON object from path, exiting with a readable error on malformed input."""
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as exc:
        sys.exit(f"Error: Malformed JSON in {path} (line {exc.lineno}, column {exc.colno}): {exc.msg}")
    if not isinstance(data, dict):
        sys.exit(f"Error: Expected a JSON object at the top level of {path}.")
    return data


def load_manifest(
    manifest_path: Path = MANIFEST_PATH,
    local_override_path: Path | None = None,
) -> dict[str, Any]:
    if not manifest_path.exists():
        sys.exit(f"Error: Manifest not found at {manifest_path}")
    manifest: dict[str, Any] = _read_json(manifest_path)

    override_file = local_override_path
    if override_file is None:
        env_override = os.environ.get("FDE_LOCAL_MANIFEST")
        if env_override:
            override_file = Path(env_override)
        else:
            rel_name = manifest.get("corp_layer", {}).get(
                "local_override_file", "skills.manifest.local.json"
            )
            override_file = manifest_path.parent / rel_name

    if override_file and override_file.is_file():
        local_data = _read_json(override_file)
        if isinstance(local_data.get("corp_layer"), dict):
            merged_corp = dict(manifest.get("corp_layer", {}))
            merged_corp.update(local_data["corp_layer"])
            manifest["corp_layer"] = merged_corp
    return manifest


def is_corp_mounted(manifest: dict[str, Any]) -> bool:
    corp_cfg = manifest.get("corp_layer", {})
    check_paths: list[str] = list(corp_cfg.get("mount_check_paths", []))
    single = corp_cfg.get("mount_check_path")
    if single and single not in check_paths:
        check_paths.append(single)
    return any(Path(p).is_dir() for p in check_paths if p)


def validate_skill_name(skill_name: str) -> bool:
    return bool(SKILL_NAME_RE.match(skill_name))


def validate_link_name(link_name: str) -> bool:
    """Looser check for corp overlay and detach names: allows underscores, rejects path syntax."""
    return bool(LINK_NAME_RE.match(link_name))


def find_upstream_source(
    skill_name: str,
    manifest: dict[str, Any] | None,
) -> tuple[str, str] | None:
    """Return (repo, ref) if skill_name is registered in manifest upstream_sources."""
    if not manifest:
        return None
    for source in manifest.get("upstream_sources", []):
        if skill_name in source.get("skills", []):
            return source["repo"], source.get("ref", "")
    return None


def pull_single_upstream_skill(
    repo: str,
    ref: str,
    skill_name: str,
    cache_dir: Path,
    dry_run: bool = False,
) -> bool:
    """Pull a single skill from an upstream repo via npx skills into cache_dir."""
    staging_root = cache_dir.parent
    repo_spec = f"{repo}@{ref}" if ref else repo
    cmd = ["npx", "-y", "skills", "add", repo_spec, "--skill", skill_name]
    if dry_run:
        print(f"  [DRY-RUN] Would pull missing upstream skill in {staging_root}: {' '.join(cmd)}")
        return True

    cache_dir.mkdir(parents=True, exist_ok=True)
    print(f"  [UPSTREAM PULL] Fetching skill '{skill_name}' via: {' '.join(cmd)}")
    try:
        proc = subprocess.run(cmd, cwd=str(staging_root), check=False)
    except FileNotFoundError:
        print("  [ERROR] 'npx' not found on PATH. Install Node.js (>=18) to pull upstream skills.")
        return False
    if proc.returncode != 0:
        print(f"  [ERROR] '{' '.join(cmd)}' exited with code {proc.returncode}.")
        return False

    dest = cache_dir / skill_name
    for rel_stage in (".agents/skills", ".gemini/skills", ".claude/skills"):
        staged_candidate = staging_root / rel_stage / skill_name
        if not staged_candidate.is_dir() or staged_candidate.resolve() == dest.resolve():
            continue
        # Replace any stale cached copy so --pull-upstream picks up the pinned ref.
        if dest.is_symlink() or dest.is_file():
            dest.unlink()
        elif dest.is_dir():
            shutil.rmtree(dest)
        shutil.copytree(staged_candidate, dest, symlinks=True)
        break

    return (dest / "SKILL.md").is_file()


def resolve_skill_source(
    skill_name: str,
    manifest: dict[str, Any] | None = None,
    auto_pull: bool = False,
    dry_run: bool = False,
) -> Path | None:
    """Resolve a skill directory from repo skills/ or upstream cache (auto-pulling if configured)."""
    if not validate_skill_name(skill_name):
        return None
    local_candidate = SKILLS_DIR / skill_name
    if (local_candidate / "SKILL.md").is_file():
        return local_candidate
    cache_dir = (
        get_upstream_cache_dir(manifest)
        if manifest
        else Path("~/.cache/fde-agent-kit/upstream/skills").expanduser()
    )
    upstream_candidate = cache_dir / skill_name
    if (upstream_candidate / "SKILL.md").is_file():
        return upstream_candidate

    if auto_pull and manifest:
        upstream_info = find_upstream_source(skill_name, manifest)
        if upstream_info:
            repo, ref = upstream_info
            if pull_single_upstream_skill(repo, ref, skill_name, cache_dir, dry_run=dry_run):
                return upstream_candidate
    return None


def safe_symlink(src: Path, dest: Path, dry_run: bool = False) -> str:
    """Idempotently link dest -> src without clobbering real directories.

    Returns one of: 'created', 'updated', 'unchanged', 'conflict'.
    """
    if dest.is_symlink():
        try:
            if dest.resolve(strict=True) == src.resolve(strict=True):
                return "unchanged"
        except (FileNotFoundError, RuntimeError):
            pass
        if not dry_run:
            dest.unlink(missing_ok=True)
            dest.symlink_to(src)
        return "updated"

    if dest.exists():
        print(f"  [CONFLICT] Existing non-symlink at {dest}; skipping to preserve local files.")
        return "conflict"

    if not dry_run:
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.symlink_to(src)
    return "created"


def audit_directory(target_dir: Path) -> tuple[list[tuple[str, Path]], list[Path]]:
    """Return (valid_links, broken_links) inside target_dir."""
    valid: list[tuple[str, Path]] = []
    broken: list[Path] = []
    if not target_dir.exists():
        return valid, broken
    for entry in sorted(target_dir.iterdir()):
        if entry.is_symlink():
            try:
                resolved = entry.resolve(strict=True)
                valid.append((entry.name, resolved))
            except (FileNotFoundError, RuntimeError):
                broken.append(entry)
        elif entry.is_dir() and (entry / "SKILL.md").is_file():
            valid.append((entry.name, entry))
    return valid, broken


def prune_broken_links(target_dirs: list[Path], dry_run: bool = False) -> int:
    pruned = 0
    for d in target_dirs:
        _, broken = audit_directory(d)
        for b in broken:
            if dry_run:
                print(f"  [DRY-RUN] Would prune broken symlink: {b}")
            else:
                b.unlink(missing_ok=True)
                print(f"  [PRUNED] Removed broken symlink: {b}")
            pruned += 1
    return pruned


def sync_global_rules(manifest: dict[str, Any], dry_run: bool = False) -> None:
    if not RULES_FILE.is_file():
        print(f"  [WARN] Global rules file missing at {RULES_FILE}")
        return
    rule_targets = get_global_rule_targets(manifest)
    print(f"\n=== Syncing Global Operating Rules ({RULES_FILE.name}) ===")
    for dest in rule_targets:
        if dest.is_dir() and not dest.is_symlink():
            print(f"  [CONFLICT] {dest} is a directory, not a rules file; skipping.")
            continue
        if dest.is_symlink() and not dry_run:
            try:
                previous = os.readlink(dest)
            except OSError:
                previous = "?"
            if Path(previous) != RULES_FILE and dest.resolve() != RULES_FILE.resolve():
                print(f"  [INFO] Replacing existing symlink {dest} -> {previous}")
        if dest.exists() and not dest.is_symlink():
            backup = dest.with_suffix(dest.suffix + ".bak")
            if backup.exists():
                # Never clobber an earlier backup; add a timestamp suffix instead.
                backup = dest.with_suffix(f"{dest.suffix}.bak.{time.strftime('%Y%m%d-%H%M%S')}")
            if dry_run:
                print(f"  [DRY-RUN] Would back up {dest} -> {backup} and link {RULES_FILE}")
                continue
            shutil.copy2(dest, backup)
            dest.unlink()
            print(f"  [BACKUP] Saved existing {dest} -> {backup}")
        status = safe_symlink(RULES_FILE, dest, dry_run=dry_run)
        prefix = "[DRY-RUN] " if dry_run else ""
        if status in ("created", "updated"):
            print(f"  {prefix}[RULE LINKED] {dest} -> {RULES_FILE}")
        elif status == "unchanged":
            print(f"  {prefix}[RULE OK] {dest} (already linked)")


def sync_global(
    manifest: dict[str, Any],
    prune: bool = False,
    sync_rules: bool = False,
    dry_run: bool = False,
) -> None:
    core_skills: list[str] = manifest.get("clusters", {}).get("core", {}).get("skills", [])
    corp_mounted = is_corp_mounted(manifest)
    global_targets = get_global_targets(manifest)

    if not dry_run:
        for target_dir in global_targets:
            target_dir.mkdir(parents=True, exist_ok=True)

    if prune:
        prune_broken_links(global_targets, dry_run=dry_run)

    print(f"=== Syncing Global Core Skills ({len(core_skills)} skills) ===")
    for skill_name in core_skills:
        src = resolve_skill_source(skill_name, manifest)
        if not src:
            print(f"  [WARN] Core skill '{skill_name}' not found at {SKILLS_DIR / skill_name}")
            continue
        statuses = [safe_symlink(src, td / skill_name, dry_run=dry_run) for td in global_targets]
        prefix = "[DRY-RUN] " if dry_run else ""
        if any(s in ("created", "updated") for s in statuses):
            print(f"  {prefix}[LINKED] {skill_name} -> {src}")
        elif all(s == "unchanged" for s in statuses):
            print(f"  {prefix}[OK] {skill_name} (already linked)")

    if corp_mounted:
        corp_skills = manifest.get("corp_layer", {}).get("skills", [])
        print(f"\n=== Corp Environment Detected: Linking {len(corp_skills)} Corp Skills ===")
        for item in corp_skills:
            name = str(item.get("name", "")) if isinstance(item, dict) else ""
            raw_path = item.get("path") if isinstance(item, dict) else None
            if not validate_link_name(name) or not raw_path:
                print(
                    f"  [WARN] Skipping malformed corp_layer skill entry {item!r}: "
                    "requires 'name' matching ^[a-z0-9][a-z0-9_-]*$ and a 'path'."
                )
                continue
            src_path = Path(raw_path).expanduser()
            optional = bool(item.get("optional", False))
            if not src_path.is_dir():
                if not optional:
                    print(f"  [WARN] Corp skill path missing: {src_path}")
                continue
            statuses = [safe_symlink(src_path, td / name, dry_run=dry_run) for td in global_targets]
            prefix = "[DRY-RUN] " if dry_run else ""
            if any(s in ("created", "updated") for s in statuses):
                print(f"  {prefix}[CORP LINKED] {name} -> {src_path}")
            elif all(s == "unchanged" for s in statuses):
                print(f"  {prefix}[CORP OK] {name} (already linked)")
    else:
        print("\n=== Off-Corp Environment Detected: Skipping corp-only symlinks ===")
        if not prune:
            print("  Tip: Run with --prune to remove any dangling corp symlinks.")

    if sync_rules:
        sync_global_rules(manifest, dry_run=dry_run)


def _resolve_git_dir(project_root: Path) -> Path | None:
    """Return the git directory holding info/exclude, handling worktree/submodule `.git` files."""
    dot_git = project_root / ".git"
    if dot_git.is_dir():
        return dot_git
    if not dot_git.is_file():
        return None
    first_line = dot_git.read_text(encoding="utf-8").strip().splitlines()[:1]
    if not first_line or not first_line[0].startswith("gitdir:"):
        return None
    git_dir = Path(first_line[0].split(":", 1)[1].strip())
    if not git_dir.is_absolute():
        git_dir = (project_root / git_dir).resolve()
    # Linked worktrees share info/exclude with the main repository via `commondir`.
    commondir_file = git_dir / "commondir"
    if commondir_file.is_file():
        common = Path(commondir_file.read_text(encoding="utf-8").strip())
        git_dir = common if common.is_absolute() else (git_dir / common).resolve()
    return git_dir if git_dir.is_dir() else None


def ensure_git_exclude(project_root: Path, rel_dirs: list[str], dry_run: bool = False) -> None:
    """Ensure JIT skill directories are ignored via .git/info/exclude in git repos."""
    git_dir = _resolve_git_dir(project_root)
    if git_dir is None:
        return
    exclude_file = git_dir / "info" / "exclude"
    existing_lines: set[str] = set()
    if exclude_file.is_file():
        existing_lines = {
            line.strip()
            for line in exclude_file.read_text(encoding="utf-8").splitlines()
            if line.strip()
        }
    missing = [
        f"/{d.strip('/')}/"
        for d in rel_dirs
        if f"/{d.strip('/')}/" not in existing_lines and d not in existing_lines
    ]
    if not missing:
        return
    if dry_run:
        print(f"  [DRY-RUN] Would add {', '.join(missing)} to {exclude_file}")
        return
    exclude_file.parent.mkdir(parents=True, exist_ok=True)
    with exclude_file.open("a", encoding="utf-8") as f:
        f.write("\n# fde-agent-kit JIT skill links\n")
        for entry in missing:
            f.write(f"{entry}\n")


def _is_kit_managed_link(link: Path, manifest: dict[str, Any]) -> bool:
    """True if link points into this kit's skills/ dir or the upstream cache (even if dangling)."""
    try:
        raw_target = Path(os.readlink(link))
    except OSError:
        return False
    if not raw_target.is_absolute():
        raw_target = link.parent / raw_target
    target = Path(os.path.abspath(raw_target))
    roots = [SKILLS_DIR, get_upstream_cache_dir(manifest)]
    for root in roots:
        for candidate_root in {Path(os.path.abspath(root)), root.resolve()}:
            if target == candidate_root or candidate_root in target.parents:
                return True
    return False


def detach_project_skills(
    manifest: dict[str, Any],
    project_path: Path,
    detach_skills: list[str],
    dry_run: bool = False,
) -> None:
    project_root = project_path.resolve()
    project_targets = get_project_targets(manifest, project_root)
    detach_all = "all" in detach_skills
    invalid_names = [s for s in detach_skills if s != "all" and not validate_link_name(s)]
    if invalid_names:
        sys.exit(
            f"Error: Invalid skill name(s) for --detach: {', '.join(invalid_names)}. "
            "Must match ^[a-z0-9][a-z0-9_-]*$."
        )
    removed = 0
    for pt in project_targets:
        if not pt.exists():
            continue
        for entry in sorted(pt.iterdir()):
            if not entry.is_symlink() or not (detach_all or entry.name in detach_skills):
                continue
            if detach_all and not _is_kit_managed_link(entry, manifest):
                # 'all' only removes links this kit created; user-authored links stay.
                print(f"  [SKIP] {entry} is not managed by fde-agent-kit; leaving it in place.")
                continue
            if dry_run:
                print(f"  [DRY-RUN] Would detach symlink: {entry}")
            else:
                entry.unlink(missing_ok=True)
                print(f"  [DETACHED] Removed symlink: {entry}")
            removed += 1
    if removed == 0:
        print("  [INFO] No matching JIT skill symlinks found to detach.")


def sync_project(
    manifest: dict[str, Any],
    project_path: Path,
    skills: list[str],
    packs: list[str],
    dry_run: bool = False,
) -> None:
    requested: list[str] = []
    for s in skills:
        if not validate_skill_name(s):
            sys.exit(
                f"Error: Invalid skill name '{s}'. Skill names must match ^[a-z0-9-]+$."
            )
        requested.append(s)

    packs_cfg = manifest.get("packs", {})
    for pack_name in packs:
        if pack_name not in packs_cfg:
            valid_packs = ", ".join(sorted(packs_cfg.keys()))
            sys.exit(f"Error: Unknown pack '{pack_name}'. Valid packs: {valid_packs}")
        pack = packs_cfg[pack_name]
        requested.extend(pack.get("local_skills", []))
        requested.extend(pack.get("upstream_skills", []))

    seen: set[str] = set()
    unique_skills = [s for s in requested if not (s in seen or seen.add(s))]

    missing_skills: list[str] = []
    resolved_pairs: list[tuple[str, Path]] = []
    for skill_name in unique_skills:
        src = resolve_skill_source(
            skill_name,
            manifest,
            auto_pull=True,
            dry_run=dry_run,
        )
        if not src:
            missing_skills.append(skill_name)
        else:
            resolved_pairs.append((skill_name, src))

    if missing_skills:
        cache_dir = get_upstream_cache_dir(manifest)
        sys.exit(
            f"Error: Skill(s) not found locally or in {cache_dir} (and could not be pulled from upstream): "
            f"{', '.join(missing_skills)}."
        )

    project_root = project_path.resolve()
    project_targets = get_project_targets(manifest, project_root)
    if not dry_run:
        for pt in project_targets:
            pt.mkdir(parents=True, exist_ok=True)

    rel_dirs = manifest.get("harnesses", {}).get(
        "project_skill_targets",
        [".gemini/skills", ".claude/skills", ".codex/skills", ".agents/skills"],
    )
    ensure_git_exclude(project_root, rel_dirs, dry_run=dry_run)

    print(f"=== Bootstrapping Project JIT Skills in {project_root} ===")
    for skill_name, src in resolved_pairs:
        statuses = [safe_symlink(src, pt / skill_name, dry_run=dry_run) for pt in project_targets]
        prefix = "[DRY-RUN] " if dry_run else ""
        if any(s in ("created", "updated") for s in statuses):
            print(f"  {prefix}[JIT LINKED] {skill_name} -> {src}")
        elif all(s == "unchanged" for s in statuses):
            print(f"  {prefix}[JIT OK] {skill_name} (already linked)")


def pull_upstream(manifest: dict[str, Any], dry_run: bool = False) -> None:
    sources = manifest.get("upstream_sources", [])
    cache_dir = get_upstream_cache_dir(manifest)
    print(f"=== Pulling Upstream Skills into {cache_dir} ===")
    if not dry_run:
        cache_dir.mkdir(parents=True, exist_ok=True)

    failures: list[str] = []
    for source in sources:
        repo = source["repo"]
        ref = source.get("ref", "")
        repo_spec = f"{repo}@{ref}" if ref else repo
        for skill_name in source.get("skills", []):
            ok = pull_single_upstream_skill(repo, ref, skill_name, cache_dir, dry_run=dry_run)
            if not ok:
                failures.append(f"{repo_spec}:{skill_name}")

    if failures:
        sys.exit(f"Error: Failed to pull upstream skills: {', '.join(failures)}")


def print_audit_report(manifest: dict[str, Any]) -> None:
    corp_mounted = is_corp_mounted(manifest)
    global_targets = get_global_targets(manifest)
    print("=================================================================")
    print(" FDE Agent Kit — Skill Symlink & Environment Audit")
    print("=================================================================")
    print(f"Repository Root : {REPO_ROOT}")
    print(f"Corp Layer      : {'MOUNTED' if corp_mounted else 'OFF-CORP (unmounted or unconfigured)'}")

    core_skills = set(manifest.get("clusters", {}).get("core", {}).get("skills", []))
    jit_skills = set(manifest.get("clusters", {}).get("jit", {}).get("skills", []))
    print(f"Repo Inventory  : {len(core_skills)} Global Core | {len(jit_skills)} Project JIT")

    for target_dir in global_targets:
        valid, broken = audit_directory(target_dir)
        print(f"\nTarget Harness  : {target_dir}")
        print(f"  Active Skills ({len(valid)}):")
        for name, resolved in valid:
            tag = "[CORE]" if name in core_skills else ("[JIT]" if name in jit_skills else "[EXT/CORP]")
            print(f"    - {name:<32} {tag:<10} -> {resolved}")
        if broken:
            print(f"  BROKEN Symlinks ({len(broken)}) — run with `--prune --fix` to clean:")
            for b in broken:
                print(f"    ! {b.name} (dangling target)")
        else:
            print("  Broken Symlinks: 0 (Clean)")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Audit, prune, and synchronize global and project-scoped agent skills."
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Ensure all Global Core skills (and Corp skills when mounted) are symlinked.",
    )
    parser.add_argument(
        "--prune",
        action="store_true",
        help="Remove broken/dangling symlinks (e.g., corp links when off-corp).",
    )
    parser.add_argument(
        "--sync-rules",
        action="store_true",
        help="Symlink rules/AGENTS.md to ~/.gemini/GEMINI.md, ~/.claude/CLAUDE.md, and ~/.codex/AGENTS.md.",
    )
    parser.add_argument(
        "--project",
        type=Path,
        help="Target project workspace path for Just-In-Time (JIT) skill attachment.",
    )
    parser.add_argument(
        "--skills",
        type=str,
        default="",
        help="Comma-separated list of skills to JIT-link into --project.",
    )
    parser.add_argument(
        "--pack",
        type=str,
        default="",
        help="Comma-separated pack names (adk, arch, devrel, audit) to JIT-link into --project.",
    )
    parser.add_argument(
        "--detach",
        type=str,
        default="",
        help="Comma-separated skill names (or 'all') to detach from --project.",
    )
    parser.add_argument(
        "--pull-upstream",
        action="store_true",
        help="Fetch/update pinned upstream skills from skills.manifest.json via npx skills.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview all changes without modifying the filesystem.",
    )

    args = parser.parse_args(argv)
    manifest = load_manifest()

    if (args.skills or args.pack or args.detach) and not args.project:
        sys.exit("Error: --skills, --pack, and --detach require --project <path>.")

    did_action = False

    if args.pull_upstream:
        pull_upstream(manifest, dry_run=args.dry_run)
        did_action = True

    if args.fix:
        sync_global(
            manifest,
            prune=args.prune,
            sync_rules=args.sync_rules,
            dry_run=args.dry_run,
        )
        did_action = True
    elif args.prune:
        prune_broken_links(get_global_targets(manifest), dry_run=args.dry_run)
        did_action = True
    elif args.sync_rules:
        sync_global_rules(manifest, dry_run=args.dry_run)
        did_action = True

    if args.project:
        if args.detach:
            detach_list = [s.strip() for s in args.detach.split(",") if s.strip()]
            detach_project_skills(manifest, args.project, detach_list, dry_run=args.dry_run)
        skill_list = [s.strip() for s in args.skills.split(",") if s.strip()]
        pack_list = [p.strip() for p in args.pack.split(",") if p.strip()]
        if not skill_list and not pack_list and not args.detach:
            sys.exit(
                "Error: Provide --skills <s1,s2>, --pack <pack>, or --detach <s1|all> with --project."
            )
        if skill_list or pack_list:
            sync_project(
                manifest,
                args.project,
                skill_list,
                pack_list,
                dry_run=args.dry_run,
            )
        did_action = True

    if not did_action:
        print_audit_report(manifest)


if __name__ == "__main__":
    main()
