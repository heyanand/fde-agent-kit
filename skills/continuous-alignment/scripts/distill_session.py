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
"""Session Transcript Distiller & AGENTS.md Budget Enforcer (distill_session.py)."""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path
import re
import sys
from typing import Any


BUDGET_MAX_LINES = 200
BUDGET_WARN_LINES = 180
MAX_LISTED_ITEMS = 10
EXIT_CODE_RE = re.compile(r"exited with code (-?[1-9]\d*)", re.IGNORECASE)
RULE_FILES = ("AGENTS.md", "GEMINI.md", "CLAUDE.md", "rules/AGENTS.md")
ADR_DIR_CANDIDATES = (
    "docs/adr",
    "docs/decisions",
    "doc/adr",
    ".gemini/knowledge/ADRs",
)


def check_budget(project_dir: Path) -> int:
    if not project_dir.is_dir():
        sys.exit(f"Error: --check-budget expects a project directory, got: {project_dir}")
    violations = 0
    seen_resolved: set[Path] = set()
    found_any = False

    for rel_name in RULE_FILES:
        candidate = project_dir / rel_name
        if not candidate.is_file():
            continue
        resolved = candidate.resolve()
        if resolved in seen_resolved:
            print(f"[SKIP_SYMLINK] {candidate} -> {resolved} (already audited)")
            continue
        seen_resolved.add(resolved)
        found_any = True

        line_count = len(
            candidate.read_text(encoding="utf-8", errors="replace").splitlines()
        )
        if line_count > BUDGET_MAX_LINES:
            status = "OVER_BUDGET"
            violations += 1
        elif line_count > BUDGET_WARN_LINES:
            status = "NEAR_BUDGET"
        else:
            status = "PASS"
        print(f"[{status}] {candidate}: {line_count}/{BUDGET_MAX_LINES} lines")
        if status == "NEAR_BUDGET":
            print(
                f"  -> Over {BUDGET_WARN_LINES} lines: extract domain-specific sections into "
                ".agents/rules/<domain>.md or skills/<name>/SKILL.md."
            )

    if not found_any:
        print(
            f"[WARN] No rule files ({', '.join(RULE_FILES)}) found in {project_dir}."
        )
    return violations


def _decode_arg(value: Any) -> Any:
    """Antigravity transcripts JSON-encode string args (e.g. '"pytest -q"'); unwrap them."""
    if isinstance(value, str) and len(value) >= 2 and value[0] == value[-1] == '"':
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    return value


def _describe_tool_call(call: Any) -> str:
    """Return a short human-readable label (command line or tool name) for a tool call."""
    if not isinstance(call, dict):
        return "tool"
    args = call.get("args")
    if args is None:
        args = call.get("arguments")
    if isinstance(args, str):
        try:
            args = json.loads(args)
        except json.JSONDecodeError:
            args = {}
    if not isinstance(args, dict):
        args = {}
    cmd = _decode_arg(args.get("CommandLine") or args.get("command") or args.get("cmd"))
    label = str(cmd) if cmd else str(call.get("name", "tool"))
    return label.replace("\n", " ")[:120]


def _describe_tool_use(item: dict[str, Any]) -> str:
    """Label a Claude Code / Gemini CLI tool_use block by its command, path, or tool name."""
    tool_input = item.get("input") if isinstance(item.get("input"), dict) else {}
    for key in ("command", "cmd", "file_path", "path", "pattern", "url"):
        if tool_input.get(key):
            return str(tool_input[key]).replace("\n", " ")[:120]
    return str(item.get("name", "tool"))


def _extract_step_info(
    step: dict[str, Any],
    tool_use_labels: dict[str, str] | None = None,
) -> tuple[str | None, int, list[str]]:
    """Extract (user_message, tool_call_count, failed_commands) across harness schemas.

    `tool_use_labels` maps Claude Code tool_use ids to command labels so a later
    `tool_result` error can name the command that failed, not just its error text.
    """
    if tool_use_labels is None:
        tool_use_labels = {}
    user_msg: str | None = None
    tool_count = 0
    failures: list[str] = []

    step_type = step.get("type", "")
    # 1. Google Antigravity JSONL schema
    if step_type == "USER_INPUT" and step.get("content"):
        user_msg = str(step["content"]).strip()
    if isinstance(step.get("tool_calls"), list):
        calls = step["tool_calls"]
        tool_count += len(calls)
        if step.get("status") == "ERROR":
            for c in calls:
                err = str(step.get("content", "ERROR")).replace("\n", " ")[:120]
                failures.append(f"{_describe_tool_call(c)}: {err}")

    # 2. Claude Code / Gemini CLI JSONL schema
    msg_obj = step.get("message") if isinstance(step.get("message"), dict) else step
    role = msg_obj.get("role") or step.get("role")
    content = msg_obj.get("content")
    if (step_type == "user" or role == "user") and user_msg is None:
        if isinstance(content, str) and content.strip():
            user_msg = content.strip()
        elif isinstance(content, list):
            text_parts = []
            for item in content:
                if isinstance(item, dict):
                    if item.get("type") == "text" and item.get("text"):
                        text_parts.append(str(item["text"]).strip())
                    elif item.get("type") == "tool_result" and item.get("is_error"):
                        err_txt = _tool_result_text(item.get("content")).replace("\n", " ")
                        label = tool_use_labels.get(str(item.get("tool_use_id", "")))
                        failures.append(f"{label}: {err_txt[:120]}" if label else err_txt[:140])
            if text_parts:
                user_msg = " ".join(text_parts)

    if role == "assistant" and isinstance(content, list):
        for item in content:
            if isinstance(item, dict) and item.get("type") == "tool_use":
                tool_count += 1
                if item.get("id"):
                    tool_use_labels[str(item["id"])] = _describe_tool_use(item)

    return user_msg, tool_count, failures


