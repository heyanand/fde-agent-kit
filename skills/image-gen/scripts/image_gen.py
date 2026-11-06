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
"""CLI wrapper for Gemini Native Image Generation & Vertex AI Imagen asset generation."""

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
from pathlib import Path
import subprocess
import sys
from typing import Any
import urllib.error
import urllib.request


STYLE_PREFIXES = {
    "arch": (
        "Clean, modern enterprise cloud architecture illustration, crisp geometric vector style, "
        "high contrast slate and sky-blue palette, minimal text labels: "
    ),
    "hero": (
        "Editorial technical hero banner, modern abstract geometric composition, deep navy and "
        "cyan lighting, minimalist high-tech aesthetic: "
    ),
    "infographic": (
        "Structured executive technical infographic, flat vector iconography, clear visual hierarchy, "
        "clean background: "
    ),
    "icon": (
        "Square app icon logo, centered geometric emblem, 10% empty margin around edges, high contrast, "
        "minimalist flat vector: "
    ),
    "none": "",
}

DEFAULT_MODEL = "gemini-nano-banana-2.1"
DEFAULT_VERTEX_LOCATION = "global"
ASPECT_RATIOS = ("16:9", "4:3", "1:1", "3:4", "9:16")
SUPPORTED_REFERENCE_MIME_TYPES = ("image/png", "image/jpeg", "image/webp")
MAX_REFERENCE_BYTES = 7 * 1024 * 1024  # Conservative cap that keeps the inline JSON request small.
REQUEST_TIMEOUT_SECONDS = 120
MAGIC_SIGNATURES = (
    (b"\x89PNG\r\n\x1a\n", ".png"),
    (b"\xff\xd8\xff", ".jpg"),
    (b"RIFF", ".webp"),
)
EXTENSION_ALIASES = {".jpeg": ".jpg"}


def _warn(message: str) -> None:
    print(f"[WARN] {message}", file=sys.stderr)


def load_reference_image(reference_image: Path) -> tuple[str, str]:
    """Validate a reference image and return (mime_type, base64_data)."""
    if not reference_image.is_file():
        sys.exit(f"Error: Reference image not found: {reference_image}")
    mime_type, _ = mimetypes.guess_type(str(reference_image))
    if mime_type not in SUPPORTED_REFERENCE_MIME_TYPES:
        sys.exit(
            f"Error: Unsupported reference image type ({mime_type or 'unknown'}) for "
            f"{reference_image}. Use one of: .png, .jpg/.jpeg, .webp."
        )
    raw = reference_image.read_bytes()
    if not raw:
        sys.exit(f"Error: Reference image is empty: {reference_image}")
    if len(raw) > MAX_REFERENCE_BYTES:
        sys.exit(
            f"Error: Reference image is {len(raw) / 1_048_576:.1f} MiB; inline limit is "
            f"{MAX_REFERENCE_BYTES // 1_048_576} MiB. Downscale it first."
        )
    return mime_type, base64.b64encode(raw).decode("ascii")


def detect_image_extension(img_bytes: bytes) -> str | None:
    for signature, ext in MAGIC_SIGNATURES:
        if img_bytes.startswith(signature):
            if ext == ".webp" and img_bytes[8:12] != b"WEBP":
                continue
            return ext
    return None


def is_gemini_native_model(model: str) -> bool:
    """Return True for Gemini multimodal generateContent models, False for Imagen predict models."""
    return model.lower().startswith("gemini-")


