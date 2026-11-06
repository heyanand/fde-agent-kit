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
"""Unit, integration, and repo-hygiene test suite for fde-agent-kit.

Covers the 5 CLI scripts, the skill inventory and manifest contracts, the
negative paths of ``verify_static.py --mode skill``, and a publication
sanitization scan over every tracked file.
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "skills"
VERIFY_SCRIPT = SKILLS_DIR / "verify" / "scripts" / "verify_static.py"


def _load_module(name: str, rel_path: str):
    full_path = REPO_ROOT / rel_path
    spec = importlib.util.spec_from_file_location(name, full_path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


sync_skills = _load_module("sync_skills", "skills/sync/scripts/sync_skills.py")
distill_session = _load_module(
    "distill_session", "skills/continuous-alignment/scripts/distill_session.py"
)
compile_portal = _load_module("compile_portal", "skills/sdlc-and-portal/scripts/compile_portal.py")
image_gen = _load_module("image_gen", "skills/image-gen/scripts/image_gen.py")
verify_static = _load_module("verify_static", "skills/verify/scripts/verify_static.py")


class _QuietStdout(unittest.TestCase):
    """Silence CLI progress output so `unittest -v` stays readable."""

    def setUp(self) -> None:
        super().setUp()
        stack = contextlib.ExitStack()
        stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
        self.addCleanup(stack.close)


class TestSyncSkills(_QuietStdout):
    def test_find_repo_root_resolves_to_manifest(self) -> None:
        root = sync_skills.find_repo_root()
        self.assertEqual(root, REPO_ROOT)
        self.assertTrue((root / "skills.manifest.json").is_file())

    def test_fix_sync_rules_and_conflict_handling(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_home = Path(tmp) / "home"
            tmp_home.mkdir()
            # Pre-create a non-symlink directory to test conflict handling (R6)
            conflict_dir = tmp_home / ".gemini" / "skills" / "catalog"
            conflict_dir.mkdir(parents=True)
            (conflict_dir / "custom.txt").write_text("keep me", encoding="utf-8")

            # Pre-create a regular GEMINI.md file to test backup on --sync-rules (R2)
            gemini_md = tmp_home / ".gemini" / "GEMINI.md"
            gemini_md.parent.mkdir(parents=True, exist_ok=True)
            gemini_md.write_text("existing rules", encoding="utf-8")

            with mock.patch.dict(
                os.environ,
                {"HOME": str(tmp_home), "FDE_LOCAL_MANIFEST": "/nonexistent"},
            ):
                manifest = sync_skills.load_manifest()
                sync_skills.sync_global(manifest, prune=True, sync_rules=True)

            # Conflict directory must NOT be deleted or overwritten
            self.assertFalse(conflict_dir.is_symlink())
            self.assertTrue((conflict_dir / "custom.txt").is_file())

            # Other core skills must be symlinked across all 4 harnesses (C2 + Codex)
            for rel_target in (
                ".gemini/config/skills",
                ".gemini/skills",
                ".claude/skills",
                ".codex/skills",
            ):
                verify_link = tmp_home / rel_target / "verify"
                self.assertTrue(verify_link.is_symlink())
                self.assertEqual(verify_link.resolve(), REPO_ROOT / "skills" / "verify")

            # GEMINI.md, CLAUDE.md, and ~/.codex/AGENTS.md must be linked to rules/AGENTS.md
            self.assertTrue((tmp_home / ".gemini" / "GEMINI.md.bak").is_file())
            self.assertTrue(gemini_md.is_symlink())
            self.assertEqual(gemini_md.resolve(), REPO_ROOT / "rules" / "AGENTS.md")
            self.assertTrue((tmp_home / ".codex" / "AGENTS.md").is_symlink())
            self.assertEqual(
                (tmp_home / ".codex" / "AGENTS.md").resolve(),
                REPO_ROOT / "rules" / "AGENTS.md",
            )

    def test_project_jit_pack_audit_auto_pulls_missing_upstream_and_git_exclude(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            proj = Path(tmp) / "customer-repo"
            (proj / ".git" / "info").mkdir(parents=True)
            cache_dir = Path(tmp) / "cache" / "upstream" / "skills"
            manifest = sync_skills.load_manifest(local_override_path=Path("/nonexistent"))
            manifest["harnesses"]["upstream_cache_dir"] = str(cache_dir)

            def _fake_npx_run(cmd: list[str], cwd: str | None = None, check: bool = False):
                # Simulate `npx -y skills add <repo> --skill <skill_name>` writing to .agents/skills/<skill>
                skill_name = cmd[-1]
                staged = Path(cwd or tmp) / ".agents" / "skills" / skill_name
                staged.mkdir(parents=True, exist_ok=True)
                (staged / "SKILL.md").write_text(f"---\nname: {skill_name}\n---\n", encoding="utf-8")
                res = mock.MagicMock()
                res.returncode = 0
                return res

            with mock.patch.object(sync_skills.subprocess, "run", side_effect=_fake_npx_run) as m_run:
                sync_skills.sync_project(manifest, proj, skills=["sdlc-and-portal"], packs=["audit"])
                # Should have auto-pulled all 3 missing upstream audit skills via npx
                self.assertEqual(m_run.call_count, 3)

            # Verify both local ("sdlc-and-portal", "verify") and auto-pulled upstream ("security-and-hardening") linked
            for skill in ("sdlc-and-portal", "verify", "security-and-hardening", "doubt-driven-development"):
                for harness_dir in (
                    ".gemini/skills",
                    ".claude/skills",
                    ".codex/skills",
                    ".agents/skills",
                ):
                    self.assertTrue((proj / harness_dir / skill).is_symlink())

            # Verify .git/info/exclude updated
            exclude_text = (proj / ".git" / "info" / "exclude").read_text(encoding="utf-8")
            self.assertIn("/.gemini/skills/", exclude_text)
            self.assertIn("/.claude/skills/", exclude_text)
            self.assertIn("/.codex/skills/", exclude_text)

            # Detach 'sdlc-and-portal' and verify removal
            sync_skills.detach_project_skills(manifest, proj, ["sdlc-and-portal"])
            self.assertFalse((proj / ".gemini" / "skills" / "sdlc-and-portal").exists())

    def test_invalid_or_missing_skill_exits_nonzero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            proj = Path(tmp)
            manifest = sync_skills.load_manifest(local_override_path=Path("/nonexistent"))
            with self.assertRaises(SystemExit):
                sync_skills.sync_project(manifest, proj, skills=["../traversal"], packs=[])
            with self.assertRaises(SystemExit):
                sync_skills.sync_project(manifest, proj, skills=["nonexistent-skill"], packs=[])

    def test_cli_fix_links_underscore_corp_skills_and_rejects_traversal(self) -> None:
        """Corp overlay names like fde_charter must link; '../x' and '.hidden' must not."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            home = tmp_path / "home"
            home.mkdir()
            corp_root = tmp_path / "corp-mount"
            for name in ("fde_charter", "ai_native_sdlc", "x", ".hidden"):
                d = corp_root / "skills" / name
                d.mkdir(parents=True)
                (d / "SKILL.md").write_text(f"---\nname: {name}\n---\n", encoding="utf-8")
            overlay = tmp_path / "overlay.json"
            overlay.write_text(
                json.dumps(
                    {
                        "corp_layer": {
                            "mount_check_paths": [str(corp_root)],
                            "skills": [
                                {"name": n, "path": str(corp_root / "skills" / p)}
                                for n, p in (
                                    ("fde_charter", "fde_charter"),
                                    ("ai_native_sdlc", "ai_native_sdlc"),
                                    ("../x", "x"),
                                    (".hidden", ".hidden"),
                                )
                            ],
                        }
                    }
                ),
                encoding="utf-8",
            )
            env = {**os.environ, "HOME": str(home), "FDE_LOCAL_MANIFEST": str(overlay)}
            script = str(SKILLS_DIR / "sync" / "scripts" / "sync_skills.py")
            proc = subprocess.run(
                [sys.executable, script, "--fix"],
                env=env, capture_output=True, text=True, check=False, timeout=120,
            )
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

            targets = [home / ".gemini" / "config" / "skills", home / ".claude" / "skills"]
            for target in targets:
                for name in ("fde_charter", "ai_native_sdlc"):
                    with self.subTest(target=str(target), skill=name):
                        link = target / name
                        self.assertTrue(link.is_symlink(), proc.stdout)
                        self.assertEqual(link.resolve(), (corp_root / "skills" / name).resolve())
                with self.subTest(target=str(target), skill="rejected"):
                    self.assertFalse((target / ".hidden").exists())
                    self.assertFalse((target.parent / "x").exists())
            self.assertFalse(any(home.rglob("x")), "traversal entry escaped the target dir")

            # Off-corp: once the mount disappears, --prune removes the dangling corp links.
            shutil.rmtree(corp_root)
            proc = subprocess.run(
                [sys.executable, script, "--prune"],
                env=env, capture_output=True, text=True, check=False, timeout=120,
            )
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            for target in targets:
                self.assertFalse((target / "fde_charter").is_symlink(), proc.stdout)
                self.assertTrue((target / "verify").is_symlink())


