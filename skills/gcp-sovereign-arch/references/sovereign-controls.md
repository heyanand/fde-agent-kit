# Sovereign Cloud, VPC-SC, CMEK & Cloud Foundation Fabric Reference

Authoritative reference patterns for the `gcp-sovereign-arch` skill.

---

## 1. Sovereign Compliance Regimes & Organization Policies

| Compliance Regime | Key GCP Controls Required | Mandatory Organization Policy Constraints |
| :--- | :--- | :--- |
| **EU Sovereign Controls / Cloud Sovereign** | EU-only regions (`europe-west3`, `europe-west1`, `europe-west4`), CMEK with EKM/HSM, Access Transparency + Access Approval (EU personnel) | `constraints/gcp.resourceLocations`, `constraints/gcp.restrictNonCmekServices`, `constraints/gcp.restrictCmekCryptoKeyProjects` |
| **US FedRAMP High / IL4** | Assured Workloads folder, FIPS 140-2 validated KMS, VPC-SC enforced perimeter, Private Google Access (`restricted.googleapis.com`) | `constraints/compute.vmExternalIpAccess` (Deny All), `constraints/iam.disableServiceAccountKeyCreation` |
| **Regulated Financial / Healthcare (DORA / HIPAA)** | Dedicated VPC-SC perimeter per environment, CMEK 90-day key rotation, immutable Cloud Audit Logs (Data Access enabled) | `constraints/storage.uniformBucketLevelAccess`, `constraints/sql.restrictPublicIp` |

### Essential Organization Policy Constraints (Terraform)
```hcl
resource "google_org_policy_policy" "restrict_non_cmek" {
  name   = "projects/${var.project_id}/policies/gcp.restrictNonCmekServices"
  parent = "projects/${var.project_id}"

  spec {
    rules {
      values {
        all_values = "ALLOW"
      }
      # Explicitly require CMEK on Vertex AI, BigQuery, Cloud Storage, and Secret Manager
    }
  }
}

resource "google_org_policy_policy" "disable_sa_keys" {
  name   = "projects/${var.project_id}/policies/iam.disableServiceAccountKeyCreation"
  parent = "projects/${var.project_id}"

  spec {
    rules {
      enforce = "TRUE"
    }
  }
}
```

---

## 2. Customer-Managed Encryption Keys (CMEK) & Service Agent Identity

Before any CMEK-protected resource (`aiplatform.googleapis.com`, `bigquery.googleapis.com`, `storage.googleapis.com`) can use a Cloud KMS key, you **must** provision the Google-managed service identity and grant `roles/cloudkms.cryptoKeyEncrypterDecrypter` **on the specific key** (never at the project level):

```hcl
# 1. Provision the Vertex AI Google-managed service agent
resource "google_project_service_identity" "vertex_sa" {
  provider = google-beta
  project  = var.project_id
  service  = "aiplatform.googleapis.com"
}

# 2. Key Ring & CryptoKey with 90-day rotation (HSM protection level for Sovereign workloads)
resource "google_kms_key_ring" "sovereign_ring" {
  name     = "${var.prefix}-kr-${var.region}"
  location = var.region
  project  = var.kms_project_id
}

resource "google_kms_crypto_key" "vertex_cmek" {
  name            = "${var.prefix}-vertex-key"
  key_ring        = google_kms_key_ring.sovereign_ring.id
  rotation_period = "7776000s" # 90 days
  purpose         = "ENCRYPT_DECRYPT"

  version_template {
    algorithm        = "GOOGLE_SYMMETRIC_ENCRYPTION"
    protection_level = var.use_hsm ? "HSM" : "SOFTWARE"
  }

  lifecycle {
    prevent_destroy = true
  }
}

# 3. Resource-scoped additive grant on the single KMS CryptoKey (never project-wide)
resource "google_kms_crypto_key_iam_member" "vertex_cmek_binding" {
  crypto_key_id = google_kms_crypto_key.vertex_cmek.id
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = "serviceAccount:${google_project_service_identity.vertex_sa.email}"
}

# 4. CMEK-protected resource: depend on the key grant so the first apply never races IAM
resource "google_vertex_ai_dataset" "sovereign_dataset" {
  provider            = google-beta
  project             = var.project_id
  region              = var.region
  display_name        = "${var.prefix}-dataset"
  metadata_schema_uri = "gs://google-cloud-aiplatform/schema/dataset/metadata/tabular_1.0.0.yaml"

  encryption_spec {
    kms_key_name = google_kms_crypto_key.vertex_cmek.id
  }

  depends_on = [google_kms_crypto_key_iam_member.vertex_cmek_binding]
}
```

