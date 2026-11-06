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
"""Deterministic Static Verifier for Expectation-Grounded Alignment (verify_static.py).

Modes:
  --mode prose      : Audits Markdown documents (--profile narrative|technical) for
                      restrained bolding, inline backtick density in narrative prose,
                      high-confidence AI-slop terms (both profiles), unclosed fences,
                      and Mermaid diagram hygiene.
  --mode skill      : Audits SKILL.md files for YAML frontmatter, kebab-case naming,
                      50..800 line bounds, 'Use when' / 'Don't use' triggers,
                      relative link resolution (SKILL.md + README.md), a non-empty
                      sibling README.md, provenance leakage into SKILL.md, and
                      Unicode dashes in code blocks.
  --mode adk        : Audits Google ADK Python packages for __init__.py, AST-verified
                      root_agent export, and sync/async tool docstrings + type hints.
  --mode terraform  : Recursively audits Terraform modules for main.tf, variables.tf,
                      outputs.tf, versions.tf, and comment-aware IAM least privilege.
  --mode okf        : Audits Open Knowledge Format (OKF) catalog/index files.
  --mode codelab    : Audits interactive codelab Markdown files for duration metadata,
                      environment setup, verification checkpoints, and cleanup steps.
"""

from __future__ import annotations

import argparse
import ast
from pathlib import Path
import re
import sys


KEBAB_CASE_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
FENCE_OPEN_RE = re.compile(r"^(`{3,}|~{3,})(.*)$")
MD_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


# High-confidence AI-slop terms from the unslop lexicon (skills/unslop/references/).
SLOP_TERM_RE = re.compile(
    r"\b(?:"
    r"delv(?:e|es|ed|ing)"
    r"|seamless(?:ly)?"
    r"|cutting[- ]edge"
    r"|game[- ]chang(?:ing|er|ers)"
    r"|world[- ]class"
    r"|next[- ]generation"
    r"|synerg(?:y|ies|istic)"
    r"|revolutioni[sz](?:e|es|ed|ing)"
    r"|supercharg(?:e|es|ed|ing)"
    r"|spearhead(?:s|ed|ing)?"
    r"|in today[\u2019']s (?:rapidly evolving|fast[- ]paced)"
    r"|it is worth noting"
    r"|unlock(?:s|ed|ing)? the full potential"
    r"|harness(?:es|ed|ing)? the power"
    r")\b",
    flags=re.IGNORECASE,
)
# Spans treated as *mentions* of a term rather than uses: inline code, italics, and quotes.
_MENTION_SPAN_RES = (
    re.compile(r"`[^`]+`"),
    re.compile(r"(?<!\*)\*(?!\*)[^*\n]+?(?<!\*)\*(?!\*)"),
    re.compile(r"(?<![\w_])_(?!_)[^_\n]+?(?<!_)_(?![\w_])"),
    re.compile(r"\"[^\"\n]*\""),
    re.compile("\u201c[^\u201d\n]*\u201d"),
)


def _find_slop_terms(line: str) -> list[str]:
    """Return slop terms used (not merely mentioned) in a prose line."""
    cleaned = line
    for span_re in _MENTION_SPAN_RES:
        cleaned = span_re.sub(" ", cleaned)
    cleaned = re.sub(r"\]\([^)]*\)", "]", cleaned)  # ignore link targets
    return [m.group(0) for m in SLOP_TERM_RE.finditer(cleaned)]


