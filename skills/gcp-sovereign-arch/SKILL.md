---
name: gcp-sovereign-arch
description: >-
  Architects and validates enterprise Google Cloud and Sovereign AI
  infrastructure using Cloud Foundation Fabric (CFF) Terraform conventions,
  VPC Service Controls (VPC-SC), Customer-Managed Encryption Keys (CMEK/EKM),
  Assured Workloads, and Workload Identity Federation (WIF). Use when designing
  GCP architectures, authoring Terraform (.tf) modules, or reviewing security
  boundaries for regulated workloads. Don't use for non-cloud frontend styling.
---

# Google Cloud Sovereign & Enterprise AI Architecture (`gcp-sovereign-arch`)

Provides production guardrails and Terraform patterns for regulated Google Cloud and Vertex AI deployments (EU Sovereign Controls, FedRAMP High, DORA, HIPAA).

See [references/sovereign-controls.md](references/sovereign-controls.md) for copy-pasteable HCL blocks covering Org Policies, CMEK + Service Identities, VPC-SC Dry-Run/Ingress perimeters, IAM binding safety, Workload Identity Federation, and a pinned `versions.tf`.

---

## 1. The 5 Non-Negotiable Sovereign Cloud Guardrails

### 1.1 Zero Standing Keys (Workload Identity Federation Only)
- Enforce `constraints/iam.disableServiceAccountKeyCreation` across all folders/projects.
- External CI/CD pipelines (GitHub Actions, GitLab) and multi-cloud workloads must authenticate via **Workload Identity Federation (`google_iam_workload_identity_pool`)** with short-lived OIDC/SAML tokens.
- Every microservice, Cloud Run job, or ADK agent runtime must run under its own dedicated, purpose-scoped Service Account (never the default Compute Engine service account).

### 1.2 Least-Privilege, Resource-Scoped IAM
- **Forbidden Roles & Principals:** Never grant `roles/owner`, `roles/editor`, `allUsers`, or `allAuthenticatedUsers`.
- **Scope Down to the Resource:** Grant `roles/secretmanager.secretAccessor` on the specific secret (`google_secret_manager_secret_iam_member`), `roles/storage.objectViewer` on the specific bucket, and `roles/bigquery.dataViewer` on the specific dataset — not at the project root.
- **Avoid the `google_project_iam_binding` Footgun:** Never use project-wide authoritative `google_project_iam_binding` on roles shared with Google-managed service agents (`service-*@gcp-sa-*.iam.gserviceaccount.com`), as it strips control-plane access. Prefer Cloud Foundation Fabric (`iam_bindings_additive`) or resource-scoped `_iam_member` resources.

### 1.3 Customer-Managed Encryption Keys (CMEK / Cloud EKM)
- Enforce `constraints/gcp.restrictNonCmekServices` and `constraints/gcp.restrictCmekCryptoKeyProjects`.
- Provision the service agent identity explicitly via `google_project_service_identity` (`aiplatform.googleapis.com`, `bigquery.googleapis.com`, `storage.googleapis.com`, `run.googleapis.com`) **before** creating the CMEK-encrypted resource, with explicit `depends_on` on the `google_kms_crypto_key_iam_member` grant.
- Configure `rotation_period = "7776000s"` (90 days) and `lifecycle { prevent_destroy = true }` on all production `google_kms_crypto_key` resources.

### 1.4 VPC Service Controls (VPC-SC) & Private Google Access
- Route all Google API traffic over **Private Google Access** (`restricted.googleapis.com` -> `199.36.153.4/30`) with `vpc_accessible_services` restricted to `RESTRICTED-SERVICES`.
- Always deploy new or modified VPC-SC perimeters in **Dry-Run (`spec`) mode** first (`use_explicit_dry_run_spec = true`), audit Cloud Audit Logs for false-positive blocks, and document the required **Ingress** and **Egress** rules before enforcing in `status`.

### 1.5 Cloud Foundation Fabric (CFF) Terraform Module Standards
Every Terraform module must include:
- `main.tf`: Core resource definitions or CFF module calls (`github.com/GoogleCloudPlatform/cloud-foundation-fabric//modules/...` pinned to a release tag `?ref=v34.0.0`).
- `variables.tf`: Typed inputs (`type`, `description`, `default`, and `validation` blocks for region/prefix constraints).
- `outputs.tf`: Explicit resource IDs, service account emails, and endpoint URIs.
- `versions.tf`: Pinned `required_version = ">= 1.6.0"` and `google` / `google-beta` provider constraints.

---

## 2. Mandatory Verification Gate

Run `verify_static.py --mode terraform` (plus `terraform fmt -check` and `terraform validate` when the binary is installed) before completing any infrastructure task (`<skill-dir>` is the directory containing this `SKILL.md`; sibling kit skills such as `verify` and `sdlc-and-portal` resolve as `<skill-dir>/../<skill>` because every harness links skills from the same `fde-agent-kit` clone.):
```bash
python3 <skill-dir>/../verify/scripts/verify_static.py --mode terraform path/to/terraform_module/
```
This recursively audits all `*.tf` files (stripping `#`, `//`, and `/* ... */` comments) to ensure:
1. Root module contains `main.tf`, `variables.tf`, `outputs.tf`, and `versions.tf`.
2. Zero occurrences of `roles/owner`, `roles/editor`, `allUsers`, or `allAuthenticatedUsers`.

## Common Rationalizations

| Rationalization | Reality |
| :--- | :--- |
| "It's just a PoC, I'll use `roles/editor` and tighten IAM before production" | PoC Terraform modules get copy-pasted directly into production. Write least-privilege resource-scoped bindings from day one. |
| "I'll export a JSON service account key for the GitHub Action" | Service account keys do not expire and are the #1 cause of cloud breaches. Configure Workload Identity Federation (`WIF`) in 20 lines of HCL. |
| "I'll attach the KMS key to the Vertex AI resource without `google_project_service_identity`" | `terraform apply` will fail on a fresh project because the Vertex AI service agent does not exist until explicitly provisioned. |
| "I'll enable VPC-SC in enforced mode immediately" | Enforcing VPC-SC without dry-run analysis and ingress/egress rules breaks CI/CD runners and cross-project telemetry immediately. |

## Red Flags

- Any `.tf` file granting `roles/owner`, `roles/editor`, `allUsers`, or `allAuthenticatedUsers`
- Creating `google_service_account_key` resources instead of Workload Identity Federation
- Using project-wide authoritative `google_project_iam_binding` on shared roles
- Missing `versions.tf`, `variables.tf`, `outputs.tf`, or `main.tf` in a Terraform module
- Unpinned Git module sources (`?ref=main` instead of a release tag or commit SHA)
- CMEK-protected resources missing `depends_on` for the KMS `cryptoKeyEncrypterDecrypter` IAM binding

## Verification

- [ ] Module passes `python3 <skill-dir>/../verify/scripts/verify_static.py --mode terraform <dir>` with 0 findings
- [ ] All CMEK resources depend on explicit `google_project_service_identity` and `google_kms_crypto_key_iam_member` grants
- [ ] VPC-SC perimeters define explicit `ingress_policies` / `egress_policies` and dry-run (`spec`) configuration
- [ ] Architecture diagrams quote all node labels containing parentheses (`CloudRun["Agent Gateway (europe-west3)"]`)
