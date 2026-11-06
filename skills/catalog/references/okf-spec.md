# Open Knowledge Format (OKF v0.2) Specification

Open Knowledge Format (OKF) structures project domain knowledge, architecture references, and runbooks into modular, machine-navigable Markdown trees with minimal token overhead. An agent reads one small index, picks the concept file whose triggers match the task, and never loads the rest.

## 1. Directory Layout

```text
docs/knowledge/                 (or references/)
|-- INDEX.okf.md                # Master routing index (< 100 lines)
|-- architecture/
|   |-- vpc-sc-perimeter.md
|   `-- cmek-key-rotation.md
`-- operations/
    `-- incident-triage.md
```

## 2. `INDEX.okf.md` Schema

| Field | Required | Format | Purpose |
| :--- | :---: | :--- | :--- |
| `okf_version` | Yes | Quoted string, `"0.2"` | Lets tooling reject indexes written for an incompatible schema. |
| `generated_at` | Yes | ISO 8601 date (`2026-11-05`) | Signals staleness; regenerate when concept files change. |
| `scope` | Yes | Relative path or one-line description | States which directory the index covers. |

The body contains one `## Cluster: <topic>` section per topic, each with a routing table:

| Column | Content |
| :--- | :--- |
| `File` | Relative Markdown link to the concept file. |
| `Use when` | Positive trigger: the task or question this file answers. |
| `Don't use for` | Negative boundary that prevents mis-routing to a neighbor file. |

## 3. Complete Example `INDEX.okf.md`

```markdown
---
okf_version: "0.2"
generated_at: 2026-11-05
scope: docs/knowledge
---

# Knowledge Index: Sovereign Agent Platform

## Cluster: Architecture

| File | Use when | Don't use for |
| :--- | :--- | :--- |
| [vpc-sc-perimeter.md](architecture/vpc-sc-perimeter.md) | Designing ingress/egress rules or restricted VIP access | Key management (see cmek-key-rotation.md) |
| [cmek-key-rotation.md](architecture/cmek-key-rotation.md) | Rotating or scoping Cloud KMS keys | Network perimeter design |

## Cluster: Operations

| File | Use when | Don't use for |
| :--- | :--- | :--- |
| [incident-triage.md](operations/incident-triage.md) | Paging alert fired; need first-15-minute steps | Postmortem writing |
```

Validate it with `verify_static.py --mode okf docs/knowledge/INDEX.okf.md`. The OKF mode checks for YAML frontmatter, at least one `##` section, closed code fences, and Mermaid hygiene.

## 4. Concept File Frontmatter Schema

Every concept file referenced by the index begins with YAML frontmatter so agents can confirm relevance from the first lines:

```yaml
---
id: arch-vpc-sc-perimeter
title: VPC Service Controls Perimeter Design
summary: Ingress/egress policies, restricted VIPs, and bridge perimeter patterns for regulated GCP workloads.
tags: [gcp, security, vpc-sc, sovereign-cloud]
updated: 2026-11-05
---
```

- `id` is stable kebab-case and unique across the knowledge tree; renaming a file must not change its `id`.
- `summary` is one sentence; the index's `Use when` column may reuse it.

## 5. Edge Cases

- **More than ~100 index lines:** Split into `architecture/INDEX.okf.md`, `operations/INDEX.okf.md`, and link those sub-indexes from the root index.
- **Concept file without frontmatter:** Add frontmatter before indexing; do not invent a summary the file does not support.
- **Duplicate topics across files:** Merge them or give each a distinct `Don't use for` boundary; two rows with the same trigger defeat routing.
- **Moved or deleted files:** Regenerate the index and bump `generated_at`; stale links mislead agents more than a missing index does.