def build_request_payload(
    model: str,
    prompt: str,
    aspect_ratio: str,
    seed: int | None = None,
    negative_prompt: str | None = None,
    reference_image: Path | None = None,
) -> dict[str, Any]:
    if is_gemini_native_model(model):
        full_text = f"{prompt}\nAspect ratio: {aspect_ratio}."
        if negative_prompt:
            full_text += f"\nAvoid: {negative_prompt}."
        parts: list[dict[str, Any]] = [{"text": full_text}]
        if reference_image is not None:
            mime_type, encoded_ref = load_reference_image(reference_image)
            parts.append({"inlineData": {"mimeType": mime_type, "data": encoded_ref}})
        lower_model = model.lower()
        modalities = ["IMAGE"] if "flash-lite-image" in lower_model else ["TEXT", "IMAGE"]
        gen_cfg: dict[str, Any] = {"responseModalities": modalities}
        if seed is not None:
            if "nano-banana" in lower_model:
                _warn(
                    f"{model} does not support the 'seed' parameter on Vertex AI / Agent Platform "
                    "(setting it returns HTTP 400); omitting 'seed' from generationConfig."
                )
            else:
                gen_cfg["seed"] = seed
        return {
            "contents": [{"role": "user", "parts": parts}],
            "generationConfig": gen_cfg,
        }

    # Legacy Imagen :predict payload (standalone Imagen 3.0 / 4.0 endpoints reached
    # their Vertex AI discontinuation date on June 30, 2026).
    _warn(
        f"{model} uses the legacy Imagen :predict endpoint, which was discontinued on Vertex AI "
        "on June 30, 2026. Consider migrating to gemini-nano-banana-2.1 or gemini-3-pro-image."
    )
    params: dict[str, Any] = {"sampleCount": 1, "aspectRatio": aspect_ratio}
    if seed is not None:
        params["seed"] = seed
        params["addWatermark"] = False
    if negative_prompt:
        params["negativePrompt"] = negative_prompt
    instance: dict[str, Any] = {"prompt": prompt}
    if reference_image is not None:
        _, encoded_ref = load_reference_image(reference_image)
        if "capability" not in model.lower():
            _warn(
                f"{model} may ignore reference images; Imagen style customization requires a "
                "capability model (e.g. imagen-3.0-capability-001) or a gemini-* image model."
            )
        instance["referenceImages"] = [
            {
                "referenceType": "REFERENCE_TYPE_STYLE",
                "referenceId": 1,
                "referenceImage": {"bytesBase64Encoded": encoded_ref},
            }
        ]
    return {"instances": [instance], "parameters": params}


def build_endpoint_and_headers(
    model: str,
    api_key: str | None = None,
    project: str | None = None,
    location: str = DEFAULT_VERTEX_LOCATION,
    access_token: str | None = None,
) -> tuple[str, dict[str, str]]:
    method = "generateContent" if is_gemini_native_model(model) else "predict"
    if api_key:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:{method}"
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": api_key,
        }
        return url, headers

    if project:
        token = access_token or os.environ.get("GOOGLE_OAUTH_ACCESS_TOKEN")
        if not token:
            try:
                proc = subprocess.run(
                    ["gcloud", "auth", "print-access-token"],
                    capture_output=True,
                    text=True,
                    check=True,
                    timeout=15,
                )
                token = proc.stdout.strip()
            except FileNotFoundError:
                sys.exit(
                    "Error: `gcloud` CLI not found on PATH. Install the Google Cloud SDK, set "
                    "GOOGLE_OAUTH_ACCESS_TOKEN, or set GEMINI_API_KEY instead."
                )
            except subprocess.CalledProcessError as exc:
                detail = (exc.stderr or "").strip().splitlines()[-1:] or [str(exc)]
                sys.exit(
                    f"Error: `gcloud auth print-access-token` failed ({detail[0]}). "
                    "Run `gcloud auth login` or set GEMINI_API_KEY."
                )
            except subprocess.SubprocessError as exc:
                sys.exit(f"Error: Failed to obtain Vertex AI access token via gcloud ({exc}).")
            if not token:
                sys.exit("Error: gcloud returned an empty access token. Run `gcloud auth login`.")
        host = (
            "aiplatform.googleapis.com"
            if location == "global"
            else f"{location}-aiplatform.googleapis.com"
        )
        url = (
            f"https://{host}/v1/projects/{project}"
            f"/locations/{location}/publishers/google/models/{model}:{method}"
        )
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        }
        return url, headers

    sys.exit(
        "Error: Set GEMINI_API_KEY (or GOOGLE_API_KEY) for Gemini Developer API, "
        "or set GOOGLE_CLOUD_PROJECT for Vertex AI ADC, or pass --dry-run."
    )


