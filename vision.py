"""
vision.py — GPT-4o Vision calls for Product Studio AI (Phase 2).
Image in → structured text/JSON out. Different modality from image_pipeline.py
which is image in → image out.
"""

import base64
import json

from openai import OpenAI

from prompts import (
    PLACEMENT_SUGGESTIONS_PROMPT,
    RECOGNIZE_PRODUCT_PROMPT,
    STYLE_REGISTERS,
)

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    """Lazy-init so .env loads before we read the key."""
    global _client
    if _client is None:
        _client = OpenAI()
    return _client


def recognize_product(image_bytes: bytes, model: str = "gpt-4o") -> dict:
    """
    Ask GPT-4o Vision to describe the product in the photo as JSON.

    Returns:
        On success: a dict with keys product_type, material, primary_color,
            key_features, current_photo_issues, uncertainties.
        On failure: {"error": "..."}
    """
    try:
        # The Vision API takes the image as a base64 data URL inside a message.
        b64 = base64.b64encode(image_bytes).decode("utf-8")
        data_url = f"data:image/png;base64,{b64}"

        response = _get_client().chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": RECOGNIZE_PRODUCT_PROMPT},
                        {"type": "image_url", "image_url": {"url": data_url}},
                    ],
                }
            ],
            response_format={"type": "json_object"},
        )

        text = response.choices[0].message.content or ""
        parsed = json.loads(text)
        return parsed
    except json.JSONDecodeError as e:
        return {"error": f"Model returned invalid JSON: {e}. Raw text: {text[:200]}"}
    except Exception as e:
        return {"error": f"{type(e).__name__}: {e}"}


def _format_product_context_text(ctx: dict) -> str:
    """Format the confirmed-context dict into a readable bullet list."""
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
        lines.append("- Distinguishing features:")
        for f in features:
            lines.append(f"    • {f}")
    return "\n".join(lines) if lines else "(no product context provided)"


def suggest_placements(
    product_context: dict,
    style_register: str = "Modern",
    model: str = "gpt-4o",
) -> dict:
    """
    Ask GPT-4o for 10 placement / styling concepts tailored to the product,
    in the chosen aesthetic register. Text-only call (no image needed) —
    context comes from the confirmed description from Stage 2.

    `style_register` is a key in prompts.STYLE_REGISTERS
    ("Understated" | "Modern" | "Luxe"); it overrides the model's
    category-default styling.

    Returns:
        On success: {"placements": [ {label, placement_type, description,
            mood_keywords, scene_prompt, color_palette, why_it_works}, ... ]}
        On failure: {"error": "..."}
    """
    text = ""
    try:
        register_text = STYLE_REGISTERS.get(style_register, STYLE_REGISTERS["Modern"])
        prompt = PLACEMENT_SUGGESTIONS_PROMPT.format(
            product_context=_format_product_context_text(product_context),
            style_register=register_text,
        )
        response = _get_client().chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )
        text = response.choices[0].message.content or ""
        parsed = json.loads(text)
        return parsed
    except json.JSONDecodeError as e:
        return {"error": f"Model returned invalid JSON: {e}. Raw text: {text[:200]}"}
    except Exception as e:
        return {"error": f"{type(e).__name__}: {e}"}