class TestDistillSession(_QuietStdout):
    def test_adr_numbering_gap_never_overwrites_existing(self) -> None:
        """Regression test for C3: gap in ADR numbering must use max + 1 and open('x')."""
        with tempfile.TemporaryDirectory() as tmp:
            proj = Path(tmp)
            adr_dir = proj / "docs" / "decisions"
            adr_dir.mkdir(parents=True)
            (adr_dir / "0001-init.md").write_text("ADR 1", encoding="utf-8")
            adr3 = adr_dir / "0003-keep-me.md"
            adr3.write_text("DO NOT OVERWRITE", encoding="utf-8")

            created = distill_session.create_adr(proj, "New Queue Strategy")
            self.assertEqual(created.name, "0004-new-queue-strategy.md")
            self.assertEqual(adr3.read_text(encoding="utf-8"), "DO NOT OVERWRITE")
            self.assertIn("- **Status:** Proposed", created.read_text(encoding="utf-8"))
            self.assertTrue((adr_dir / "README.md").is_file())

    def test_non_ascii_adr_title_fallback_slug(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            proj = Path(tmp)
            created = distill_session.create_adr(proj, "🚀✨")
            self.assertEqual(created.name, "0001-decision-0001.md")

    def test_multi_harness_transcript_and_symlink_dedup(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            proj = Path(tmp)
            agents_md = proj / "AGENTS.md"
            agents_md.write_text("# Rules\nLine 2\n", encoding="utf-8")
            (proj / "GEMINI.md").symlink_to(agents_md)
            self.assertEqual(distill_session.check_budget(proj), 0)

            transcript = proj / "transcript.jsonl"
            events = [
                {"type": "USER_INPUT", "content": "Antigravity prompt 1"},
                {
                    "type": "PLANNER_RESPONSE",
                    "status": "ERROR",
                    "content": "Command failed",
                    "tool_calls": [{"name": "run_command", "arguments": {"CommandLine": "pytest"}}],
                },
                {"type": "user", "message": {"role": "user", "content": "Claude Code prompt 2"}},
                {
                    "type": "user",
                    "message": {
                        "role": "user",
                        "content": [{"type": "tool_result", "is_error": True, "content": "Exit code 1"}],
                    },
                },
            ]
            transcript.write_text(
                "\n".join(json.dumps(e) for e in events), encoding="utf-8"
            )
            summary = distill_session.analyze_transcript(transcript)
            self.assertEqual(len(summary["user_messages"]), 2)
            self.assertEqual(len(summary["failed_events"]), 2)


class TestCompilePortal(_QuietStdout):
    def test_script_breakout_escaped_and_duplicate_stems_disambiguated(self) -> None:
        """Regression test for C4: </script> inside Markdown must never break out of <script>."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dir_a = root / "a"
            dir_b = root / "b"
            dir_a.mkdir()
            dir_b.mkdir()
            md_a = dir_a / "README.md"
            md_b = dir_b / "README.md"
            md_a.write_text(
                "# Doc A\nMalicious payload: </script><script>alert(1)</script>\n",
                encoding="utf-8",
            )
            md_b.write_text("# Doc B\nNormal content\n", encoding="utf-8")
            out_html = root / "portal.html"

            compile_portal.compile_portal("Test Portal", [root], out_html)
            html_text = out_html.read_text(encoding="utf-8")

            # Extract JSON block between <script id="portal-data"...> and </script>
            marker_start = '<script id="portal-data" type="application/json">'
            start_idx = html_text.index(marker_start) + len(marker_start)
            end_idx = html_text.index("</script>", start_idx)
            json_payload = html_text[start_idx:end_idx]

            # Must parse as valid JSON and restore the original markdown
            parsed = json.loads(json_payload)
            self.assertEqual(len(parsed), 2)
            self.assertNotEqual(parsed[0]["id"], parsed[1]["id"])
            self.assertIn("</script><script>alert(1)</script>", parsed[0]["markdown"])


class TestImageGen(unittest.TestCase):
    def test_api_key_in_header_not_url_and_dual_model_payloads(self) -> None:
        """Regression test for R1: API key must be in x-goog-api-key header, never in URL."""
        self.assertEqual(image_gen.DEFAULT_MODEL, "gemini-nano-banana-2.1")
        self.assertEqual(image_gen.DEFAULT_VERTEX_LOCATION, "global")

        url, headers = image_gen.build_endpoint_and_headers(
            model="imagen-3.0-generate-002", api_key="secret-test-key"
        )
        self.assertNotIn("secret-test-key", url)
        self.assertNotIn("?key=", url)
        self.assertEqual(headers["x-goog-api-key"], "secret-test-key")
        self.assertTrue(url.endswith(":predict"))

        gem_url, _ = image_gen.build_endpoint_and_headers(
            model="gemini-3-pro-image", api_key="secret-test-key"
        )
        self.assertTrue(gem_url.endswith(":generateContent"))

        # Legacy Imagen payload emits a June 30, 2026 discontinuation warning
        err_buf = io.StringIO()
        with contextlib.redirect_stderr(err_buf):
            imagen_payload = image_gen.build_request_payload(
                model="imagen-3.0-generate-002",
                prompt="test",
                aspect_ratio="16:9",
                seed=42,
                negative_prompt="blur",
            )
        self.assertIn("discontinued on Vertex AI on June 30, 2026", err_buf.getvalue())
        self.assertEqual(imagen_payload["parameters"]["seed"], 42)
        self.assertFalse(imagen_payload["parameters"]["addWatermark"])
        self.assertEqual(imagen_payload["parameters"]["negativePrompt"], "blur")

        gemini_payload = image_gen.build_request_payload(
            model="gemini-3-pro-image",
            prompt="test",
            aspect_ratio="1:1",
            seed=7,
        )
        self.assertEqual(
            gemini_payload["generationConfig"]["responseModalities"], ["TEXT", "IMAGE"]
        )
        self.assertEqual(gemini_payload["generationConfig"]["seed"], 7)

    def test_vertex_global_endpoint_and_model_parameter_constraints(self) -> None:
        """Vertex AI location=global must use aiplatform.googleapis.com and respect model constraints."""
        global_url, global_headers = image_gen.build_endpoint_and_headers(
            model="gemini-nano-banana-2.1",
            project="demo-proj",
            location="global",
            access_token="tok-123",
        )
        self.assertEqual(
            global_url,
            "https://aiplatform.googleapis.com/v1/projects/demo-proj"
            "/locations/global/publishers/google/models/gemini-nano-banana-2.1:generateContent",
        )
        self.assertNotIn("global-aiplatform.googleapis.com", global_url)
        self.assertEqual(global_headers["Authorization"], "Bearer tok-123")

        regional_url, _ = image_gen.build_endpoint_and_headers(
            model="gemini-2.5-flash-image",
            project="demo-proj",
            location="us-central1",
            access_token="tok-123",
        )
        self.assertTrue(
            regional_url.startswith("https://us-central1-aiplatform.googleapis.com/v1/")
        )

        # gemini-nano-banana-2.1 rejects 'seed' on Vertex AI / Agent Platform
        err_buf = io.StringIO()
        with contextlib.redirect_stderr(err_buf):
            nb_payload = image_gen.build_request_payload(
                model="gemini-nano-banana-2.1",
                prompt="test",
                aspect_ratio="16:9",
                seed=99,
            )
        self.assertNotIn("seed", nb_payload["generationConfig"])
        self.assertIn("does not support the 'seed' parameter", err_buf.getvalue())

        # gemini-3.1-flash-lite-image supports IMAGE output modality only
        lite_payload = image_gen.build_request_payload(
            model="gemini-3.1-flash-lite-image",
            prompt="test",
            aspect_ratio="1:1",
        )
        self.assertEqual(
            lite_payload["generationConfig"]["responseModalities"], ["IMAGE"]
        )


class TestVerifyStatic(unittest.TestCase):
    def test_mermaid_init_cylinder_and_unquoted_shapes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            md = Path(tmp) / "diagram.md"
            md.write_text(
                "# Doc\n~~~mermaid\n%%{init: {'theme': 'dark'}}%%\nflowchart\n"
                "  db[(Database)] --> ok[\"Service (v1)\"]\n~~~\n",
                encoding="utf-8",
            )
            self.assertEqual(verify_static.verify_prose(md, profile="technical"), [])

            bad_md = Path(tmp) / "bad.md"
            bad_md.write_text(
                "# Doc\n```mermaid\nflowchart TD\n  a{Decision (bad)} --> b(Round (bad))\n```\n",
                encoding="utf-8",
            )
            errs = verify_static.verify_prose(bad_md, profile="technical")
            self.assertEqual(len(errs), 1)
            self.assertIn("MERMAID_UNQUOTED_LABEL", errs[0])

    def test_adk_ast_strict_root_agent_and_async_tools(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pkg = Path(tmp) / "my_agent"
            pkg.mkdir()
            # Missing __init__.py and root_agent only in comment must fail (R7)
            agent_py = pkg / "agent.py"
            agent_py.write_text(
                "# root_agent is mentioned in a comment only\n"
                "async def bad_tool(x):\n    return x\n",
                encoding="utf-8",
            )
            errs = verify_static.verify_adk(pkg)
            codes = " ".join(errs)
            self.assertIn("ADK_MISSING_INIT", codes)
            self.assertIn("ADK_ROOT_AGENT", codes)
            self.assertIn("ADK_TOOL_DOCSTRING", codes)
            self.assertIn("ADK_TOOL_TYPE_HINTS", codes)

            # Valid package with __init__.py, AnnAssign root_agent, and typed async tool
            (pkg / "__init__.py").write_text("from . import agent\n", encoding="utf-8")
            agent_py.write_text(
                "async def good_tool(query: str) -> str:\n"
                '    """Search records."""\n'
                "    return query\n\n"
                "root_agent: object = object()\n",
                encoding="utf-8",
            )
            self.assertEqual(verify_static.verify_adk(pkg), [])

    def test_terraform_recursive_and_comment_stripping(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tf_root = Path(tmp)
            for name in ("main.tf", "variables.tf", "outputs.tf", "versions.tf"):
                (tf_root / name).write_text(
                    "// Never use roles/owner\n/* or allUsers */\n# or roles/editor\n",
                    encoding="utf-8",
                )
            self.assertEqual(verify_static.verify_terraform(tf_root), [])

            sub = tf_root / "modules" / "sub"
            sub.mkdir(parents=True)
            (sub / "iam.tf").write_text('role = "roles/owner"\n', encoding="utf-8")
            errs = verify_static.verify_terraform(tf_root)
            self.assertEqual(len(errs), 1)
            self.assertIn("TF_IAM_LEAST_PRIVILEGE", errs[0])

    def test_prose_slop_terms_flagged_in_narrative_but_not_in_code(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            slop = Path(tmp) / "slop.md"
            slop.write_text(
                "# Readout\n\n"
                "This is a seamless, cutting-edge solution. Let us delve in.\n\n"
                "In today's fast-paced market we harness the power of synergy.\n",
                encoding="utf-8",
            )
            errs = verify_static.verify_prose(slop, profile="narrative")
            self.assertIn("PROSE_SLOP_TERM", _codes(errs))
            flagged_lines = {e.split(":")[1] for e in errs if "PROSE_SLOP_TERM" in e}
            self.assertEqual(flagged_lines, {"3", "5"})

            clean = Path(tmp) / "clean.md"
            clean.write_text(
                "# Reference\n\n"
                "Run `delve --seamless` to inspect the `synergy` index.\n\n"
                "```text\nA seamless, cutting-edge, world-class tool. Delve in.\n```\n\n"
                "| Term | Status |\n| :--- | :--- |\n| seamless | banned |\n\n"
                "> Quoted customer text: a game-changing, next-generation release.\n\n"
                "The latency dropped from 420 ms to 95 ms after the cache change.\n",
                encoding="utf-8",
            )
            self.assertEqual(verify_static.verify_prose(clean, profile="narrative"), [])


# ---------------------------------------------------------------------------
# Shared helpers for inventory, negative-path, and sanitization tests
# ---------------------------------------------------------------------------

EXPECTED_CORE_COUNT = 8
EXPECTED_JIT_COUNT = 9
EXPECTED_SKILL_COUNT = EXPECTED_CORE_COUNT + EXPECTED_JIT_COUNT

def _read_json(rel_path: str) -> dict:
    return json.loads((REPO_ROOT / rel_path).read_text(encoding="utf-8"))


def _skill_dirs() -> list[Path]:
    return sorted(
        p
        for p in SKILLS_DIR.iterdir()
        if p.is_dir() and not p.name.startswith((".", "_"))
    )


def _run_cli(*args: str, cwd: Path = REPO_ROOT) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )


_FIXTURE_FRONTMATTER = (
    "---\n"
    "name: {name}\n"
    "description: >-\n"
    "  Minimal fixture skill for verifier regression tests. Use when exercising\n"
    "  verify_static.py skill mode. Don't use for real agent work.\n"
    "---\n"
)


def _write_fixture_skill(
    root: Path,
    name: str = "demo-skill",
    *,
    fm_name: str | None = None,
    body_extra: str = "",
    readme: str | None = "# demo-skill\n\nHuman-facing provenance and rationale live here.\n",
    body_lines: int = 60,
) -> Path:
    """Create root/skills/<name>/ with a SKILL.md that passes every check by default."""
    skill_dir = root / "skills" / name
    skill_dir.mkdir(parents=True)
    body = "\n".join(f"{i}. Perform verification step {i}." for i in range(1, body_lines + 1))
    text = (
        _FIXTURE_FRONTMATTER.format(name=fm_name or name)
        + "\n# Demo Skill\n\n"
        + body_extra
        + body
        + "\n"
    )
    (skill_dir / "SKILL.md").write_text(text, encoding="utf-8")
    if readme is not None:
        (skill_dir / "README.md").write_text(readme, encoding="utf-8")
    return skill_dir


def _codes(errors: list[str]) -> set[str]:
    return set(re.findall(r"\[([A-Z_]+)\]", " ".join(errors)))


class TestSkillInventoryAndManifest(unittest.TestCase):
    """Integration tests binding skills/, the manifests, the lockfile, and plugin.json."""

    def test_all_17_skills_ship_non_empty_skill_md_and_readme(self) -> None:
        dirs = _skill_dirs()
        self.assertEqual(
            len(dirs), EXPECTED_SKILL_COUNT, f"Unexpected skill dirs: {[d.name for d in dirs]}"
        )
        for skill_dir in dirs:
            with self.subTest(skill=skill_dir.name):
                for fname in ("SKILL.md", "README.md"):
                    f = skill_dir / fname
                    self.assertTrue(f.is_file(), f"{skill_dir.name} is missing {fname}")
                    self.assertTrue(
                        f.read_text(encoding="utf-8").strip(), f"{skill_dir.name}/{fname} is empty"
                    )

    def test_every_skill_passes_verify_static_skill_mode(self) -> None:
        for skill_dir in _skill_dirs():
            with self.subTest(skill=skill_dir.name):
                self.assertEqual(verify_static.verify_skill(skill_dir), [])

    def test_verify_static_skill_cli_exits_zero_on_repo(self) -> None:
        proc = _run_cli(str(VERIFY_SCRIPT), "--mode", "skill", "skills/")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("STATIC VERIFICATION PASSED", proc.stdout)

    def test_manifest_clusters_partition_skill_directories(self) -> None:
        manifest = _read_json("skills.manifest.json")
        core = manifest["clusters"]["core"]["skills"]
        jit = manifest["clusters"]["jit"]["skills"]
        self.assertEqual(len(core), EXPECTED_CORE_COUNT)
        self.assertEqual(len(jit), EXPECTED_JIT_COUNT)
        self.assertEqual(len(set(core)), len(core), "duplicate core skill")
        self.assertEqual(len(set(jit)), len(jit), "duplicate jit skill")
        self.assertFalse(set(core) & set(jit), "skill listed in both core and jit")
        self.assertEqual(set(core) | set(jit), {d.name for d in _skill_dirs()})

    def test_packs_reference_known_local_and_registered_upstream_skills(self) -> None:
        manifest = _read_json("skills.manifest.json")
        local_names = {d.name for d in _skill_dirs()}
        registered = {
            s for src in manifest["upstream_sources"] for s in src.get("skills", [])
        }
        self.assertEqual(set(manifest["packs"]), {"adk", "arch", "devrel", "audit"})
        for pack_name, pack in manifest["packs"].items():
            with self.subTest(pack=pack_name):
                self.assertTrue(pack.get("description"))
                self.assertLessEqual(set(pack["local_skills"]), local_names)
                self.assertLessEqual(set(pack["upstream_skills"]), registered)

    def test_lockfile_matches_manifest_upstream_sources(self) -> None:
        manifest = _read_json("skills.manifest.json")
        lock = _read_json("skills.lock.json")
        self.assertEqual(lock["lockfileVersion"], 1)
        manifest_sources = {
            src["repo"]: (src.get("ref", ""), src["skills"]) for src in manifest["upstream_sources"]
        }
        lock_sources = {
            repo: (entry.get("ref", ""), entry["skills"]) for repo, entry in lock["sources"].items()
        }
        self.assertEqual(manifest_sources, lock_sources)
        for repo, (ref, _skills) in manifest_sources.items():
            with self.subTest(repo=repo):
                self.assertTrue(ref, f"upstream source {repo} has no pinned ref")

    def test_example_overlay_merges_with_placeholder_paths_only(self) -> None:
        example = REPO_ROOT / "skills.manifest.local.example.json"
        manifest = sync_skills.load_manifest(local_override_path=example)
        corp = manifest["corp_layer"]
        # Keys from the base manifest survive the shallow merge.
        self.assertEqual(corp["local_override_file"], "skills.manifest.local.json")
        self.assertTrue(corp["skills"], "example overlay should demonstrate corp skills")
        for entry in corp["skills"]:
            with self.subTest(skill=entry.get("name")):
                self.assertTrue(sync_skills.validate_skill_name(entry["name"]))
                self.assertTrue(entry["path"].startswith("/path/to/"), entry["path"])
        # Placeholder mount paths must never resolve on a real machine.
        self.assertFalse(sync_skills.is_corp_mounted(manifest))

    def test_plugin_json_metadata_is_consistent(self) -> None:
        plugin = _read_json("plugin.json")
        manifest = _read_json("skills.manifest.json")
        self.assertEqual(plugin["name"], manifest["repository"])
        self.assertRegex(plugin["version"], r"^\d+\.\d+\.\d+$")
        for harness in ("Google Antigravity", "Gemini CLI", "Claude Code", "OpenAI Codex"):
            self.assertIn(harness, plugin["description"])
        self.assertTrue(plugin["suggestedPrompts"])

    def test_readme_relative_links_resolve(self) -> None:
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        targets = re.findall(r"\]\(([^)#\s]+)(?:#[^)]*)?\)", readme)
        local = [t for t in targets if not re.match(r"^[a-z]+://", t)]
        self.assertTrue(local)
        for target in local:
            with self.subTest(link=target):
                self.assertTrue((REPO_ROOT / target).exists(), f"README link {target} is broken")

    def test_readme_and_agents_md_pass_narrative_prose_and_budget(self) -> None:
        for rel in ("README.md", "rules/AGENTS.md"):
            with self.subTest(file=rel):
                self.assertEqual(
                    verify_static.verify_prose(REPO_ROOT / rel, profile="narrative"), []
                )
        agents_lines = (REPO_ROOT / "rules" / "AGENTS.md").read_text(encoding="utf-8").splitlines()
        self.assertLess(len(agents_lines), 200)

    def test_every_python_cli_responds_to_help(self) -> None:
        scripts = sorted(REPO_ROOT.glob("scripts/*.py")) + sorted(SKILLS_DIR.glob("*/scripts/*.py"))
        self.assertGreaterEqual(len(scripts), 6)
        for script in scripts:
            with self.subTest(script=str(script.relative_to(REPO_ROOT))):
                proc = _run_cli(str(script), "--help")
                self.assertEqual(proc.returncode, 0, proc.stderr)
                self.assertIn("usage:", proc.stdout)

    def test_root_wrapper_reexports_canonical_sync_api(self) -> None:
        wrapper = _load_module("sync_skills_wrapper", "scripts/sync_skills.py")
        for symbol in ("main", "load_manifest", "sync_project", "find_repo_root"):
            self.assertTrue(callable(getattr(wrapper, symbol, None)), symbol)
        self.assertEqual(wrapper.find_repo_root(), REPO_ROOT)

    def test_skill_commands_do_not_hardcode_single_harness_paths(self) -> None:
        """Runnable python3 commands must resolve on every harness, not only Antigravity."""
        hardcoded = "~/.gemini/config/skills/"
        offenders: list[str] = []
        for skill_md in sorted(SKILLS_DIR.glob("*/SKILL.md")):
            in_fence = False
            for lineno, line in enumerate(skill_md.read_text(encoding="utf-8").splitlines(), 1):
                if re.match(r"^\s*(```|~~~)", line):
                    in_fence = not in_fence
                    continue
                # Fenced lines are commands as a whole; in prose only inline code spans
                # are runnable, so a rule that merely names the path is not an offender.
                candidates = [line] if in_fence else re.findall(r"`([^`]+)`", line)
                if any("python3" in c and hardcoded in c for c in candidates):
                    offenders.append(f"{skill_md.relative_to(REPO_ROOT)}:{lineno}: {line.strip()}")
        self.assertEqual(
            offenders,
            [],
            "Use <skill-dir>/../<skill>/scripts/... instead of a harness-specific path:\n"
            + "\n".join(offenders),
        )


class TestVerifySkillNegativePaths(unittest.TestCase):
    """verify_static.py --mode skill must catch each defect class in isolation."""

    def test_clean_fixture_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = _write_fixture_skill(Path(tmp))
            self.assertEqual(verify_static.verify_skill(skill_dir), [])

    def test_broken_relative_link_is_flagged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = _write_fixture_skill(
                Path(tmp), body_extra="See [the guide](references/missing.md#setup).\n\n"
            )
            errs = verify_static.verify_skill(skill_dir)
            self.assertIn("BROKEN_LINK", _codes(errs))
            self.assertTrue(any("references/missing.md" in e for e in errs))

    def test_valid_links_and_links_in_code_are_not_flagged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            body = (
                "See [the guide](references/guide.md#intro) and [docs](https://example.com).\n"
                "Inline code `[x](does/not/exist.md)` is ignored.\n\n"
                "```text\n[y](also/missing.md)\n```\n\n"
            )
            skill_dir = _write_fixture_skill(Path(tmp), body_extra=body)
            (skill_dir / "references").mkdir()
            (skill_dir / "references" / "guide.md").write_text("# Guide\n", encoding="utf-8")
            self.assertEqual(verify_static.verify_skill(skill_dir), [])

    def test_missing_readme_is_flagged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = _write_fixture_skill(Path(tmp), readme=None)
            self.assertIn("SKILL_MISSING_README", _codes(verify_static.verify_skill(skill_dir)))

    def test_empty_readme_is_flagged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = _write_fixture_skill(Path(tmp), readme="   \n")
            self.assertIn("SKILL_MISSING_README", _codes(verify_static.verify_skill(skill_dir)))

    def test_provenance_in_skill_body_is_flagged(self) -> None:
        for leak in (
            "Inspired by [upstream/skill](https://example.com/upstream).\n\n",
            "Adapted from the upstream sync skill.\n\n",
        ):
            with self.subTest(leak=leak.strip()), tempfile.TemporaryDirectory() as tmp:
                skill_dir = _write_fixture_skill(Path(tmp), body_extra=leak)
                self.assertIn(
                    "SKILL_PROVENANCE_IN_BODY", _codes(verify_static.verify_skill(skill_dir))
                )

    def test_frontmatter_mismatch_short_body_and_routing_are_flagged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = _write_fixture_skill(Path(tmp), fm_name="other-name", body_lines=5)
            codes = _codes(verify_static.verify_skill(skill_dir))
            self.assertIn("FRONTMATTER_MISMATCH", codes)
            self.assertIn("SKILL_TOO_SHORT", codes)

            skill_md = skill_dir / "SKILL.md"
            skill_md.write_text(
                skill_md.read_text(encoding="utf-8").replace("Don't use", "Avoid"),
                encoding="utf-8",
            )
            self.assertIn("ROUTING", _codes(verify_static.verify_skill(skill_dir)))

    def test_unicode_dash_in_code_fence_and_unclosed_fence_are_flagged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            body = "```bash\nrun \u2014flag\n```\n\n```text\nnever closed\n"
            skill_dir = _write_fixture_skill(Path(tmp), body_extra=body)
            codes = _codes(verify_static.verify_skill(skill_dir))
            self.assertIn("CODE_UNICODE_DASH", codes)
            self.assertIn("UNCLOSED_FENCE", codes)

    def test_cli_exits_nonzero_and_recurses_skills_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_fixture_skill(root, "good-skill")
            _write_fixture_skill(root, "bad-skill", body_extra="[x](nope.md)\n\n")
            proc = _run_cli(str(VERIFY_SCRIPT), "--mode", "skill", str(root / "skills"))
            self.assertEqual(proc.returncode, 1, proc.stdout)
            self.assertIn("STATIC VERIFICATION FAILED", proc.stdout)
            self.assertIn("bad-skill", proc.stdout)
            self.assertNotIn("good-skill", proc.stdout)


# Internal-only identifiers that must never ship publicly. Fragments are split so
# this test file does not match its own scan.
_INTERNAL_TERMS_RE = re.compile(
    "|".join(
        (
            "google" + "3",
            "/google" + "/src",
            "jet" + "ski",
            "g4" + "d",
            "cit" + "c",
            "bla" + "ze",
            "mo" + "ma",
            "bug" + "anizer",
            r"\b" + "b" + r"/[0-9]{6,}",
            r"\b" + "cl" + r"/[0-9]{6,}",
        )
    ),
    re.IGNORECASE,
)
# The google-oss skill documents the sanitization regex itself.
_SANITIZATION_ALLOWLIST = {"skills/google-oss/SKILL.md"}
_WALK_SKIP_PARTS = {".git", "__pycache__", "node_modules", "dist", "build", "output"}


def _publishable_files() -> list[str]:
    """Tracked plus untracked-but-not-ignored files, relative to REPO_ROOT."""
    if shutil.which("git"):
        proc = subprocess.run(
            ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            check=False,
        )
        if proc.returncode == 0 and proc.stdout:
            return sorted(
                p
                for p in proc.stdout.decode("utf-8").split("\0")
                if p and (REPO_ROOT / p).is_file()
            )
    files = []
    for path in REPO_ROOT.rglob("*"):
        rel = path.relative_to(REPO_ROOT)
        if path.is_file() and not (set(rel.parts) & _WALK_SKIP_PARTS):
            if rel.name != "skills.manifest.local.json" and path.suffix != ".pyc":
                files.append(rel.as_posix())
    return sorted(files)


class TestRepoSanitization(unittest.TestCase):
    """Publication gate: no internal identifiers in anything that would be pushed."""

    def test_no_internal_terms_in_publishable_files(self) -> None:
        files = _publishable_files()
        self.assertIn("README.md", files)
        self.assertIn("tests/test_scripts.py", files)
        leaks: list[str] = []
        for rel in files:
            if rel in _SANITIZATION_ALLOWLIST:
                continue
            data = (REPO_ROOT / rel).read_bytes()
            if b"\0" in data:
                continue  # binary asset
            for lineno, line in enumerate(data.decode("utf-8", "replace").splitlines(), 1):
                m = _INTERNAL_TERMS_RE.search(line)
                if m:
                    leaks.append(f"{rel}:{lineno}: '{m.group(0)}'")
        self.assertEqual(leaks, [], "Internal identifiers found:\n" + "\n".join(leaks))

    def test_local_corp_overlay_is_gitignored(self) -> None:
        gitignore = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
        self.assertIn("skills.manifest.local.json", [ln.strip() for ln in gitignore])
        self.assertNotIn("skills.manifest.local.json", _publishable_files())

    def test_sanitization_regex_catches_each_term(self) -> None:
        samples = [
            "path //depot/" + "google" + "3/foo",
            "/google" + "/src/cloud/me",
            "built for " + "Jet" + "ski",
            "run " + "bla" + "ze build",
            "see " + "b" + "/123456789",
        ]
        for sample in samples:
            with self.subTest(sample=sample):
                self.assertIsNotNone(_INTERNAL_TERMS_RE.search(sample))
        self.assertIsNone(_INTERNAL_TERMS_RE.search("Google Antigravity, Gemini CLI, web/123"))


if __name__ == "__main__":
    unittest.main()
