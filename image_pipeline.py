"""
image_pipeline.py — All GPT-Image image calls for Product Studio AI (demo build).
app.py calls functions here; this module never imports from app.py.

DEMO BUILD: the image model and quality are fixed to the flagship
gpt-image-2 / medium for consistent, portfolio-grade output. There is no
model selector in this build (unlike the development repo).
"""

import io

from openai import OpenAI

from prompts import (
    PLACEMENT_GENERATE_PROMPT,
    STUDIO_ENHANCE_PROMPT,
    STUDIO_ENHANCE_WITH_CONTEXT_PROMPT,
)

# ── Fixed model settings for the demo build ───────────────────────────────────
IMAGE_MODEL = "gpt-image-2"
IMAGE_QUALITY = "medium"
IMAGE_SIZE = "1024x1024"

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    """Lazy-init the OpenAI client so .env has time to load before we read the key."""
    global _client
    if _client is None:
        _client = OpenAI()
    return _client


def enhance_image(
    image_bytes: bytes,
    model: str = IMAGE_MODEL,
    size: str = IMAGE_SIZE,
    quality: str = IMAGE_QUALITY,
    n: int = 1,
) -> dict:
    """
    Send a product image to GPT-Image-1 for studio-style enhancement.

    Returns:
        {"images": [b64_str, ...]} on success
        {"error": "..."}         on failure
    """
    try:
        # The SDK uses the file's .name attribute to infer the MIME type.
        # We wrap the raw bytes in a BytesIO and give it a .png name.
        file_like = io.BytesIO(image_bytes)
        file_like.name = "input.png"

        result = _get_client().images.edit(
            model=model,
            image=file_like,
            prompt=STUDIO_ENHANCE_PROMPT,
            size=size,
            quality=quality,
            n=n,
        )
        return {"images": [item.b64_json for item in result.data]}
    except Exception as e:
        return {"error": f"{type(e).__name__}: {e}"}


def _format_product_context(ctx: dict) -> str:
    """Turn the confirmed-context dict into a readable text block for the prompt."""
    lines = []
    if ctx.get("product_type"):
        lines.append(f"- Product: {ctx['product_type']}")
    if ctx.get("material"):
        lines.append(f"- Material: {ctx['material']}")
    if ctx.get("primary_color"):
        lines.append(f"- Primary colour: {ctx['primary_color']}")
    if ctx.get("approximate_dimensions"):
        lines.append(f"- Approximate real-world size: {ctx['approximate_dimensions']}")

    features = ctx.get("distinguishing_features") or []
    if features:
        lines.append("- Distinguishing features (must remain visible):")
        for f in features:
            lines.append(f"    • {f}")

    warnings = ctx.get("warnings_for_enhancement") or []
    if warnings:
        lines.append("- ⚠ Preservation warnings (do NOT alter these):")
        for w in warnings:
            lines.append(f"    • {w}")

    return "\n".join(lines) if lines else "(no additional context provided)"


def enhance_image_with_context(
    image_bytes: bytes,
    product_context: dict,
    user_adjustment: str = "",
    model: str = IMAGE_MODEL,
    size: str = IMAGE_SIZE,
    quality: str = IMAGE_QUALITY,
    n: int = 1,
) -> dict:
    """
    Context-informed enhancement (Phase 2 — Turn 2).

    `product_context` is the human-confirmed description from Stage 2.
    `user_adjustment` is optional free-text feedback like "make the background warmer".
    """
    try:
        context_block = _format_product_context(product_context)
        adjustment = user_adjustment.strip() or "(none)"

        prompt = STUDIO_ENHANCE_WITH_CONTEXT_PROMPT.format(
            product_context=context_block,
            user_adjustment=adjustment,
        )

        file_like = io.BytesIO(image_bytes)
        file_like.name = "input.png"

        result = _get_client().images.edit(
            model=model,
            image=file_like,
            prompt=prompt,
            size=size,
            quality=quality,
            n=n,
        )
        return {"images": [item.b64_json for item in result.data], "prompt": prompt}
    except Exception as e:
        return {"error": f"{type(e).__name__}: {e}"}


def generate_placement(
    image_bytes: bytes,
    scene_prompt: str,
    product_context: dict,
    model: str = IMAGE_MODEL,
    size: str = IMAGE_SIZE,
    quality: str = IMAGE_QUALITY,
    n: int = 1,
) -> dict:
    """
    Lifestyle placement (Phase 2 — Turn 3).
    Renders the product into a chosen scene while preserving the product itself.
    """
    try:
        context_block = _format_product_context(product_context)
        prompt = PLACEMENT_GENERATE_PROMPT.format(
            product_context=context_block,
            scene_prompt=scene_prompt,
        )

        file_like = io.BytesIO(image_bytes)
        file_like.name = "input.png"

        result = _get_client().images.edit(
            model=model,
            image=file_like,
            prompt=prompt,
            size=size,
            quality=quality,
            n=n,
        )
        return {"images": [item.b64_json for item in result.data], "prompt": prompt}
    except Exception as e:
        return {"error": f"{type(e).__name__}: {e}"}
