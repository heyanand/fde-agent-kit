# `google-oss` — Google Open Source Publishing & Sanitization Standard

## Provenance & Attribution
- Portable adaptation of Google Open Source release compliance standards (`Apache-2.0` 13-line license headers, CLA/security templates, and internal identifier sanitization) for public GitHub repositories and customer deliverables.

## Cluster & Context Budget Rationale
- **Cluster:** Cluster 2 — Project-Scoped JIT Domain Skill (Included in `--pack devrel`)
- **Why Project JIT:** Attached when preparing a repository, sample, or skill kit for public GitHub export or external customer delivery.

## Directory Contents
- [`SKILL.md`](SKILL.md): Agent-facing Apache-2.0 header templates across languages and the pre-release `git grep` sanitization gate.
- [`templates/CONTRIBUTING.md`](templates/CONTRIBUTING.md): Standard Google CLA and contributor covenant template.
- [`templates/SECURITY.md`](templates/SECURITY.md): Standard vulnerability disclosure policy (`https://g.co/vulnz`).

## JIT Attachment Command
```bash
python3 /path/to/fde-agent-kit/skills/sync/scripts/sync_skills.py --project . --skills google-oss
```