def _truncate(value: Any, limit: int = 400) -> str:
    text = json.dumps(value) if not isinstance(value, str) else value
    return text if len(text) <= limit else text[:limit] + "...(truncated)"


def extract_image_bytes(model: str, data: dict[str, Any]) -> bytes:
    if is_gemini_native_model(model):
        text_parts: list[str] = []
        finish_reasons: list[str] = []
        for candidate in data.get("candidates", []):
            if candidate.get("finishReason"):
                finish_reasons.append(str(candidate["finishReason"]))
            parts = (candidate.get("content") or {}).get("parts", [])
            for part in parts:
                inline = part.get("inlineData") or part.get("inline_data")
                if inline and "data" in inline:
                    return base64.b64decode(inline["data"])
                if part.get("text"):
                    text_parts.append(str(part["text"]))
        block_reason = (data.get("promptFeedback") or {}).get("blockReason")
        if block_reason:
            sys.exit(
                f"Error: Prompt blocked by safety filters (blockReason={block_reason}). "
                "Rephrase the prompt."
            )
        details = []
        if finish_reasons:
            details.append(f"finishReason={','.join(finish_reasons)}")
        if text_parts:
            details.append(f"model text: {_truncate(' '.join(text_parts), 300)}")
        sys.exit(
            "Error: No inline image returned in generateContent response"
            + (f" ({'; '.join(details)})" if details else f": {_truncate(data)}")
            + ". Check that the model supports image output."
        )

    predictions = data.get("predictions", [])
    if not predictions:
        sys.exit(
            "Error: Imagen returned no predictions (likely filtered by Responsible AI safety "
            f"settings). Rephrase the prompt. Response: {_truncate(data)}"
        )
    first = predictions[0]
    if "bytesBase64Encoded" not in first:
        reason = first.get("raiFilteredReason")
        if reason:
            sys.exit(f"Error: Imagen output filtered by safety settings: {reason}")
        sys.exit(f"Error: Unexpected Imagen predict payload: {_truncate(data)}")
    return base64.b64decode(first["bytesBase64Encoded"])


def execute_generation(
    model: str,
    url: str,
    headers: dict[str, str],
    payload: dict[str, Any],
    output_path: Path,
) -> None:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT_SECONDS) as resp:
            response_data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        err_body = ""
        try:
            err_body = exc.read().decode("utf-8", errors="replace")[:400]
        except Exception:
            pass
        sys.exit(f"Error: Image API returned HTTP {exc.code} ({exc.reason}): {err_body}")
    except urllib.error.URLError as exc:
        sys.exit(f"Error: Network failure reaching image endpoint: {exc.reason}")
    except TimeoutError:
        sys.exit(f"Error: Image API did not respond within {REQUEST_TIMEOUT_SECONDS}s. Retry later.")
    except json.JSONDecodeError as exc:
        sys.exit(f"Error: Image API returned a non-JSON response ({exc}).")

    img_bytes = extract_image_bytes(model, response_data)
    if not img_bytes:
        sys.exit("Error: Image API returned an empty image payload.")
    detected = detect_image_extension(img_bytes)
    requested = EXTENSION_ALIASES.get(output_path.suffix.lower(), output_path.suffix.lower())
    if detected and requested != detected:
        _warn(
            f"API returned {detected} bytes but --output ends in '{output_path.suffix or '(none)'}'; "
            f"consider renaming to {output_path.with_suffix(detected).name}."
        )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(img_bytes)
    print(f"[OK] Saved generated image ({len(img_bytes)} bytes) -> {output_path}")


