---
name: image-gen
description: >-
  Generates high-craft technical diagrams, editorial hero banners, executive
  infographics, and square app icons from the CLI using Gemini Native Image
  Generation (gemini-nano-banana-2.1, gemini-3-pro-image,
  gemini-3.1-flash-lite-image, gemini-2.5-flash-image). Use when a document,
  README, codelab, or deck needs visual assets. Don't use when a deterministic
  Mermaid diagram in Markdown is more maintainable and editable than a raster
  image.
---

# Visual Asset & Architecture Diagram Generator (`image-gen`)

Wraps `<skill-dir>/scripts/image_gen.py` to generate consistent visual assets via either the **Gemini Developer API** (`GEMINI_API_KEY` / `GOOGLE_API_KEY` passed securely via the `x-goog-api-key` HTTP header) or **Vertex AI / Gemini Enterprise Agent Platform Application Default Credentials** (`GOOGLE_CLOUD_PROJECT` + `gcloud auth print-access-token`).

---

## 1. Art Direction Presets & Recommended Aspect Ratios

| Preset (`--style`) | Recommended `--ar` | Visual Aesthetic & Best Use Case |
| :--- | :---: | :--- |
| **`arch`** | `16:9` or `4:3` | Clean enterprise cloud architecture illustration, crisp geometric vector style, high-contrast slate and sky-blue palette |
| **`hero`** | `16:9` | Editorial technical hero banner for READMEs, portals, and executive decks; deep navy and cyan lighting |
| **`infographic`** | `16:9` or `3:4` | Structured executive technical infographic with flat vector iconography and clear visual hierarchy |
| **`icon`** | `1:1` | Square app/agent logo emblem with 10% empty margin around edges, high contrast, minimalist flat vector (warns on any other `--ar`) |
| **`none`** | any | No style prefix; sends `--prompt` verbatim (use when you supply complete art direction yourself) |

---

## 2. Validated Vertex AI / Agent Platform Models & Auth Modes

### Validated Model Matrix (`--model` or `GEMINI_IMAGE_MODEL`)

| Model ID | Status | Vertex AI Location | Endpoint & Modalities | Best Use Case & API Constraints |
| :--- | :---: | :---: | :--- | :--- |
| **`gemini-nano-banana-2.1`** *(default)* | **GA** (Oct 2026) | `global` | `:generateContent` (`TEXT`, `IMAGE`) | Balanced high-efficiency image generation & editing (up to 14 reference images, 1K/2K/4K). **Note:** Rejects `seed`, `temperature`, `topP`, `topK`, and `logprobs` (`image_gen.py` auto-omits `--seed` with a warning). |
| **`gemini-3-pro-image`** *(Nano Banana Pro)* | **GA** (May 2026) | `global` | `:generateContent` (`TEXT`, `IMAGE`) | Reasoning-driven model for complex layouts, executive infographics, and multi-concept compositions (supports `--seed` and up to 14 reference images). |
| **`gemini-3.1-flash-lite-image`** *(Nano Banana 2 Lite)* | **GA** | `global` | `:generateContent` (`IMAGE` only) | High-volume, low-latency 1K asset generation and rapid iteration (`image_gen.py` automatically sets `responseModalities: ["IMAGE"]`). |
| **`gemini-2.5-flash-image`** | **GA** | `global` & regional | `:generateContent` (`TEXT`, `IMAGE`) | Regional-endpoint fallback when customer data residency prohibits `location=global`. |
| **`imagen-3.0-*` / `imagen-4.0-*`** | **Discontinued** (Jun 30, 2026) | legacy regional | `:predict` | Standalone Vertex AI Imagen endpoints reached end-of-life on June 30, 2026. Retained in `image_gen.py` only for backward compatibility with a deprecation warning. |

### Reference Images (`--reference-image`)
- Accepts `.png`, `.jpg`/`.jpeg`, or `.webp` up to 7 MiB; other types, empty files, and missing paths fail fast before any API call.
- Gemini models receive the image as `inlineData`. Legacy `imagen-*` models send it as a `REFERENCE_TYPE_STYLE` reference and emit a deprecation warning.

### Authentication Modes
- **Mode A — Gemini API Key:** Set `export GEMINI_API_KEY="your-key"` (sent in the `x-goog-api-key` request header, never in URL query parameters).
- **Mode B — Vertex AI / Agent Platform ADC (On-Corp / Cloud Workstation):** Set `export GOOGLE_CLOUD_PROJECT="your-gcp-project"` and optional `export GOOGLE_CLOUD_LOCATION="global"` (defaults to `global`, routing to `https://aiplatform.googleapis.com/v1/projects/{project}/locations/global/...`; regional values such as `us-central1` route to `https://{location}-aiplatform.googleapis.com/...`). Uses `GOOGLE_OAUTH_ACCESS_TOKEN` or `gcloud auth print-access-token`.