def _has_unquoted_mermaid_parens(line: str) -> bool:
    """Detect unquoted parentheses inside Mermaid node labels while allowing [(Cylinder)]."""
    stripped = line.strip()
    if not stripped or stripped.startswith("%%"):
        return False

    # 1. Strip properly quoted cylinder/subroutine/stadium shapes first
    cleaned = re.sub(r'\b[A-Za-z0-9_-]+\[\("[^"]*"\)\]', "", stripped)
    cleaned = re.sub(r"\b[A-Za-z0-9_-]+\[\('[^']*'\)\]", "", cleaned)
    cleaned = re.sub(r'\b[A-Za-z0-9_-]+\[\["[^"]*"\]\]', "", cleaned)

    # 2. Unquoted cylinder nodes: id[(Label)] -> flag if inner label has unquoted ( or )
    for m in re.finditer(r"\b[A-Za-z0-9_-]+\[\((?![\"'])(.*?)\)\]", cleaned):
        inner = m.group(1)
        if "(" in inner or ")" in inner:
            return True

    # Remove remaining simple cylinder and subroutine shapes before checking general brackets
    cleaned = re.sub(r"\b[A-Za-z0-9_-]+\[\([^\)]*\)\]", "", cleaned)
    cleaned = re.sub(r"\b[A-Za-z0-9_-]+\[\[[^\]]*\]\]", "", cleaned)

    # 2. Square bracket nodes: id[Label (info)]
    for m in re.finditer(r"\b[A-Za-z0-9_-]+\[(?![\"'])([^\]]*)\]", cleaned):
        if "(" in m.group(1) or ")" in m.group(1):
            return True

    # 3. Diamond decision nodes: id{Decision (info)}
    for m in re.finditer(r"\b[A-Za-z0-9_-]+\{(?![\{\"'])([^\}]*)\}", cleaned):
        if "(" in m.group(1) or ")" in m.group(1):
            return True

    # 4. Round/stadium nodes with nested unquoted parentheses: id(Round (info))
    if re.search(r"\b[A-Za-z0-9_-]+\((?![\(\[\"'])[^\)]*\([^\)]*\)[^\)]*\)", cleaned):
        return True

    return False


def _check_mermaid(path: Path, mermaid_lines: list[tuple[int, str]]) -> list[str]:
    errors: list[str] = []
    content_lines = [
        (idx, line.strip())
        for idx, line in mermaid_lines
        if line.strip() and not line.strip().startswith("%%")
    ]
    if not content_lines:
        return errors

    first_idx, first_line = content_lines[0]
    lower_first = first_line.lower()
    allowed_prefixes = (
        "flowchart",
        "graph ",
        "sequencediagram",
        "statediagram",
        "classdiagram",
        "erdiagram",
        "xychart-beta",
    )
    if not lower_first.startswith(allowed_prefixes):
        errors.append(
            f"{path}:{first_idx}: [MERMAID_TYPE] Unsupported Mermaid diagram type '{first_line}'."
        )

    for idx, line in mermaid_lines:
        if _has_unquoted_mermaid_parens(line):
            errors.append(
                f"{path}:{idx}: [MERMAID_UNQUOTED_LABEL] Quote node labels containing parentheses: "
                'e.g. id["Label (Info)"].'
            )
    return errors


def verify_prose(path: Path, profile: str = "narrative") -> list[str]:
    if not path.exists():
        return [f"{path}: [MISSING] File or directory not found."]
    if path.is_dir():
        md_files = sorted(p for p in path.rglob("*.md") if ".git" not in p.parts)
        if not md_files:
            return [f"{path}: [EMPTY_DIR] No Markdown files found in directory."]
        errors: list[str] = []
        for md in md_files:
            errors.extend(verify_prose(md, profile=profile))
        return errors

    errors = []
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    in_fence = False
    fence_marker = ""
    fence_lang = ""
    mermaid_lines: list[tuple[int, str]] = []

    for idx, line in enumerate(lines, start=1):
        stripped = line.strip()
        m_fence = FENCE_OPEN_RE.match(stripped)
        if m_fence:
            marker, rest = m_fence.group(1), m_fence.group(2).strip()
            if not in_fence:
                in_fence = True
                fence_marker = marker
                fence_lang = rest.lower()
                mermaid_lines = []
                continue
            elif marker[0] == fence_marker[0] and len(marker) >= len(fence_marker) and not rest:
                if fence_lang == "mermaid":
                    errors.extend(_check_mermaid(path, mermaid_lines))
                in_fence = False
                fence_marker = ""
                fence_lang = ""
                continue

        if in_fence:
            if fence_lang == "mermaid":
                mermaid_lines.append((idx, line))
            elif fence_lang not in ("markdown", "md", "prose") and ("\u2014" in line or "\u2013" in line):
                errors.append(
                    f"{path}:{idx}: [CODE_UNICODE_DASH] Unicode em/en-dash inside fenced code block."
                )
            continue

        # Prose checks skip headings, tables, blockquotes, horizontal rules, and HTML comments.
        if not stripped or stripped.startswith(("#", "|", ">", "---", "<!--")):
            continue

        slop_terms = _find_slop_terms(line)
        if slop_terms:
            errors.append(
                f"{path}:{idx}: [PROSE_SLOP_TERM] AI-slop term(s) {', '.join(repr(t) for t in slop_terms)}; "
                "replace with the concrete mechanism or metric (see the unslop skill lexicon)."
            )

        if profile != "narrative":
            continue

        bold_spans = re.findall(r"\*\*[^*]+\*\*", line)
        if len(bold_spans) > 3:
            errors.append(
                f"{path}:{idx}: [PROSE_BOLD_OVERUSE] {len(bold_spans)} bold spans in one line "
                "(restrict bolding to bullet lead-ins and primary headline numbers)."
            )

        backtick_spans = re.findall(r"`[^`]+`", line)
        if len(backtick_spans) > 3:
            errors.append(
                f"{path}:{idx}: [PROSE_BACKTICK_CLUTTER] {len(backtick_spans)} inline code spans in narrative line "
                "(avoid Roboto Mono backtick clutter in narrative prose)."
            )

    if in_fence:
        errors.append(f"{path}: [UNCLOSED_FENCE] File ends inside an unclosed {fence_marker} fenced block.")

    return errors


