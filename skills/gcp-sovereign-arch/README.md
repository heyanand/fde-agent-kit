# `gcp-sovereign-arch` — Google Cloud Sovereign & Enterprise AI Architecture

## Provenance & Attribution
- Authored for Forward Deployed Engineering on Google Cloud, synthesizing Cloud Foundation Fabric (CFF) Terraform standards, Assured Workloads, VPC Service Controls (VPC-SC), CMEK/EKM, and Workload Identity Federation (WIF) best practices.

## Cluster & Context Budget Rationale
- **Cluster:** Cluster 2 — Project-Scoped JIT Domain Skill (Included in `--pack arch` and `--pack adk`)
- **Why Project JIT:** Attached when architecting regulated Google Cloud infrastructure or writing Terraform modules so heavy HCL reference patterns are only loaded in cloud infrastructure workspaces.

## Directory Contents
- [`SKILL.md`](SKILL.md): Agent-facing 5 non-negotiable Sovereign Cloud guardrails and `verify_static.py --mode terraform` gate.
- [`references/sovereign-controls.md`](references/sovereign-controls.md): Copy-pasteable HCL reference blocks for Org Policies, CMEK + Service Identities, VPC-SC Dry-Run/Ingress perimeters, and additive IAM bindings.

## JIT Attachment Command
```bash
python3 /path/to/fde-agent-kit/skills/sync/scripts/sync_skills.py --project . --skills gcp-sovereign-arch
```