---

## 3. CLI Usage & Style Consistency Controls

In the commands below, `<skill-dir>` is the directory containing this `SKILL.md` (e.g. `~/.gemini/config/skills/image-gen` on Google Antigravity, `~/.claude/skills/image-gen` on Claude Code, or `<project>/.gemini/skills/image-gen` / `<project>/.claude/skills/image-gen` when JIT-linked):

```bash
# 1. Preview the composed prompt and JSON payload without calling the API (--dry-run)
python3 <skill-dir>/scripts/image_gen.py \
  --style arch \
  --ar 16:9 \
  --negative-prompt "blurry text, 3d cartoon clutter, neon pink" \
  --prompt "Zero-trust VPC Service Controls perimeter protecting Vertex AI and BigQuery" \
  --output assets/vpc-sc-overview.png \
  --dry-run

# 2. Generate a 16:9 hero banner using the default gemini-nano-banana-2.1 model
python3 <skill-dir>/scripts/image_gen.py \
  --style hero \
  --ar 16:9 \
  --prompt "Autonomous multi-agent verification harness inspecting cloud infrastructure" \
  --output assets/hero-banner.png

# 3. Generate a 1:1 agent icon using gemini-3-pro-image with a seed and reference image
python3 <skill-dir>/scripts/image_gen.py \
  --model gemini-3-pro-image \
  --style icon \
  --ar 1:1 \
  --seed 42 \
  --reference-image assets/brand-palette.png \
  --prompt "Geometric shield and compass emblem representing sovereign cloud governance" \
  --output assets/agent-icon.png
```

---

## 4. Prompt Engineering Rules for Technical Visuals

1. **Minimize Dense Embedded Text:** Raster image models struggle with paragraphs of small labels. Use Mermaid (`flowchart`, `sequenceDiagram`) for exact box-and-arrow text labels, and use `image-gen` for conceptual architecture overviews, hero banners, and icons.
2. **Pin `--style` and `--reference-image` (Plus `--seed` Where Supported) Across a Document Suite:** When generating multiple illustrations for one customer readout or codelab, reuse the same `--style` and `--reference-image` (and `--seed` on `gemini-3-pro-image` or `gemini-2.5-flash-image`) so the color palette and stroke weights match.
3. **Read Safety Errors, Don't Retry Blindly:** A `blockReason`, `finishReason`, or `raiFilteredReason` error means the prompt was filtered; rephrase it rather than re-running the same command. `--dry-run` elides base64 image data so payload previews stay readable.
4. **Match `--output` Extension to the Returned Format:** The script sniffs PNG/JPEG/WebP magic bytes and warns when `--output` uses a different extension (e.g. the API returns PNG bytes when `--output` ends in `.jpg`).
5. **Keep Generated Binaries Out of Git Unless Intended:** Root `.gitignore` ignores loose `*.png` and `*.webp` files outside `skills/**/assets/`. Store project visuals in an explicit `assets/` or `docs/assets/` directory when they belong in version control.

## Common Rationalizations

| Rationalization | Reality |
| :--- | :--- |
| "I'll use `image-gen` for a 20-node sequence diagram with exact RPC method names" | Raster models garble dense method signatures and cannot be diffed in Git. Use a Mermaid `sequenceDiagram` instead. |
| "I'll pass the API key via `curl ...?key=$GEMINI_API_KEY`" | Putting API keys in URL query strings leaks credentials into shell history, proxy logs, and error traces. Use `image_gen.py` (`x-goog-api-key` header). |
| "I'll fire 5 live API calls before checking the prompt composition" | Always run `--dry-run` first to verify the composed style prefix, aspect ratio, and output path. |

## Red Flags

- Passing API keys in URL query strings (`?key=...`) instead of the `x-goog-api-key` header
- Mismatched aspect ratios (e.g., passing `--ar 16:9` when `--style icon` requires `1:1`)
- Replacing editable Mermaid architecture diagrams with un-editable raster PNGs for detailed technical specs
- Generating multiple images for the same deck without pinning `--style` and `--seed`

## Verification

- [ ] Ran `image_gen.py --dry-run` first to verify prompt, model, and aspect ratio alignment
- [ ] Output image exists at `--output` and is non-empty
- [ ] Markdown image reference (`![Alt text](assets/filename.png)`) uses descriptive accessibility alt text