def _extract_frontmatter_field(fm: str, key: str) -> str | None:
    m = re.search(rf"^{re.escape(key)}:[ \t]*(.*)$", fm, flags=re.MULTILINE)
    if not m:
        return None
    val = m.group(1).strip()
    if val in ("", ">", ">-", ">+", "|", "|-", "|+"):
        # YAML block scalar: collect the following indented continuation lines.
        block: list[str] = []
        for cont in fm[m.end():].splitlines()[1:]:
            if cont.strip() and not cont[:1].isspace():
                break
            block.append(cont.strip())
        val = " ".join(part for part in block if part)
    return val.strip().strip("'\"")


# Human-facing provenance belongs in README.md, not in the agent-facing SKILL.md body.
PROVENANCE_RE = re.compile(
    r"^\s*(?:>\s*)?(?:[-*+]\s+)?(?:\*\*|__)?\s*"
    r"(?:(?:Inspired by|Adapted from)(?:\*\*|__)?[\s:]|Synthesi[sz]es\b.*\bfrom\s|Provenance\b)"
)
PROVENANCE_HEADING_RE = re.compile(r"^#{1,6}\s+.*\bProvenance\b", flags=re.IGNORECASE)
SKIP_LINK_PREFIXES = (
    "http://", "https://", "mailto:", "file://", "sidecar://", "conversation://", "/", "#", "<",
)
MAX_SKILL_NAME_LEN = 64
MAX_DESCRIPTION_LEN = 1024


def _iter_non_fenced_lines(lines: list[str]):
    """Yield (line_no, line) for lines outside fenced code blocks."""
    in_fence = False
    fence_marker = ""
    for idx, line in enumerate(lines, start=1):
        m_fence = FENCE_OPEN_RE.match(line.strip())
        if m_fence:
            marker, rest = m_fence.group(1), m_fence.group(2).strip()
            if not in_fence:
                in_fence, fence_marker = True, marker
                continue
            if marker[0] == fence_marker[0] and len(marker) >= len(fence_marker) and not rest:
                in_fence, fence_marker = False, ""
                continue
        if not in_fence:
            yield idx, line


def _check_relative_links(md_path: Path, lines: list[str]) -> list[str]:
    """Flag relative Markdown links (outside fences and inline code) whose target is missing."""
    errors: list[str] = []
    base_dir = md_path.parent
    for idx, line in _iter_non_fenced_lines(lines):
        line_no_inline_code = re.sub(r"`[^`]+`", "", line)
        for m_link in MD_LINK_RE.finditer(line_no_inline_code):
            raw_target = m_link.group(1).strip()
            # Drop optional link titles: [text](path "Title")
            raw_target = re.split(r"\s+[\"'(]", raw_target, maxsplit=1)[0]
            target_url = raw_target.split("#", 1)[0].split("?", 1)[0].strip()
            if not target_url or target_url.startswith(SKIP_LINK_PREFIXES):
                continue
            resolved_target = (base_dir / target_url).resolve()
            if not resolved_target.exists():
                errors.append(
                    f"{md_path}:{idx}: [BROKEN_LINK] Relative link target '{target_url}' does not exist at {resolved_target}."
                )
    return errors


