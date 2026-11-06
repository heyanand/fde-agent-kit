# AI Slop Lexicon & Before/After Transformations

Reference guide for the `unslop` skill. Use this lexicon to identify and eliminate AI-generated prose clichés, typography clutter, and defensive code bloat.

---

## 1. Banned AI Prose Openers, Transitions & Inflationary Verbs

| Category | Slop Phrases to Delete or Replace | Direct Engineering Replacement |
| :--- | :--- | :--- |
| **Throat-Clearing Openers** | *"In today's fast-paced digital landscape..."*, *"As organizations increasingly adopt..."*, *"It is worth noting that..."*, *"At its core..."* | Delete entirely. Start with the system, problem, or metric in sentence 1. |
| **Inflationary Verbs** | *delve into*, *spearhead*, *revolutionize*, *supercharge*, *unlock the full potential of*, *orchestrate a paradigm shift*, *harness the power of* | Use concrete verbs: *built*, *reduced*, *migrated*, *enforced*, *indexed*, *partitioned*, *deployed*. |
| **Promotional Adjectives** | *seamless*, *robust*, *cutting-edge*, *next-generation*, *world-class*, *battle-tested*, *game-changing*, *holistic*, *synergistic* | Replace with the specific mechanism or number that makes it reliable (e.g., *"idempotent retry with 30s backoff"*, *"99.95% availability"*). |
| **Filler Transitions** | *"Furthermore, it is crucial to remember..."*, *"Moreover, this underscores..."*, *"In conclusion, by leveraging..."* | Delete or use simple logical connectors (*Because*, *Therefore*, *However*). |
| **Hedging / Puffery Contrasts** | *"Not only does X do A, but it also effortlessly enables B..."*, *"This isn't just a tool — it's a transformation."* | State what X does and state the measured impact. |

---

## 2. Narrative & Resume Before/After Examples

### Example A: Resume / Impact Bullet
- **Before (Slop + Excessive Bolding + Backtick Clutter):**
  > **Spearheaded** a **groundbreaking**, **enterprise-grade** GenAI agent platform leveraging `Vertex AI`, `LangGraph`, and `BigQuery` to **revolutionize** customer support workflows, **seamlessly** orchestrating `MCP` tools and achieving **massive** latency reductions across **15+ global markets**.
- **After (Clean, Restrained Bolding, Zero Roboto Mono Backticks):**
  > **Multi-Agent Customer Triage Platform:** Architected a production Vertex AI and BigQuery agent pipeline across 15 European markets, cutting p95 ticket resolution latency by **62%** (from 14m to 5.3m) across **1.4M monthly requests**.

### Example B: Executive Architecture Readout Paragraph
- **Before (Slop + Backtick Clutter):**
  > In order to ensure a **robust** and **seamless** security posture, our `Cloud Run` microservices are deployed inside a **cutting-edge** `VPC Service Controls` perimeter with `CMEK` encryption via `Cloud KMS` and **strict** `Workload Identity Federation` bindings.
- **After (Clean Narrative Prose):**
  > All Cloud Run services operate inside an enforced VPC Service Controls perimeter with customer-managed encryption keys in Cloud KMS. External workloads authenticate through short-lived Workload Identity Federation tokens rather than static service account keys, eliminating cross-perimeter data exfiltration paths.

---

## 3. Code De-Slopping Before/After Examples

### Example C: Over-Defensive Hallucinated Fallbacks & Restated Comments
```python
# BEFORE (AI Code Slop):
def get_project_id(config: dict) -> str:
    """This function gets the project_id from the config dictionary."""
    # Check if config is not None and is a dict
    if config is not None and isinstance(config, dict):
        # Get the project_id key
        project_id = config.get("project_id", None)
        if project_id is not None and str(project_id).strip() != "":
            return str(project_id).strip()
    # Fallback to default project id if anything goes wrong
    try:
        return os.environ.get("PROJECT_ID", "default-placeholder-project")
    except Exception:
        return "default-placeholder-project"


# AFTER (Clean, Explicit Contract):
def get_project_id(config: dict[str, str]) -> str:
    project_id = config.get("project_id", "").strip()
    if not project_id:
        raise ValueError("Missing required 'project_id' in configuration.")
    return project_id
```
Why the After version is better:
1. Deletes comments that restate the code.
2. Removes silent fallback to `"default-placeholder-project"` (which masks broken config in production and causes confusing downstream IAM errors).
3. Fails fast with a clear `ValueError` at the boundary.
