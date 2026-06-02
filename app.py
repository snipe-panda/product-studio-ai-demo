"""
app.py — Streamlit UI for Product Studio AI.
All OpenAI calls go through image_pipeline.py and vision.py — never called
directly here.

Phase 2 introduces a multi-stage conversational flow:
    upload → recognize → enhance
The current stage lives in st.session_state["stage"] so it survives Streamlit's
top-to-bottom rerun on every interaction.
"""

import base64
import random
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from image_pipeline import (
    enhance_image,
    enhance_image_with_context,
    generate_placement,
)
from styles import inject_css
from utils import b64_to_pil, pil_to_bytes, resize_image
from vision import recognize_product, suggest_placements

load_dotenv()


# ── Witty processing messages (one picked at random per run) ──────────────────
SPIN_IDENTIFY = [
    "Squinting at the details…",
    "Getting to know your product…",
    "Reading the fine print, logos and all…",
    "Sizing it up…",
]
SPIN_ENHANCE = [
    "Rolling out the seamless backdrop…",
    "Adjusting the studio lights…",
    "Making it look expensive…",
    "Booking the (virtual) photographer…",
    "Straighten, light, polish, repeat…",
]
SPIN_SUGGEST = [
    "Moodboarding {reg} scenes…",
    "Scouting {reg} locations…",
    "Auditioning props…",
    "Dreaming up {reg} setups…",
]
SPIN_PLACE = [
    "Dressing the set…",
    "Styling the scene…",
    "Arranging the props just so…",
    "Rolling cameras…",
]


def spin(pool: list[str], **fmt) -> str:
    """Pick a random witty line, formatting any {placeholders}."""
    return random.choice(pool).format(**fmt)


# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Kira — Product Studio",
    page_icon="◆",
    layout="wide",
)
inject_css()


# ── Session state initialisation ──────────────────────────────────────────────
# NOTE on persistence: st.session_state survives Streamlit reruns (button clicks,
# slider changes) but is wiped on a full browser refresh. We mirror the current
# `stage` into the URL query string (?stage=...) so a refresh at least restores
# the stage — though the image bytes and AI results are still lost. True
# cross-refresh persistence would require localStorage or server-side storage
# (tracked as a future enhancement).
STAGES = ["upload", "recognize", "enhance", "place"]

if "stage" not in st.session_state:
    # Try to recover the stage from the URL on first load
    param_stage = st.query_params.get("stage")
    if param_stage in STAGES:
        st.session_state["stage"] = param_stage
    else:
        st.session_state["stage"] = "upload"
        st.query_params["stage"] = "upload"


def goto(stage: str) -> None:
    """Move the state machine to a given stage and rerun."""
    st.session_state["stage"] = stage
    st.query_params["stage"] = stage
    st.rerun()


def snapshot_gen_params(model: str, quality: str, size: str, n: int) -> None:
    """
    Freeze the current sidebar values into session state so an in-flight
    generation isn't disturbed if the user fiddles with the sidebar. The
    auto-run blocks read from this snapshot, not the live widgets.
    """
    st.session_state["gen_params"] = {
        "model": model,
        "quality": quality,
        "size": size,
        "n": n,
    }


def clear_generation(*keys: str) -> None:
    """Clear a result key + the params snapshot so the next run re-snapshots."""
    for k in keys:
        st.session_state.pop(k, None)
    st.session_state.pop("gen_params", None)


def reset_all() -> None:
    """Clear everything and return to the upload stage."""
    for key in [
        "stage",
        "image_bytes",
        "source_name",
        "recognition",
        "product_context",
        "result",
        "adjustment",
        "placements",
        "selected_placement_idx",
        "placement_result",
        "style_register",
        "gen_params",
    ]:
        st.session_state.pop(key, None)
    st.session_state["stage"] = "upload"
    st.query_params["stage"] = "upload"
    st.rerun()


# ── Header ────────────────────────────────────────────────────────────────────
head_l, head_r = st.columns([4, 1])
with head_l:
    st.markdown(
        '<div class="kira-brand"><span class="mark">◆</span>'
        '<span class="name">Kira</span></div>',
        unsafe_allow_html=True,
    )