def redact_inline_data(payload: dict[str, Any]) -> str:
    """Serialize a payload for --dry-run with base64 image blobs elided."""

    def _scrub(node: Any) -> Any:
        if isinstance(node, dict):
            scrubbed: dict[str, Any] = {}
            for key, value in node.items():
                is_blob = key in ("data", "bytesBase64Encoded") and isinstance(value, str)
                scrubbed[key] = f"<{len(value)} base64 chars>" if is_blob else _scrub(value)
            return scrubbed
        if isinstance(node, list):
            return [_scrub(item) for item in node]
        return node

    return json.dumps(_scrub(payload))


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Generate visual assets via Gemini / Imagen.",
        epilog=(
            "Auth: GEMINI_API_KEY / GOOGLE_API_KEY (Gemini Developer API) or "
            "GOOGLE_CLOUD_PROJECT (+ GOOGLE_CLOUD_LOCATION) for Vertex AI.\n"
            "Example:\n  %(prog)s --style hero --ar 16:9 --seed 7 "
            "--prompt \"Agent mesh over cloud\" --output assets/hero.png --dry-run"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--prompt", required=True, help="Visual description prompt.")
    parser.add_argument(
        "--style",
        choices=sorted(STYLE_PREFIXES.keys()),
        default="arch",
        help="Art direction preset ('none' sends the prompt verbatim).",
    )
    parser.add_argument(
        "--ar",
        choices=list(ASPECT_RATIOS),
        default="16:9",
        help="Aspect ratio.",
    )
    parser.add_argument(
        "--model",
        default=os.environ.get("GEMINI_IMAGE_MODEL", DEFAULT_MODEL),
        help=(
            "Model ID (default: gemini-nano-banana-2.1; also supports gemini-3-pro-image, "
            "gemini-3.1-flash-lite-image, gemini-2.5-flash-image, or legacy imagen-*)."
        ),
    )
    parser.add_argument("--seed", type=int, default=None, help="Optional integer seed for reproducibility.")
    parser.add_argument(
        "--negative-prompt",
        type=str,
        default=None,
        help="Optional negative prompt describing elements to exclude.",
    )
    parser.add_argument(
        "--reference-image",
        type=Path,
        default=None,
        help="Optional reference image path for style/composition conditioning.",
    )
    parser.add_argument("--output", type=Path, required=True, help="Output image file path.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the composed prompt and request payload without calling the API.",
    )
    args = parser.parse_args(argv)

    prompt = " ".join(args.prompt.split())
    if not prompt:
        parser.error("--prompt must not be empty.")
    if args.output.is_dir():
        parser.error(f"--output must be a file path, not a directory: {args.output}")
    if not args.model.strip():
        parser.error("--model must not be empty.")
    if args.style == "icon" and args.ar != "1:1":
        _warn(f"--style icon is designed for --ar 1:1 (got {args.ar}).")

    full_prompt = STYLE_PREFIXES[args.style] + prompt
    payload = build_request_payload(
        model=args.model,
        prompt=full_prompt,
        aspect_ratio=args.ar,
        seed=args.seed,
        negative_prompt=args.negative_prompt,
        reference_image=args.reference_image,
    )

    if args.dry_run:
        print(f"[DRY-RUN] Model        : {args.model}")
        print(f"[DRY-RUN] Aspect Ratio : {args.ar}")
        print(f"[DRY-RUN] Output Path  : {args.output}")
        print(f"[DRY-RUN] Full Prompt  : {full_prompt}")
        method = "generateContent" if is_gemini_native_model(args.model) else "predict"
        print(f"[DRY-RUN] Endpoint     : :{method}")
        print(f"[DRY-RUN] Payload JSON : {redact_inline_data(payload)}")
        return

    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    project = os.environ.get("GOOGLE_CLOUD_PROJECT") or os.environ.get("CLOUD_ML_PROJECT_ID")
    location = os.environ.get("GOOGLE_CLOUD_LOCATION", DEFAULT_VERTEX_LOCATION)
    url, headers = build_endpoint_and_headers(
        model=args.model,
        api_key=api_key,
        project=project,
        location=location,
    )
    execute_generation(args.model, url, headers, payload, args.output)


if __name__ == "__main__":
    main()
