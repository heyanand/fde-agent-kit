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
"""Compiles Markdown documents or directories into a single-file HTML presentation portal."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
import re
import sys


TEMPLATE_PATH = Path(__file__).resolve().parent.parent / "templates" / "portal.html"
MARKDOWN_SUFFIXES = (".md", ".markdown")
TEMPLATE_TOKEN_RE = re.compile(r"__PORTAL_TITLE__|__PORTAL_PAYLOAD_JSON__")
ATX_HEADING_RE = re.compile(r"^#\s+(.+?)\s*#*\s*$")
SKIPPED_DIR_NAMES = {"node_modules", "venv", "__pycache__", "site-packages"}


def _is_skipped(path: Path, root: Path) -> bool:
    """Skip hidden and vendored directories (e.g. .git, node_modules) during recursion."""
    rel_parts = path.relative_to(root).parts[:-1]
    return any(part in SKIPPED_DIR_NAMES or part.startswith(".") for part in rel_parts)


def collect_markdown_files(inputs: list[Path]) -> list[Path]:
    collected: list[Path] = []
    seen: set[Path] = set()

    def _add(path: Path) -> None:
        resolved = path.resolve()
        if resolved not in seen:  # Dedupe a file passed both directly and via its directory.
            seen.add(resolved)
            collected.append(path)

    for item in inputs:
        if not item.exists():
            raise SystemExit(f"Error: Markdown path not found: {item}")
        if item.is_dir():
            md_files = sorted(
                p
                for p in item.rglob("*")
                if p.is_file()
                and p.suffix.lower() in MARKDOWN_SUFFIXES
                and not _is_skipped(p, item)
            )
            if not md_files:
                raise SystemExit(
                    f"Error: No Markdown (*.md, *.markdown) files found inside directory: {item}"
                )
            for md in md_files:
                _add(md)
        elif item.suffix.lower() not in MARKDOWN_SUFFIXES:
            raise SystemExit(
                f"Error: Not a Markdown file (expected .md or .markdown): {item}"
            )
        else:
            _add(item)
    return collected


def strip_front_matter(content: str) -> str:
    """Drop a leading YAML front matter block so it never renders as a setext heading."""
    lines = content.splitlines(keepends=True)
    if lines and lines[0].strip() == "---":
        for idx in range(1, len(lines)):
            if lines[idx].strip() in ("---", "..."):
                return "".join(lines[idx + 1 :]).lstrip("\r\n")
    return content


def extract_title(content: str, fallback: str) -> str:
    """Return the first level-1 ATX heading outside YAML front matter and code fences."""
    fence: str | None = None
    for line in strip_front_matter(content).splitlines():
        stripped = line.strip()
        if stripped.startswith(("```", "~~~")):
            marker = stripped[:3]
            if fence is None:
                fence = marker
            elif marker == fence:
                fence = None
            continue
        if fence is None:
            match = ATX_HEADING_RE.match(line)
            if match and match.group(1).strip():
                return match.group(1).strip()
    return fallback


def build_sections(md_paths: list[Path]) -> list[dict[str, str]]:
    sections: list[dict[str, str]] = []
    used_ids: set[str] = set()

    for md_path in md_paths:
        try:
            content = md_path.read_text(encoding="utf-8-sig")
        except UnicodeDecodeError as exc:
            raise SystemExit(f"Error: {md_path} is not valid UTF-8 ({exc}).") from exc
        fallback_title = md_path.stem.replace("-", " ").replace("_", " ").title()
        content = strip_front_matter(content)
        first_heading = extract_title(content, fallback_title)

        base_id = re.sub(r"[^a-z0-9-]+", "-", md_path.stem.lower()).strip("-") or "section"
        candidate_id = base_id
        if candidate_id in used_ids and md_path.parent.name:
            parent_slug = re.sub(r"[^a-z0-9-]+", "-", md_path.parent.name.lower()).strip("-")
            if parent_slug:
                candidate_id = f"{parent_slug}-{base_id}"
        counter = 2
        while candidate_id in used_ids:
            candidate_id = f"{base_id}-{counter}"
            counter += 1
        used_ids.add(candidate_id)

        sections.append(
            {
                "id": candidate_id,
                "title": first_heading,
                "source": str(md_path.name),
                "markdown": content,
            }
        )
    return sections


def serialize_sections_safely(sections: list[dict[str, str]]) -> str:
    """Serialize JSON safe for embedding inside a <script> element (C4).

    Escapes every `<`, `>`, and `&` as JSON unicode escapes. This blocks both
    `</script>` breakout and the `<!--<script>` "double-escaped" parser state that
    a plain `</` -> `<\\/` replacement does not cover. JSON.parse restores the text.
    """
    raw_json = json.dumps(sections, ensure_ascii=False)
    return (
        raw_json.replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )


def compile_portal(title: str, inputs: list[Path], output_path: Path) -> Path:
    if output_path.is_dir():
        raise SystemExit(f"Error: --output must be a file path, not a directory: {output_path}")
    if output_path.suffix.lower() not in (".html", ".htm"):
        print(f"[WARN] --output does not end in .html: {output_path}", file=sys.stderr)
    if not TEMPLATE_PATH.is_file():
        raise SystemExit(f"Error: Portal template missing: {TEMPLATE_PATH}")

    md_paths = collect_markdown_files(inputs)
    sections = build_sections(md_paths)
    safe_json = serialize_sections_safely(sections)

    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    replacements = {
        "__PORTAL_TITLE__": html.escape(title.strip() or "Technical Architecture Portal"),
        "__PORTAL_PAYLOAD_JSON__": safe_json,
    }
    # Single-pass substitution so a title containing a token can never inject the payload.
    rendered = TEMPLATE_TOKEN_RE.sub(lambda m: replacements[m.group(0)], template)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rendered, encoding="utf-8")
    print(f"[OK] Compiled {len(sections)} document(s) -> {output_path}")
    return output_path


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Compile Markdown files or directories into a single-file interactive HTML portal.",
        epilog=(
            "Example:\n  %(prog)s --title \"Architecture Portal\" --output dist/portal.html "
            "docs/PRD.md docs/adr/\n\nDirectories are searched recursively for *.md / "
            "*.markdown (hidden dirs, node_modules, venv, and __pycache__ are skipped). Sections "
            "are deep-linkable via #<section-id>."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--title", default="Technical Architecture Portal", help="Portal title")
    parser.add_argument("--output", type=Path, required=True, help="Output HTML file path")
    parser.add_argument("files", nargs="+", type=Path, help="Input Markdown files or directories")
    args = parser.parse_args(argv)
    compile_portal(args.title, args.files, args.output)


if __name__ == "__main__":
    main()
