---
name: unslop
description: >-
  Audits and strips AI-generated slop from technical prose, resumes,
  architecture documents, and source code. Enforces restrained bolding, removes
  inline Roboto Mono backtick clutter in narrative documents, preserves all
  load-bearing engineering facts/qualifiers, and eliminates redundant code
  abstractions. Use when polishing any user-facing document, resume, ADR, or
  AI-authored code diff. Don't use when raw unedited transcripts, quotes, or
  legal text must be preserved verbatim, or for judging code correctness (use
  code-review-and-quality).
---

# Prose & Code De-Slopper (`unslop`)

See [references/slop-lexicon-and-examples.md](references/slop-lexicon-and-examples.md) for the complete banned phrase lexicon and concrete Before/After transformations.

## Workflow

1. **Classify the target:** narrative (resume, readout, proposal, customer email) or technical (README, spec, ADR, code). The class decides the typography rules in 1.1 and the `--profile` in Section 3.
2. **Inventory facts** (Section 1.3) before touching a word.
3. **Purge and tighten** (Sections 1.2 and 2).
4. **Re-check the inventory** against the edited text: every metric, unit, and caveat still present with the same meaning.
5. **Run the verification gate** (Section 3) and fix every finding.

---

## 1. Narrative & Document De-Slopping Rules

When authoring or cleaning resumes, executive readouts, PRDs, architecture narratives, or customer proposals:

### 1.1 Typography & Formatting Restraint (Google Docs Safe)
- **Restrained Bolding:** Restrict bold formatting (`**...**`) strictly to **bullet lead-in titles** and **primary headline numbers** (e.g., **62%**, **\$2.4M**, **1.4M QPS**). Never bold full sentences or scatter 4+ bold spans across a paragraph.
- **Zero Inline Monospace Clutter in Narrative Prose:** Do NOT wrap product names, cloud services, protocols, or common technical nouns in Markdown backticks (`` `Vertex AI` ``, `` `Cloud Run` ``, `` `VPC-SC` ``, `` `gRPC` ``) inside narrative paragraphs or resume bullets. In Google Docs imports, backticks render in jarring `Roboto Mono` font. Reserve backticks and fenced code blocks strictly for technical CLI reference guides, file paths in developer docs, and actual code listings.
- **Clean Punctuation:** Never place Unicode em-dashes (`—`) or en-dashes (`–`) inside fenced code blocks or CLI commands where they corrupt copy-pasted flags (`--flag`).

### 1.2 Lexical Purge
- Delete throat-clearing intros (*"In today's rapidly evolving landscape..."*, *"It is worth noting that..."*).
- Replace inflationary verbs (*spearheaded*, *delved*, *revolutionized*, *supercharged*, *unlocked*) with concrete engineering actions (*architected*, *migrated*, *reduced*, *partitioned*, *enforced*).
- Replace vague adjectives (*seamless*, *robust*, *cutting-edge*, *holistic*) with the specific mechanism or metric that proves reliability.

### 1.3 Fact & Qualifier Preservation (Non-Negotiable)
Clearer wording must **never** alter technical reality:
1. Before editing, inventory every metric, unit, SLA, constraint, version number, and caveat in the source text.
2. Never delete a load-bearing qualifier (*"tested up to 5k QPS"*, *"requires regional KMS key in the same continent"*) just to make a sentence punchier.
3. Never invent metrics or stronger guarantees unsupported by the source.
4. If a sentence is vague *and* carries no fact (for example, *"Our robust solution delivers value"*), ask the author for the missing metric or delete the sentence; do not fabricate a number to fill the gap.

Mini-example of a fact-preserving edit:
- **Before:** *"Our cutting-edge pipeline seamlessly handles massive scale, tested up to 5k QPS in us-central1."*
- **After:** *"The pipeline sustains 5k QPS in load tests (us-central1 only)."* The tested ceiling and the region caveat survive; the adjectives do not.

### 1.4 Edge Cases
- **Quoted material, legal text, or customer-provided requirements:** Leave verbatim; de-slop only the surrounding prose.
- **Technical docs that must name commands, flags, or file paths:** Backticks stay; the narrative backtick ban applies to resumes, readouts, and proposals only.
- **Brand or product names that look like jargon** (for example, *"Workload Identity Federation"*): Keep the official name; cut only the adjectives around it.

---

## 2. Source Code De-Slopping Rules

When cleaning AI-generated code diffs:
1. **Delete Restated Comments:** Remove comments that narrate *what* the next line visibly does (`# Set x to 1`). Keep only comments that explain *why* (invariants, non-obvious platform gotchas, ADR references).
2. **Eliminate Silent Hallucinated Fallbacks:** Strip defensive `try / except Exception: return "default"` wrappers that swallow real configuration or runtime errors. Fail fast with explicit exceptions at system boundaries.
3. **Remove Single-Use Pass-Through Wrappers:** Collapse helper functions, classes, or interfaces that only forward arguments to another function without narrowing the contract.
4. **Purge Dead Artifacts:** Remove unused imports, commented-out code blocks, `_unused` variables, and unrequested backwards-compatibility shims.

---

## 3. Mandatory Verification Gate

After de-slopping any Markdown file, run the static verifier from the sibling `verify` skill. `<skill-dir>` is the directory containing this `SKILL.md`; `verify` is always linked next to it because both are Global Core skills:
```bash
# For resumes, executive readouts, and narrative documents:
python3 <skill-dir>/../verify/scripts/verify_static.py --mode prose --profile narrative <file.md>

# For technical READMEs, specs, and ADRs:
python3 <skill-dir>/../verify/scripts/verify_static.py --mode prose --profile technical <file.md>
```
The verifier checks typography and fences only. It cannot detect a dropped caveat, so step 4 of the Workflow (fact re-check) remains mandatory.

## Common Rationalizations

| Rationalization | Reality |
| :--- | :--- |
| "Bolding every technical keyword helps the recruiter or exec skim" | When everything is bolded, nothing stands out. Restrict bolding to lead-in titles and primary headline numbers. |
| "Wrapping service names in backticks looks technical in Markdown" | When imported into Google Docs or slides, inline backticks render as ugly `Roboto Mono` spans inside proportional text. |
| "Removing the caveat makes the executive summary read cleaner" | Dropping a technical caveat falsifies the engineering claim. Keep the constraint; tighten the phrasing. |
| "The extra `try/except` fallback makes the code safer" | Swallowing unexpected exceptions and returning a dummy value hides bugs until data is corrupted downstream. |

## Red Flags

- Narrative lines containing `>3` bold spans (`[PROSE_BOLD_OVERUSE]`) or `>3` inline backtick spans (`[PROSE_BACKTICK_CLUTTER]`)
- Words like *delve*, *spearhead*, *seamless*, *game-changing*, *tapestry*, or *testament* in final prose (`verify_static.py --mode prose` reports the high-confidence subset as `[PROSE_SLOP_TERM]`; *tapestry* and *testament* still need a manual pass)
- Dropping units, latency percentiles (`p95` vs `mean`), or security prerequisites during an edit
- Leaving `// rest of implementation remains the same` or `# TODO` placeholders in code

## Verification

- [ ] Target file passes `verify_static.py --mode prose` (`--profile narrative` or `--profile technical`) with 0 findings
- [ ] All source metrics, units, and caveats are preserved intact
- [ ] Zero restated comments, silent dummy fallbacks, or dead code blocks remain in source files