with head_r:
    st.write("")
    if st.button("Start over", use_container_width=True):
        reset_all()


# ── Stepper ───────────────────────────────────────────────────────────────────
STEP_LABELS = {
    "upload": "Upload",
    "recognize": "Identify",
    "enhance": "Enhance",
    "place": "Place",
}


def render_stepper() -> None:
    cur_i = STAGES.index(st.session_state["stage"])
    parts = ['<div class="kira-stepper">']
    for i, s in enumerate(STAGES):
        cls = "active" if i == cur_i else ("done" if i < cur_i else "")
        parts.append(
            f'<div class="kira-step {cls}"><span class="num">{i + 1}</span>'
            f'<span class="lbl">{STEP_LABELS[s]}</span></div>'
        )
        if i < len(STAGES) - 1:
            parts.append('<span class="kira-step-sep"></span>')
    parts.append("</div>")
    st.markdown("".join(parts), unsafe_allow_html=True)


render_stepper()


# ── Fixed generation settings (demo build — no selectors) ─────────────────────
# This build is locked to the flagship model + medium quality for consistent,
# demo-grade output. The development repo keeps the sidebar selectors instead.
model = "gpt-image-2"
quality = "medium"
size = "1024x1024"
n_variations = 1


# ═══════════════════════════════════════════════════════════════════════════════
# STAGE 1 — UPLOAD
# ═══════════════════════════════════════════════════════════════════════════════
if st.session_state["stage"] == "upload":
    hero_l, hero_r = st.columns([1, 1], gap="large")
    with hero_l:
        st.markdown(
            '<div class="kira-eyebrow">AI Product Photography · Under 60 Seconds</div>'
            '<div class="kira-hero">One phone photo in.<br>'
            '<em>Studio listing</em> out.</div>'
            '<div class="kira-sub">Drop a crooked, badly-lit shot from your phone. '
            'Kira straightens it, cuts the background, adds studio lighting, then '
            'suggests lifestyle scenes — listing-ready in seconds.</div>'
            '<div class="kira-chips">'
            '<span class="kira-chip"><span class="ic">⚡</span> No studio booking</span>'
            '<span class="kira-chip"><span class="ic">✓</span> Amazon-compliant white BG</span>'
            '<span class="kira-chip"><span class="ic">✦</span> Ready in seconds</span>'
            '</div>',
            unsafe_allow_html=True,
        )
    with hero_r:
        uploaded_file = st.file_uploader(
            "Drop a product photo",
            type=["jpg", "jpeg", "png"],
            label_visibility="collapsed",
        )
        st.caption("No photo handy? Drop any image to see the pipeline run.")

    if uploaded_file is not None:
        # Resize once and store bytes in session state so later stages have it
        resized = resize_image(uploaded_file)
        st.session_state["image_bytes"] = pil_to_bytes(resized, format="PNG")
        st.session_state["source_name"] = uploaded_file.name

        st.divider()
        prev_l, prev_r = st.columns([1, 1], gap="large")
        with prev_l:
            st.image(resized, caption=uploaded_file.name, use_container_width=True)
        with prev_r:
            st.markdown('<div class="kira-eyebrow">Ready</div>', unsafe_allow_html=True)
            st.markdown(f"**{uploaded_file.name}** · {uploaded_file.size / 1024:.0f} KB")
            st.write("")
            if st.button("Continue to Identify  →", type="primary", use_container_width=True):
                st.session_state.pop("recognition", None)
                goto("recognize")