def _tool_result_text(content: Any) -> str:
    """Flatten tool_result content, which may be a string or a list of text blocks."""
    if isinstance(content, list):
        texts = [str(c.get("text", "")) for c in content if isinstance(c, dict)]
        return " ".join(t for t in texts if t) or "tool_result error"
    return str(content) if content else "tool_result error"


def _tool_result_failure(step: dict[str, Any], pending_calls: list[Any]) -> str | None:
    """Detect a failed Antigravity tool-result step and attribute it to its pending call.

    Antigravity records tool calls on PLANNER_RESPONSE steps and the results on the
    following non-planner steps, whose `status` is ERROR or whose content reports a
    non-zero `exited with code N`.
    """
    content = str(step.get("content", ""))
    call = pending_calls[0] if pending_calls else {}
    call_args = call.get("args") or call.get("arguments") if isinstance(call, dict) else None
    # Only trust "exited with code N" for shell-style calls, not file reads that quote it.
    is_shell = isinstance(call_args, (dict, str)) and "CommandLine" in str(call_args)
    exit_match = EXIT_CODE_RE.search(content[:600]) if is_shell else None
    if step.get("status") != "ERROR" and not exit_match:
        return None
    label = _describe_tool_call(pending_calls[0]) if pending_calls else "tool"
    reason = f"exit code {exit_match.group(1)}" if exit_match else content.replace("\n", " ")[:120]
    return f"{label}: {reason or 'ERROR'}"


def _print_capped(items: list[str], prefix: str, start: int = 1) -> None:
    for idx, item in enumerate(items[:MAX_LISTED_ITEMS], start=start):
        print(f"  [{prefix}{idx}] {item}")
    if len(items) > MAX_LISTED_ITEMS:
        print(f"  ... and {len(items) - MAX_LISTED_ITEMS} more (truncated)")


def analyze_transcript(transcript_path: Path) -> dict[str, Any]:
    if not transcript_path.is_file():
        sys.exit(f"Error: Transcript not found: {transcript_path}")

    user_messages: list[str] = []
    tool_calls = 0
    failed_events: list[str] = []
    skipped_lines = 0
    pending_calls: list[Any] = []
    tool_use_labels: dict[str, str] = {}

    with transcript_path.open(encoding="utf-8", errors="replace") as handle:
        for raw_line in handle:
            if not raw_line.strip():
                continue
            try:
                step = json.loads(raw_line)
            except json.JSONDecodeError:
                skipped_lines += 1
                continue
            if not isinstance(step, dict):
                skipped_lines += 1
                continue

            step_type = step.get("type", "")
            if step_type == "PLANNER_RESPONSE" and isinstance(step.get("tool_calls"), list):
                # Results for these calls arrive on the following non-planner steps.
                pending_calls = list(step["tool_calls"]) if step.get("status") != "ERROR" else []
            elif pending_calls and step_type not in ("USER_INPUT", "PLANNER_RESPONSE"):
                failure = _tool_result_failure(step, pending_calls)
                if failure:
                    failed_events.append(failure)
                pending_calls.pop(0)
            elif step_type == "USER_INPUT":
                pending_calls = []

            u_msg, t_count, step_failures = _extract_step_info(step, tool_use_labels)
            if u_msg:
                user_messages.append(u_msg)
            tool_calls += t_count
            failed_events.extend(step_failures)

    print(f"=== Transcript Summary: {transcript_path.name} ===")
    print(f"Total User Prompts : {len(user_messages)}")
    print(f"Total Tool Calls   : {tool_calls}")
    print(f"Failed Tool Events : {len(failed_events)}")
    if skipped_lines:
        print(f"Skipped Lines      : {skipped_lines} (malformed or non-object JSON)")
    if not user_messages and not tool_calls:
        print(
            "[WARN] No recognizable steps found. Supported schemas: Google Antigravity "
            "(USER_INPUT / PLANNER_RESPONSE.tool_calls) and Claude Code / Gemini CLI "
            "(role: user/assistant, tool_use, tool_result)."
        )

    if len(user_messages) > 1:
        print("\nFollow-up User Prompts (Inspect for reusable corrections/rules):")
        snippets = [m.replace("\n", " ")[:160] for m in user_messages[1:]]
        _print_capped(snippets, prefix="", start=2)

    if failed_events:
        print("\nFailed Commands / Tool Errors (Candidate gotchas for AGENTS.md or skills):")
        _print_capped(failed_events, prefix="ERR-")

    return {
        "user_messages": user_messages,
        "tool_calls": tool_calls,
        "failed_events": failed_events,
    }