def verify_skill(path: Path) -> list[str]:
    if not path.exists():
        return [f"{path}: [MISSING] SKILL.md or skill directory not found."]

    if path.is_dir() and not (path / "SKILL.md").is_file():
        skill_files = sorted(path.glob("*/SKILL.md"))
        if skill_files:
            errors: list[str] = []
            # A skills/ root: every visible subdirectory must be a real skill.
            for sub in sorted(p for p in path.iterdir() if p.is_dir()):
                if sub.name.startswith((".", "_")):
                    continue
                if not (sub / "SKILL.md").is_file():
                    errors.append(
                        f"{sub}: [SKILL_MISSING_SKILL_MD] Directory under skills root has no SKILL.md."
                    )
            for sf in skill_files:
                errors.extend(verify_skill(sf))
            return errors
        return [f"{path / 'SKILL.md'}: [MISSING] SKILL.md not found."]

    skill_md = path / "SKILL.md" if path.is_dir() else path
    skill_dir = skill_md.parent
    errors = []

    if not KEBAB_CASE_RE.match(skill_dir.name):
        errors.append(
            f"{skill_md}: [SKILL_DIR_NAME] Skill directory '{skill_dir.name}' must be kebab-case (^[a-z0-9-]+$)."
        )

    readme = skill_dir / "README.md"
    if not readme.is_file() or not readme.read_text(encoding="utf-8").strip():
        errors.append(
            f"{readme}: [SKILL_MISSING_README] Skill directory needs a non-empty README.md "
            "(provenance, cluster rationale, directory contents) alongside SKILL.md."
        )
    else:
        errors.extend(_check_relative_links(readme, readme.read_text(encoding="utf-8").splitlines()))

    # Normalize CRLF so Windows-authored files are judged on content, not line endings.
    text = skill_md.read_text(encoding="utf-8").replace("\r\n", "\n")
    lines = text.splitlines()

    if len(lines) < 50:
        errors.append(
            f"{skill_md}: [SKILL_TOO_SHORT] {len(lines)} lines is below the 50-line minimum floor."
        )
    if len(lines) > 800:
        errors.append(f"{skill_md}: [SKILL_SIZE] {len(lines)} lines exceeds 800-line ceiling.")

    if not text.startswith("---\n"):
        errors.append(f"{skill_md}:1: [FRONTMATTER] Missing YAML frontmatter opening '---'.")
    else:
        m_close = re.search(r"^---[ \t]*$", text[4:], flags=re.MULTILINE)
        if not m_close:
            errors.append(f"{skill_md}:1: [FRONTMATTER] Missing YAML frontmatter closing '---'.")
        else:
            fm = text[4 : 4 + m_close.start()]
            fm_norm = " ".join(fm.split())
            fm_name = _extract_frontmatter_field(fm, "name")
            if not fm_name:
                errors.append(f"{skill_md}: [FRONTMATTER] Missing 'name:' field.")
            else:
                if not KEBAB_CASE_RE.match(fm_name):
                    errors.append(
                        f"{skill_md}: [FRONTMATTER_NAME] Frontmatter name '{fm_name}' must be kebab-case."
                    )
                if len(fm_name) > MAX_SKILL_NAME_LEN:
                    errors.append(
                        f"{skill_md}: [FRONTMATTER_NAME] Frontmatter name exceeds {MAX_SKILL_NAME_LEN} characters."
                    )
                if fm_name != skill_dir.name:
                    errors.append(
                        f"{skill_md}: [FRONTMATTER_MISMATCH] Frontmatter name '{fm_name}' does not match directory '{skill_dir.name}'."
                    )
            description = _extract_frontmatter_field(fm, "description")
            if description is None:
                errors.append(f"{skill_md}: [FRONTMATTER] Missing 'description:' field.")
            elif not description:
                errors.append(f"{skill_md}: [FRONTMATTER] Empty 'description:' field.")
            elif len(description) > MAX_DESCRIPTION_LEN:
                errors.append(
                    f"{skill_md}: [FRONTMATTER_DESCRIPTION_LENGTH] Description is {len(description)} characters; "
                    f"harnesses truncate or reject descriptions over {MAX_DESCRIPTION_LEN}."
                )
            if "Use when" not in fm_norm:
                errors.append(f"{skill_md}: [ROUTING] Frontmatter description should include 'Use when ...'.")
            if "Don't use" not in fm_norm and "Do not use" not in fm_norm:
                errors.append(
                    f"{skill_md}: [ROUTING] Frontmatter description should include negative trigger ('Don't use ...')."
                )

    for idx, line in _iter_non_fenced_lines(lines):
        if PROVENANCE_RE.match(line) or PROVENANCE_HEADING_RE.match(line):
            errors.append(
                f"{skill_md}:{idx}: [SKILL_PROVENANCE_IN_BODY] Provenance/attribution text belongs in README.md, "
                "not in the agent-facing SKILL.md (it spends context tokens on every activation)."
            )

    errors.extend(_check_relative_links(skill_md, lines))

    in_fence = False
    fence_marker = ""
    fence_lang = ""
    mermaid_lines: list[tuple[int, str]] = []

    for idx, line in enumerate(lines, start=1):
        stripped = line.strip()
        m_fence = FENCE_OPEN_RE.match(stripped)
        if m_fence:
            marker, rest = m_fence.group(1), m_fence.group(2).strip()
            if not in_fence:
                in_fence = True
                fence_marker = marker
                fence_lang = rest.lower()
                mermaid_lines = []
                continue
            elif marker[0] == fence_marker[0] and len(marker) >= len(fence_marker) and not rest:
                if fence_lang == "mermaid":
                    errors.extend(_check_mermaid(skill_md, mermaid_lines))
                in_fence = False
                fence_marker = ""
                fence_lang = ""
                continue

        if in_fence:
            if fence_lang == "mermaid":
                mermaid_lines.append((idx, line))
            if fence_lang not in ("markdown", "md", "prose") and ("\u2014" in line or "\u2013" in line):
                errors.append(
                    f"{skill_md}:{idx}: [CODE_UNICODE_DASH] Unicode em/en-dash inside fenced code block corrupts copy-paste flags."
                )

    if in_fence:
        errors.append(f"{skill_md}: [UNCLOSED_FENCE] Unclosed fenced code block.")

    return errors