# ═══════════════════════════════════════════════════════════════════════════════
# STAGE 2 — RECOGNIZE
# ═══════════════════════════════════════════════════════════════════════════════
elif st.session_state["stage"] == "recognize":
    st.markdown('<div class="kira-eyebrow">Step 2 · Identify</div>', unsafe_allow_html=True)
    st.markdown('<div class="kira-stage-title">Review the product details</div>', unsafe_allow_html=True)

    if "image_bytes" not in st.session_state:
        st.error("No image found — please go back and upload first.")
        if st.button("← Back to upload"):
            goto("upload")
        st.stop()

    # Auto-run recognition once on entry
    if "recognition" not in st.session_state:
        with st.spinner(spin(SPIN_IDENTIFY)):
            st.session_state["recognition"] = recognize_product(st.session_state["image_bytes"])

    rec = st.session_state["recognition"]
    if "error" in rec:
        st.error(f"Recognition failed: {rec['error']}")
        col_back, col_retry = st.columns(2)
        with col_back:
            if st.button("← Back to upload", use_container_width=True):
                goto("upload")
        with col_retry:
            if st.button("↻ Retry recognition", use_container_width=True):
                st.session_state.pop("recognition", None)
                st.rerun()
        st.stop()

    # ── Layout: image on the left, editable fields on the right ─────────────
    col_img, col_form = st.columns([1, 2])
    with col_img:
        st.image(st.session_state["image_bytes"], caption="Your photo", use_container_width=True)
        confidence = rec.get("meta", {}).get("confidence_score", 0.0)
        st.metric("AI confidence", f"{confidence:.0%}")

    with col_form:
        st.caption("Correct anything the AI got wrong. These details will guide the enhancement.")

        identity = rec.get("identity", {})
        form = rec.get("form", {})
        surface = rec.get("surface", {})
        detail = rec.get("detail", {})
        meta = rec.get("meta", {})

        product_type = st.text_input("Product type", value=identity.get("product_type", ""))
        material = st.text_input("Material", value=surface.get("material_likely", ""))
        primary_color = st.text_input("Primary colour", value=surface.get("primary_color", ""))
        approximate_dimensions = st.text_input(
            "Approximate size",
            value=form.get("approximate_dimensions", ""),
            help="Real-world size, e.g. 'small, ~28cm tall × 8cm wide'. Used to keep companion objects at believable scale.",
        )

        distinguishing = detail.get("distinguishing_features", [])
        distinguishing_text = st.text_area(
            "Key features (one per line)",
            value="\n".join(distinguishing),
            height=120,
        )

        warnings = meta.get("warnings_for_enhancement", [])
        warnings_text = st.text_area(
            "⚠️ Preservation warnings (do-not-alter list, one per line)",
            value="\n".join(warnings),
            height=80,
            help="Anything the enhancement model must be careful to preserve exactly.",
        )

    with st.expander("📋 See the full AI description (read-only)"):
        st.json(rec)

    # ── Navigation ───────────────────────────────────────────────────────────
    st.divider()
    col_back, col_redo, col_fwd = st.columns([1, 1, 2])
    with col_back:
        if st.button("← Back", use_container_width=True):
            goto("upload")
    with col_redo:
        if st.button("↻ Redo AI", use_container_width=True, help="Re-run GPT-4o on the same image"):
            st.session_state.pop("recognition", None)
            st.rerun()
    with col_fwd:
        if st.button("Continue to Enhance →", type="primary", use_container_width=True):
            # Persist the user's confirmed/corrected context
            st.session_state["product_context"] = {
                "product_type": product_type,
                "material": material,
                "primary_color": primary_color,
                "approximate_dimensions": approximate_dimensions,
                "distinguishing_features": [
                    line.strip() for line in distinguishing_text.splitlines() if line.strip()
                ],
                "warnings_for_enhancement": [
                    line.strip() for line in warnings_text.splitlines() if line.strip()
                ],
            }
            # Force a fresh enhancement on entry to the next stage
            clear_generation("result")
            snapshot_gen_params(model, quality, size, n_variations)
            goto("enhance")