def resolve_adr_dir(project_dir: Path) -> Path:
    for rel in ADR_DIR_CANDIDATES:
        candidate = project_dir / rel
        if candidate.is_dir():
            return candidate
    return project_dir / "docs" / "adr"


def create_adr(
    project_dir: Path,
    title: str,
    status: str = "Proposed",
) -> Path:
    title = " ".join(title.split())
    if not title:
        sys.exit("Error: --new-adr requires a non-empty title.")
    if not project_dir.is_dir():
        sys.exit(f"Error: --project directory does not exist: {project_dir}")
    adr_dir = resolve_adr_dir(project_dir)
    adr_dir.mkdir(parents=True, exist_ok=True)

    # Accept 0001-foo.md, ADR-0001-foo.md, adr-001_foo.md, etc.
    num_pattern = re.compile(r"^(?:adr-)?(\d{3,4})[-_]", re.IGNORECASE)
    existing_nums: list[int] = []
    for p in adr_dir.glob("*.md"):
        m = num_pattern.match(p.name)
        if m:
            existing_nums.append(int(m.group(1)))

    next_num = max(existing_nums, default=0) + 1
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:60].rstrip("-")
    if not slug:
        slug = f"decision-{next_num:04d}"

    adr_path = adr_dir / f"{next_num:04d}-{slug}.md"
    content = f"""# ADR-{next_num:04d}: {title}

- **Status:** {status}
- **Date:** {date.today().isoformat()}
- **Deciders:** [Names / Roles]

## Context and Problem Statement
[Describe the architectural force, constraint, or integration problem in 2-4 sentences.]

## Decision Drivers
- **Driver 1:** [e.g., latency, sovereignty, maintainability]
- **Driver 2:** [e.g., operational simplicity]

## Considered Options
1. **Option 1:** [Summary]
2. **Option 2:** [Summary]
3. **Option 3:** [Summary]

## Decision Outcome
Chosen option: **[Option N]**, because [concrete rationale linking back to Decision Drivers].

### Consequences
- **Positive:** [Concrete operational or architectural gain]
- **Negative / Trade-offs:** [Concrete cost, complexity, or constraint accepted]
- **Mitigations:** [How negative consequences are bounded or monitored]

## Pros and Cons of the Options

### Option 1: [Name]
- **Pros:** [...]
- **Cons:** [...]

### Option 2: [Name]
- **Pros:** [...]
- **Cons / Why Rejected:** [Specific dealbreaker or trade-off]
"""
    with adr_path.open("x", encoding="utf-8") as f:
        f.write(content)

    index_path = adr_dir / "README.md"
    entry_line = f"- [ADR-{next_num:04d}: {title}]({adr_path.name}) ({status}, {date.today().isoformat()})\n"
    if not index_path.exists():
        index_path.write_text(
            f"# Architecture Decision Records\n\n{entry_line}",
            encoding="utf-8",
        )
    else:
        existing_index = index_path.read_text(encoding="utf-8")
        if adr_path.name not in existing_index:
            separator = "" if not existing_index or existing_index.endswith("\n") else "\n"
            with index_path.open("a", encoding="utf-8") as idx_file:
                idx_file.write(separator + entry_line)

    print(f"[OK] Created ADR -> {adr_path}")
    return adr_path


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Enforce AGENTS.md budget, distill transcripts, and create ADRs.",
        epilog=(
            "Examples:\n"
            "  %(prog)s --transcript path/to/transcript.jsonl\n"
            "  %(prog)s --project . --new-adr \"Use Pub/Sub for ingestion\"\n"
            "  %(prog)s --check-budget .   (exit 1 if any rule file > 200 lines)"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--check-budget",
        type=Path,
        help="Project directory to audit rule file line budgets.",
    )
    parser.add_argument(
        "--transcript",
        type=Path,
        help="Path to transcript.jsonl to summarize.",
    )
    parser.add_argument(
        "--project",
        type=Path,
        default=Path("."),
        help="Target project root for --new-adr.",
    )
    parser.add_argument(
        "--new-adr",
        type=str,
        help="Title of a new MADR decision record to scaffold.",
    )
    parser.add_argument(
        "--status",
        type=str,
        default="Proposed",
        choices=["Proposed", "Accepted", "Deprecated", "Superseded"],
        help="Initial status for --new-adr (default: Proposed).",
    )
    args = parser.parse_args(argv)

    did_work = False
    violations = 0

    if args.transcript:
        analyze_transcript(args.transcript)
        did_work = True

    if args.new_adr:
        create_adr(args.project.resolve(), args.new_adr, status=args.status)
        did_work = True

    if args.check_budget:
        violations = check_budget(args.check_budget.resolve())
        did_work = True

    if not did_work:
        parser.print_help()
        sys.exit(2)

    if violations:
        sys.exit(1)


if __name__ == "__main__":
    main()