---

## 3. VPC Service Controls (VPC-SC): Dry-Run First, Then Enforced

Never deploy an enforced VPC-SC perimeter directly into an active project without first validating traffic in **Dry-Run (`spec`) mode** via Cloud Audit Logs (`violationReason`).

```hcl
resource "google_access_context_manager_service_perimeter" "sovereign_ai_perimeter" {
  parent = "accessPolicies/${var.access_policy_id}"
  name   = "accessPolicies/${var.access_policy_id}/servicePerimeters/${var.perimeter_name}"
  title  = "Sovereign AI Perimeter"

  # Always test changes in spec (dry-run) mode before promoting to status (enforced)
  use_explicit_dry_run_spec = true

  status {
    resources = ["projects/${var.project_number}"]
    restricted_services = [
      "aiplatform.googleapis.com",
      "bigquery.googleapis.com",
      "storage.googleapis.com",
      "secretmanager.googleapis.com",
      "kms.googleapis.com",
      "run.googleapis.com",
    ]

    vpc_accessible_services {
      enable_restriction = true
      allowed_services   = ["RESTRICTED-SERVICES"]
    }

    ingress_policies {
      ingress_from {
        identities   = ["serviceAccount:${var.gateway_sa_email}"]
        access_levels = [var.corp_access_level_name]
      }
      ingress_to {
        resources = ["*"]
        operations {
          service_name = "aiplatform.googleapis.com"
          method_selectors {
            method = "*"
          }
        }
      }
    }
  }
}
```

---

## 4. IAM Binding Safety: Authoritative vs. Additive Trap

> [!WARNING]
> **Critical Production Footgun:** Never use project-wide authoritative `google_project_iam_binding` or `google_project_iam_policy` on roles shared with Google-managed service agents (such as `roles/run.serviceAgent`, `roles/aiplatform.serviceAgent`, or `roles/cloudkms.cryptoKeyEncrypterDecrypter`). Doing so overwrites the entire member list and revokes GCP's internal control-plane permissions, breaking deployments.

- **Safe Pattern 1:** Use **Cloud Foundation Fabric (CFF)** modules (`github.com/GoogleCloudPlatform/cloud-foundation-fabric//modules/project`), which manage `iam_bindings_additive` safely alongside service identities.
- **Safe Pattern 2:** Use **resource-scoped** IAM bindings (`google_storage_bucket_iam_member`, `google_secret_manager_secret_iam_member`, `google_kms_crypto_key_iam_member`) rather than project-wide grants.

---

## 5. Zero Standing Keys: Workload Identity Federation & `versions.tf`

Authenticate external CI/CD (GitHub Actions shown) with short-lived OIDC tokens instead of exported service account keys. The `attribute_condition` pins trust to one repository:

```hcl
resource "google_iam_workload_identity_pool" "ci" {
  project                   = var.project_id
  workload_identity_pool_id = "${var.prefix}-ci-pool"
  display_name              = "CI/CD pool"
}

resource "google_iam_workload_identity_pool_provider" "github" {
  project                            = var.project_id
  workload_identity_pool_id          = google_iam_workload_identity_pool.ci.workload_identity_pool_id
  workload_identity_pool_provider_id = "github-oidc"
  attribute_mapping = {
    "google.subject"       = "assertion.sub"
    "attribute.repository" = "assertion.repository"
  }
  attribute_condition = "assertion.repository == \"${var.github_repo}\""
  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }
}

resource "google_service_account_iam_member" "ci_wif_user" {
  service_account_id = google_service_account.deployer.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.ci.name}/attribute.repository/${var.github_repo}"
}
```

Every module pins Terraform and provider versions in `versions.tf`:

```hcl
terraform {
  required_version = ">= 1.6.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 6.0" # Add an upper bound for the major version you tested (e.g. "< 7.0")
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = ">= 6.0" # Add an upper bound for the major version you tested (e.g. "< 7.0")
    }
  }
}
```