# ═══════════════════════════════════════════════════════════════════════════════
# STAGE 3 — ENHANCE
# ═══════════════════════════════════════════════════════════════════════════════
elif st.session_state["stage"] == "enhance":
    st.markdown('<div class="kira-eyebrow">Step 3 · Enhance</div>', unsafe_allow_html=True)
    st.markdown('<div class="kira-stage-title">Studio enhancement</div>', unsafe_allow_html=True)

    if "image_bytes" not in st.session_state:
        st.error("No image found — please go back and upload first.")
        if st.button("← Back to upload"):
            goto("upload")
        st.stop()

    ctx = st.session_state.get("product_context", {})
    if ctx:
        with st.expander("Confirmed product context being used"):
            st.json(ctx)

    # Get the current adjustment (may be empty)
    adjustment = st.session_state.get("adjustment", "")

    # Run enhancement once on entry (or when re-triggered).
    # Read params from the snapshot — NOT the live sidebar — so sidebar
    # changes mid-generation don't restart the call with new params.
    if "result" not in st.session_state:
        if "gen_params" not in st.session_state:
            snapshot_gen_params(model, quality, size, n_variations)
        gp = st.session_state["gen_params"]
        with st.spinner(spin(SPIN_ENHANCE)):
            st.session_state["result"] = enhance_image_with_context(
                image_bytes=st.session_state["image_bytes"],
                product_context=ctx,
                user_adjustment=adjustment,
                model=gp["model"],
                size=gp["size"],
                quality=gp["quality"],
                n=gp["n"],
            )

    result = st.session_state["result"]
    if "error" in result:
        st.error(f"Enhancement failed: {result['error']}")
        col_back, col_retry = st.columns(2)
        with col_back:
            if st.button("← Back to recognition", use_container_width=True):
                goto("recognize")
        with col_retry:
            if st.button("↻ Retry enhancement", use_container_width=True):
                clear_generation("result")
                st.rerun()
        st.stop()

    # ── Before / after display ───────────────────────────────────────────────
    source_stem = Path(st.session_state.get("source_name", "image")).stem
    images = result["images"]

    st.markdown(
        '<div class="kira-eyebrow">Studio render · 1024×1024</div>',
        unsafe_allow_html=True,
    )

    col_before, col_after = st.columns(2)
    with col_before:
        st.markdown('<div class="kira-eyebrow">Before</div>', unsafe_allow_html=True)
        st.image(st.session_state["image_bytes"], use_container_width=True)
    with col_after:
        st.markdown('<div class="kira-eyebrow">After</div>', unsafe_allow_html=True)
        first_img = b64_to_pil(images[0])
        st.image(first_img, use_container_width=True)
        st.download_button(
            label="↓ Download",
            data=base64.b64decode(images[0]),
            file_name=f"studio_{source_stem}.png",
            mime="image/png",
            use_container_width=True,
            key="dl_0",
        )

    if len(images) > 1:
        st.divider()
        st.markdown(
            f'<div class="kira-eyebrow">Variations · {len(images) - 1}</div>',
            unsafe_allow_html=True,
        )
        cols = st.columns(min(len(images) - 1, 3))
        for i, b64 in enumerate(images[1:], start=1):
            with cols[(i - 1) % len(cols)]:
                st.image(b64_to_pil(b64), use_container_width=True)
                st.download_button(
                    label=f"↓ Variation {i + 1}",
                    data=base64.b64decode(b64),
                    file_name=f"studio_{source_stem}_v{i + 1}.png",
                    mime="image/png",
                    use_container_width=True,
                    key=f"dl_{i}",
                )

    # ── Refine (iterative feedback) ──────────────────────────────────────────
    st.divider()
    st.markdown('<div class="kira-eyebrow">Refine</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="kira-stage-title" style="font-size:1.4rem;">Adjust the result</div>',
        unsafe_allow_html=True,
    )
    st.caption(
        "Type a small change and re-run. Your confirmed product details stay "
        "intact — only the tweak is layered on top."
    )
    new_adjustment = st.text_area(
        "Adjustment",
        value=adjustment,
        placeholder='e.g. "use a soft warm grey background", "show a slight three-quarter angle", "soften the shadow"',
        height=80,
        label_visibility="collapsed",
    )
    if adjustment:
        st.markdown(
            f'<div class="kira-note">Last refinement: <b>{adjustment}</b></div>',
            unsafe_allow_html=True,
        )

    # ── Navigation ───────────────────────────────────────────────────────────
    col_back, col_redo, col_apply = st.columns([1, 1, 2])
    with col_back:
        if st.button("← Back", use_container_width=True):
            goto("recognize")
    with col_redo:
        if st.button("↻ Re-run", use_container_width=True, help="Render again with the same settings"):
            clear_generation("result")
            st.rerun()
    with col_apply:
        if st.button("Apply & re-run", type="primary", use_container_width=True):
            st.session_state["adjustment"] = new_adjustment.strip()
            clear_generation("result")
            st.rerun()

    st.divider()
    if st.button("Browse lifestyle scenes →", use_container_width=True):
        # Force fresh suggestions on entry
        st.session_state.pop("placements", None)
        st.session_state.pop("selected_placement_idx", None)
        clear_generation("placement_result")
        goto("place")