def verify_adk(target: Path) -> list[str]:
    errors: list[str] = []
    if target.is_dir():
        init_py = target / "__init__.py"
        if not init_py.is_file():
            errors.append(f"{target}: [ADK_MISSING_INIT] Package directory lacks '__init__.py'.")
        agent_py = target / "agent.py"
    else:
        agent_py = target

    if not agent_py.is_file():
        errors.append(f"{agent_py}: [ADK_MISSING_AGENT] Expected agent.py at {agent_py}.")
        return errors

    source = agent_py.read_text(encoding="utf-8")
    try:
        tree = ast.parse(source, filename=str(agent_py))
    except SyntaxError as exc:
        return [f"{agent_py}:{exc.lineno}: [SYNTAX_ERROR] {exc.msg}"]

    has_root_agent = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            if any(isinstance(t, ast.Name) and t.id == "root_agent" for t in node.targets):
                has_root_agent = True
                break
        elif isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name) and node.target.id == "root_agent":
                has_root_agent = True
                break

    if not has_root_agent:
        errors.append(f"{agent_py}: [ADK_ROOT_AGENT] Module does not assign `root_agent` in AST.")

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and not node.name.startswith("_"):
            if not ast.get_docstring(node):
                errors.append(
                    f"{agent_py}:{node.lineno}: [ADK_TOOL_DOCSTRING] Public function '{node.name}' lacks a docstring "
                    "(ADK uses docstrings for LLM tool schemas)."
                )
            non_self_args = [
                a for a in node.args.args if a.arg not in ("self", "cls", "tool_context")
            ]
            missing_arg_types = [a.arg for a in non_self_args if a.annotation is None]
            if missing_arg_types or node.returns is None:
                errors.append(
                    f"{agent_py}:{node.lineno}: [ADK_TOOL_TYPE_HINTS] Public function '{node.name}' requires parameter and return type annotations."
                )
    return errors


def _strip_hcl_comments(text: str) -> str:
    """Replace HCL/Terraform comments (#, //, /* ... */) with whitespace preserving newlines."""
    def _repl(match: re.Match[str]) -> str:
        s = match.group(0)
        return "".join("\n" if ch == "\n" else " " for ch in s)

    # Match quoted strings first so # or // inside strings are preserved
    pattern = re.compile(
        r'"(?:\\.|[^"\\])*"|/\*[\s\S]*?\*/|(?:#|//)[^\n]*'
    )
    def _token_filter(m: re.Match[str]) -> str:
        tok = m.group(0)
        if tok.startswith('"'):
            return tok
        return _repl(m)

    return pattern.sub(_token_filter, text)