# ═══════════════════════════════════════════════════════════════════════════════
# STAGE 4 — PLACE (lifestyle / scene placement)
# ═══════════════════════════════════════════════════════════════════════════════
elif st.session_state["stage"] == "place":
    st.markdown('<div class="kira-eyebrow">Step 4 · Placement</div>', unsafe_allow_html=True)
    st.markdown('<div class="kira-stage-title">Pick a lifestyle scene</div>', unsafe_allow_html=True)

    if "image_bytes" not in st.session_state:
        st.error("No image found — please go back and upload first.")
        if st.button("← Back to upload"):
            goto("upload")
        st.stop()

    ctx = st.session_state.get("product_context", {})

    # ── Style register selector ──────────────────────────────────────────────
    # Lets the user override the model's category-default aesthetic
    # (e.g. jewellery skewing luxe, plants skewing casual).
    st.session_state.setdefault("style_register", "Modern")
    REGISTERS = ["Understated", "Modern", "Luxe"]
    st.caption("Styling — sets how restrained or premium every scene looks:")
    if hasattr(st, "segmented_control"):
        chosen_register = st.segmented_control(
            "Styling",
            REGISTERS,
            default=st.session_state["style_register"],
            label_visibility="collapsed",
        )
    else:
        chosen_register = st.radio(
            "Styling",
            REGISTERS,
            index=REGISTERS.index(st.session_state["style_register"]),
            horizontal=True,
            label_visibility="collapsed",
        )
    if chosen_register and chosen_register != st.session_state["style_register"]:
        st.session_state["style_register"] = chosen_register
        st.session_state.pop("placements", None)
        st.session_state.pop("selected_placement_idx", None)
        clear_generation("placement_result")
        st.rerun()

    # ── Step A: ask GPT-4o for 10 tailored placement concepts ────────────────
    register = st.session_state["style_register"]
    if "placements" not in st.session_state:
        with st.spinner(spin(SPIN_SUGGEST, reg=register.lower())):
            st.session_state["placements"] = suggest_placements(ctx, style_register=register)

    suggestions = st.session_state["placements"]
    if "error" in suggestions:
        st.error(f"Couldn't get suggestions: {suggestions['error']}")
        col_back, col_retry = st.columns(2)
        with col_back:
            if st.button("← Back to enhance", use_container_width=True):
                goto("enhance")
        with col_retry:
            if st.button("↻ Retry suggestions", use_container_width=True):
                st.session_state.pop("placements", None)
                st.rerun()
        st.stop()

    placements = suggestions.get("placements", [])
    if not placements:
        st.warning("Model returned no placements. Try again.")
        if st.button("↻ Retry"):
            st.session_state.pop("placements", None)
            st.rerun()
        st.stop()

    st.caption(f"10 **{register}** scenes tailored to your product. Click **Generate** on one you like.")

    # ── Step B: 2×2 grid of placement cards ──────────────────────────────────
    cards_per_row = 2
    for row_start in range(0, len(placements), cards_per_row):
        cols = st.columns(cards_per_row)
        for col_idx, placement in enumerate(placements[row_start:row_start + cards_per_row]):
            idx = row_start + col_idx
            with cols[col_idx]:
                with st.container(border=True):
                    # Header row: label + type badge
                    ptype = placement.get("placement_type", "")
                    type_label = ptype.replace("_", " ").title() if ptype else ""
                    if type_label:
                        st.markdown(
                            f"**{placement.get('label', f'Option {idx + 1}')}** &nbsp; "
                            f"<span class='kira-badge'>{type_label}</span>",
                            unsafe_allow_html=True,
                        )
                    else:
                        st.markdown(f"**{placement.get('label', f'Option {idx + 1}')}**")

                    st.caption(placement.get("description", ""))

                    moods = placement.get("mood_keywords", [])
                    if moods:
                        st.markdown(" ".join(f"`{m}`" for m in moods))

                    palette = placement.get("color_palette", [])
                    if palette:
                        swatches = "".join(
                            f"<span style='display:inline-block;width:18px;height:18px;border-radius:4px;background:{c};margin-right:4px;border:1px solid #00000020;' title='{c}'></span>"
                            for c in palette
                        )
                        st.markdown(swatches, unsafe_allow_html=True)

                    with st.expander("Why it works / scene prompt"):
                        if placement.get("why_it_works"):
                            st.markdown(f"_{placement['why_it_works']}_")
                        if placement.get("scene_prompt"):
                            st.caption("Scene prompt sent to the image model:")
                            st.text(placement["scene_prompt"])

                    if st.button(
                        "Generate",
                        key=f"gen_{idx}",
                        type="primary",
                        use_container_width=True,
                    ):
                        st.session_state["selected_placement_idx"] = idx
                        clear_generation("placement_result")
                        snapshot_gen_params(model, quality, size, n_variations)
                        st.rerun()

    # ── Step C: generate variations for the chosen placement ─────────────────
    selected_idx = st.session_state.get("selected_placement_idx")
    if selected_idx is not None and 0 <= selected_idx < len(placements):
        chosen = placements[selected_idx]
        st.divider()
        st.subheader(f"Generating: {chosen.get('label', 'selection')}")

        if "placement_result" not in st.session_state:
            if "gen_params" not in st.session_state:
                snapshot_gen_params(model, quality, size, n_variations)
            gp = st.session_state["gen_params"]
            with st.spinner(spin(SPIN_PLACE)):
                st.session_state["placement_result"] = generate_placement(
                    image_bytes=st.session_state["image_bytes"],
                    scene_prompt=chosen.get("scene_prompt", ""),
                    product_context=ctx,
                    model=gp["model"],
                    size=gp["size"],
                    quality=gp["quality"],
                    n=gp["n"],
                )

        pres = st.session_state["placement_result"]
        if "error" in pres:
            st.error(f"Generation failed: {pres['error']}")
            if st.button("↻ Retry generation"):
                clear_generation("placement_result")
                st.rerun()
        else:
            source_stem = Path(st.session_state.get("source_name", "image")).stem
            slug = chosen.get("label", "scene").lower().replace(" ", "_").replace("/", "_")
            images = pres["images"]

            st.markdown(
                '<div class="kira-eyebrow">Lifestyle render · 1024×1024</div>',
                unsafe_allow_html=True,
            )

            grid_cols = st.columns(min(len(images), 2))
            for i, b64 in enumerate(images):
                with grid_cols[i % len(grid_cols)]:
                    st.image(b64_to_pil(b64), use_container_width=True)
                    st.download_button(
                        label=f"↓ Download v{i + 1}" if len(images) > 1 else "↓ Download",
                        data=base64.b64decode(b64),
                        file_name=f"{source_stem}_{slug}_v{i + 1}.png",
                        mime="image/png",
                        use_container_width=True,
                        key=f"dl_place_{i}",
                    )

    # ── Navigation ───────────────────────────────────────────────────────────
    st.divider()
    col_back, col_refresh = st.columns(2)
    with col_back:
        if st.button("← Back to enhance", use_container_width=True):
            goto("enhance")
    with col_refresh:
        if st.button("↻ New suggestions", use_container_width=True, help="Ask GPT-4o for a fresh batch of scene ideas"):
            st.session_state.pop("placements", None)
            st.session_state.pop("selected_placement_idx", None)
            clear_generation("placement_result")
            st.rerun()