def verify_terraform(target: Path) -> list[str]:
    errors: list[str] = []
    if not target.is_dir():
        return [f"{target}: [TF_DIR] Expected a directory containing .tf files."]

    tf_files = sorted(
        p for p in target.rglob("*.tf") if ".terraform" not in p.parts
    )
    if not tf_files:
        return [f"{target}: [TF_EMPTY] No .tf files found in {target}."]

    root_names = {f.name for f in target.glob("*.tf")}
    for expected in ("main.tf", "variables.tf", "outputs.tf", "versions.tf"):
        if expected not in root_names:
            errors.append(f"{target}: [TF_STRUCTURE] Missing standard '{expected}' file in root module.")

    bad_iam = re.compile(r"roles/(owner|editor)|allUsers|allAuthenticatedUsers")
    for tf in tf_files:
        raw_text = tf.read_text(encoding="utf-8")
        cleaned_text = _strip_hcl_comments(raw_text)
        for idx, line in enumerate(cleaned_text.splitlines(), start=1):
            m = bad_iam.search(line)
            if m:
                errors.append(
                    f"{tf}:{idx}: [TF_IAM_LEAST_PRIVILEGE] Overly broad IAM principal/role '{m.group(0)}' detected."
                )
    return errors


def verify_okf(path: Path) -> list[str]:
    if not path.is_file():
        return [f"{path}: [MISSING] OKF file not found."]
    errors: list[str] = []
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        errors.append(f"{path}:1: [OKF_FRONTMATTER] Missing YAML frontmatter.")
    if "Cluster" not in text and "## " not in text:
        errors.append(f"{path}: [OKF_STRUCTURE] Missing structured skill catalog sections.")
    errors.extend(verify_prose(path, profile="technical"))
    return errors


def verify_codelab(path: Path) -> list[str]:
    if not path.is_file():
        return [f"{path}: [MISSING] Codelab file not found."]
    errors: list[str] = []
    text = path.read_text(encoding="utf-8")
    if "Duration:" not in text and "duration:" not in text.lower():
        errors.append(f"{path}: [CODELAB_DURATION] Codelab is missing duration metadata.")
    if "Checkpoint" not in text:
        errors.append(f"{path}: [CODELAB_CHECKPOINT] Codelab is missing verification 'Checkpoint' sections.")
    if "Cleanup" not in text and "Teardown" not in text:
        errors.append(f"{path}: [CODELAB_CLEANUP] Codelab is missing a resource 'Cleanup' / 'Teardown' section.")
    errors.extend(verify_prose(path, profile="technical"))
    return errors


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run deterministic static verification checks.")
    parser.add_argument(
        "--mode",
        choices=["prose", "skill", "adk", "terraform", "okf", "codelab"],
        required=True,
        help="Verification mode to execute.",
    )
    parser.add_argument(
        "--profile",
        choices=["narrative", "technical"],
        default="narrative",
        help="Prose profile for --mode prose (default: narrative).",
    )
    parser.add_argument("paths", nargs="+", type=Path, help="Files or directories to verify.")
    args = parser.parse_args(argv)

    all_errors: list[str] = []
    for p in args.paths:
        if args.mode == "prose":
            all_errors.extend(verify_prose(p, profile=args.profile))
        elif args.mode == "skill":
            all_errors.extend(verify_skill(p))
        elif args.mode == "adk":
            all_errors.extend(verify_adk(p))
        elif args.mode == "terraform":
            all_errors.extend(verify_terraform(p))
        elif args.mode == "okf":
            all_errors.extend(verify_okf(p))
        elif args.mode == "codelab":
            all_errors.extend(verify_codelab(p))

    if all_errors:
        print(f"=== STATIC VERIFICATION FAILED ({len(all_errors)} findings) ===")
        for err in all_errors:
            print(f"  [FAIL] {err}")
        sys.exit(1)

    print(f"=== STATIC VERIFICATION PASSED ({args.mode.upper()}: {len(args.paths)} target(s) clean) ===")


if __name__ == "__main__":
    main()
