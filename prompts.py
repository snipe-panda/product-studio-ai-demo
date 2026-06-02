"""
prompts.py — All prompt strings for Product Studio AI.

Keep every prompt here. No prompt text inline in app.py, image_pipeline.py,
or vision.py. This makes prompt iteration (the highest-churn part of an AI app)
safe and isolated from application logic.
"""

# ══════════════════════════════════════════════════════════════════════════════
# PHASE 1 — One-shot studio enhancement (3-in-1)
# ══════════════════════════════════════════════════════════════════════════════
# This single prompt instructs GPT-Image-1 to perform all three transformations
# at once: perspective correction, background replacement, lighting + shadow.
# Preservation constraints are critical — the model must not alter the product
# itself, only its orientation, background, and lighting.

STUDIO_ENHANCE_PROMPT = """
You are a professional product photographer and retoucher. You will receive one
amateur product photograph. Your job is to transform it into a clean,
studio-quality e-commerce listing image.

═══════════════════════════════════════════════════════
STEP 0 — ANALYSE THE INPUT FIRST
═══════════════════════════════════════════════════════
Before making any changes, carefully study the product in the photo:
- Identify the exact shape, size, and proportions of the product
- Note every colour, material, texture, and finish on its surface
- Read and memorise every label, logo, text, pattern, and marking
- Note the product's current orientation and any tilt or skew

You will use this analysis as your reference. The product you output must
be a faithful reproduction of this exact product — not a generic version of it.

═══════════════════════════════════════════════════════
STEP 1 — PERSPECTIVE & ORIENTATION
═══════════════════════════════════════════════════════
- Straighten the product so it sits perfectly upright with no tilt or skew
- Present it from a clean front-facing or slight three-quarter angle
  (whichever shows the most important face of the product)
- The product should appear as if photographed from eye-level or slightly above,
  with a natural, undistorted perspective — no extreme angles, no fisheye
- If the product has a natural "display side" (e.g. a label, a screen, a logo),
  ensure that face is visible and forward-facing

═══════════════════════════════════════════════════════
STEP 2 — BACKGROUND
═══════════════════════════════════════════════════════
- Remove the original background completely — no remnants, no halos, no fringing
- Replace with a pure seamless studio backdrop:
  · Colour: bright white (#FFFFFF) or very light neutral grey (#F2F2F2)
  · Texture: perfectly smooth, no gradients, no vignette, no props, no surfaces
- The background must be completely flat and uniform — identical to what you
  would see in a high-end Amazon or Apple product listing

═══════════════════════════════════════════════════════
STEP 3 — LIGHTING & SHADOW
═══════════════════════════════════════════════════════
Lighting:
- Apply soft, diffused, even studio lighting from a slight front-top angle
- The light should wrap around the product with no harsh shadows on its surface
- Highlights should be gentle and specular — bright enough to show material
  finish (matte, glossy, metallic) without blowing out
- No coloured light, no dramatic side-lighting, no dark shadows on the product

Shadow:
- Add one single, soft, natural drop shadow directly beneath the product
- The shadow should be short (not long or dramatic), soft-edged, and low opacity
  (~20–30% opacity) — just enough to "ground" the product on the surface
- The shadow falls straight down, not at an angle

═══════════════════════════════════════════════════════
STEP 4 — OUTPUT COMPOSITION
═══════════════════════════════════════════════════════
- The product should be centred horizontally and vertically in the frame
- The product should occupy approximately 75–80% of the frame height
- Leave equal, balanced white space on all four sides
- Do not crop any part of the product
- Output a single square image

═══════════════════════════════════════════════════════
CRITICAL — WHAT MUST NOT CHANGE
═══════════════════════════════════════════════════════
The following must be reproduced exactly as they appear in the input photo:
✗ Do NOT change the product's shape, silhouette, or proportions
✗ Do NOT change any colours — match them exactly to the input
✗ Do NOT alter, blur, distort, or remove any text, labels, or logos
✗ Do NOT add features, parts, or details that are not in the input photo
✗ Do NOT remove features, parts, or details visible in the input photo
✗ Do NOT change the material or texture of any surface
✗ Do NOT make the product look like a "generic" version of its category

Only three things may change: orientation, background, and lighting.
""".strip()


# ══════════════════════════════════════════════════════════════════════════════
# PHASE 2 — Recognition (Turn 1) — used by vision.py
# ══════════════════════════════════════════════════════════════════════════════

RECOGNIZE_PRODUCT_PROMPT = """
You are a senior product photographer, brand stylist, and visual merchandiser
combined. You are about to brief two downstream AI models — one that will
re-photograph this product in a studio, and one that will propose lifestyle
scenes for it. The quality of their output depends entirely on the depth and
accuracy of your description.

Study the product photograph in extreme detail and return ONE valid JSON object
with the following exact schema. Every field is required. Use empty arrays []
or "unknown" where you genuinely cannot tell — do not invent.

═══════════════════════════════════════════════════════
OUTPUT SCHEMA (return JSON in exactly this shape)
═══════════════════════════════════════════════════════
{
  "identity": {
    "product_type": "string — specific name, e.g. 'self-watering plastic plant pot' not just 'pot'",
    "product_subtype": "string — finer category, e.g. 'indoor decorative planter'",
    "likely_category": "string — retail category, e.g. 'home & garden / planters'",
    "intended_use": "string — what it is for and where it would be used"
  },

  "form": {
    "shape": "string — geometric shape (cylindrical, tapered, cuboid, rounded, etc.)",
    "silhouette": "string — overall outline description",
    "approximate_dimensions": "string — your best guess, e.g. 'small, ~12cm tall × 10cm wide'",
    "proportions": "string — height-to-width relationship, taper, symmetry",
    "orientation_in_photo": "string — how the product is currently positioned (upright, tilted, on side, etc.)"
  },

  "surface": {
    "primary_color": "string — most dominant colour, be specific (e.g. 'matte terracotta red', not 'red')",
    "secondary_colors": ["array of other visible colours, each with where it appears"],
    "color_pattern": "string — solid, gradient, two-tone, patterned, etc.",
    "material_likely": "string — material guess, append '(verify with user)' if uncertain",
    "surface_finish": "string — matte / satin / glossy / textured / brushed / etc.",
    "texture": "string — smooth, ribbed, embossed, woven, grainy, etc."
  },

  "markings": {
    "text_visible": ["EVERY piece of text/word/number you can see on the product, verbatim"],
    "logos_visible": ["describe any logos, marks, brand symbols (do NOT guess brand names you can't read)"],
    "graphics_visible": ["any illustrations, patterns, or decorative graphics"],
    "label_position": "string — where on the product the markings sit (e.g. 'lower-right face, centred')"
  },

  "detail": {
    "distinguishing_features": [
      "5 to 8 specific, observable details that make THIS product unique",
      "e.g. 'visible drainage hole at base', 'double-walled construction', 'raised lip at top'"
    ],
    "parts_visible": ["distinct parts or components visible (handle, lid, base, screen, strap, etc.)"],
    "openings_or_seams": ["any visible openings, joins, seams, or assembly lines"],
    "condition": "string — new / used / worn / damaged + any visible wear"
  },

  "photo_critique": {
    "composition_issues": ["what is wrong with framing, angle, centering, cropping"],
    "lighting_issues": ["what is wrong with lighting — direction, harshness, shadows, colour cast"],
    "background_issues": ["what is wrong with the background — clutter, colour, texture"],
    "color_issues": ["any white-balance, saturation, or colour-cast problems"],
    "suggested_best_angle": "string — the angle that would best showcase this product (front-facing / three-quarter / top-down / etc.)"
  },

  "generation_hints": {
    "target_audience": "string — who would buy this product",
    "suggested_styling_mood": "string — minimal / luxurious / playful / rustic / industrial / etc.",
    "scenes_that_would_suit": [
      "3 to 5 short scene/placement ideas tailored to THIS product",
      "e.g. 'minimal Scandinavian shelf with linen backdrop'"
    ],
    "colors_that_would_complement": ["palette colours that would flatter this product in a scene"]
  },

  "meta": {
    "uncertainties": ["anything you are not 100% sure about and should confirm with the user"],
    "confidence_score": 0.0,
    "warnings_for_enhancement": [
      "anything the enhancement model MUST be careful about preserving",
      "e.g. 'the embossed logo on the front must not be smoothed away'"
    ]
  }
}

═══════════════════════════════════════════════════════
RULES
═══════════════════════════════════════════════════════
- Be exhaustive. Err on the side of TOO MUCH detail rather than too little.
- Do NOT invent details that aren't visible. Use "unknown" or [] honestly.
- Do NOT guess brand names unless the text is clearly legible.
- Read ALL visible text verbatim — even partial or hard-to-read text.
- confidence_score is a single float between 0.0 and 1.0 reflecting overall
  certainty across the description.
- Return ONLY the JSON object. No prose before or after.
""".strip()


# ══════════════════════════════════════════════════════════════════════════════
# PHASE 2 — Context-informed enhancement (Turn 2)
# ══════════════════════════════════════════════════════════════════════════════
# Same as STUDIO_ENHANCE_PROMPT but with a slot for confirmed product context
# from Turn 1, improving fidelity.

STUDIO_ENHANCE_WITH_CONTEXT_PROMPT = """
You are a professional product photographer and retoucher. You will receive one
amateur product photograph plus a confirmed, human-verified description of the
exact product in the photo. Your job is to transform the photo into a clean,
studio-quality e-commerce listing image while reproducing the described
product with maximum fidelity.

═══════════════════════════════════════════════════════
CONFIRMED PRODUCT DETAILS (human-verified — trust these)
═══════════════════════════════════════════════════════
{product_context}

These details have been confirmed by a human. Use them to:
- Resolve any ambiguity in the input photo (poor lighting, motion blur,
  occlusion) by referring to these confirmed facts
- Make sure every named feature is visible and recognisable in your output
- Reproduce the named colours and materials accurately
- Preserve any text, logos, and markings listed above exactly as they are

═══════════════════════════════════════════════════════
STEP 0 — ANALYSE THE INPUT FIRST
═══════════════════════════════════════════════════════
Before making any changes, study the product in the photo carefully and
cross-reference against the confirmed details above:
- Identify the exact shape, size, and proportions of the product
- Note every colour, material, texture, and finish on its surface
- Read and memorise every label, logo, text, pattern, and marking
- Note the product's current orientation and any tilt or skew

The product you output must be a faithful reproduction of this exact product —
not a generic version of it.

═══════════════════════════════════════════════════════
STEP 1 — PERSPECTIVE & ORIENTATION
═══════════════════════════════════════════════════════
- Straighten the product so it sits perfectly upright with no tilt or skew
- Present it from a clean front-facing or slight three-quarter angle
  (whichever shows the most important face of the product, including any
  text or logo from the confirmed details)
- The product should appear as if photographed from eye-level or slightly above,
  with a natural, undistorted perspective — no extreme angles, no fisheye
- If the product has a natural "display side" (e.g. a label, a screen, a logo),
  ensure that face is visible and forward-facing

═══════════════════════════════════════════════════════
STEP 2 — BACKGROUND
═══════════════════════════════════════════════════════
- Remove the original background completely — no remnants, no halos, no fringing
- Replace with a pure seamless studio backdrop:
  · Colour: bright white (#FFFFFF) or very light neutral grey (#F2F2F2)
  · Texture: perfectly smooth, no gradients, no vignette, no props, no surfaces
- The background must be completely flat and uniform — identical to what you
  would see in a high-end Amazon or Apple product listing

═══════════════════════════════════════════════════════
STEP 3 — LIGHTING & SHADOW
═══════════════════════════════════════════════════════
Lighting:
- Apply soft, diffused, even studio lighting from a slight front-top angle
- The light should wrap around the product with no harsh shadows on its surface
- Highlights should be gentle and specular — bright enough to show material
  finish (matte, glossy, metallic) without blowing out
- No coloured light, no dramatic side-lighting, no dark shadows on the product

Shadow:
- Add one single, soft, natural drop shadow directly beneath the product
- The shadow should be short (not long or dramatic), soft-edged, and low opacity
  (~20–30% opacity) — just enough to "ground" the product on the surface
- The shadow falls straight down, not at an angle

═══════════════════════════════════════════════════════
STEP 4 — OUTPUT COMPOSITION
═══════════════════════════════════════════════════════
- The product should be centred horizontally and vertically in the frame
- The product should occupy approximately 75–80% of the frame height
- Leave equal, balanced white space on all four sides
- Do not crop any part of the product
- Output a single square image

═══════════════════════════════════════════════════════
USER ADJUSTMENT (optional — apply if provided)
═══════════════════════════════════════════════════════
{user_adjustment}

If the line above is empty or says "(none)", ignore it.
If it contains instructions, apply them as a layered preference on top of all
the rules above — but the preservation constraints below always win.

═══════════════════════════════════════════════════════
CRITICAL — WHAT MUST NOT CHANGE (this overrides everything else)
═══════════════════════════════════════════════════════
The following must be reproduced exactly as they appear in the input photo AND
as described in the confirmed details:
✗ Do NOT change the product's shape, silhouette, or proportions
✗ Do NOT change any colours — match them exactly to the input and the
  confirmed primary/secondary colours
✗ Do NOT alter, blur, distort, or remove any text, labels, or logos —
  especially any text or logos listed in the confirmed details
✗ Do NOT add features, parts, or details that are not in the input photo
✗ Do NOT remove features, parts, or details visible in the input photo —
  especially the named features in the confirmed details
✗ Do NOT change the material or texture of any surface
✗ Do NOT make the product look like a "generic" version of its category

Only three things may change: orientation, background, and lighting.
Plus any user adjustment above, only insofar as it does not conflict with these
preservation rules.
""".strip()


# ══════════════════════════════════════════════════════════════════════════════
# PHASE 2 — Placement suggestions (Turn 3, text step via GPT-4o)
# ══════════════════════════════════════════════════════════════════════════════
#
# DESIGN DECISION — NO HUMANS, NO BODY PARTS, NO MANNEQUINS.
# Both the suggestion prompt below and PLACEMENT_GENERATE_PROMPT enforce this.
# Rationale and the path to lifting this restriction in a future enhancement
# are documented in ARCHITECTURE.md → "Place stage — deliberate 'no humans'
# rule" and in README.md → Future enhancements. If you're about to add
# `in_use`, `on_body`, or `on_mannequin` placement types, read those notes
# first — there is a checklist for doing it safely.

# Aesthetic registers the user picks on the Place stage. Each is injected into
# the {style_register} slot of PLACEMENT_SUGGESTIONS_PROMPT to override the
# model's category-default styling. Keys match the UI labels.
STYLE_REGISTERS = {
    "Understated": (
        "UNDERSTATED / MINIMALIST. Maximum restraint. Heavy negative space, a "
        "single clean surface, at most 1–2 props. Muted, near-monochrome or "
        "tonal palette (soft whites, greys, sand, pale stone). Soft, even, "
        "diffused light with gentle shadows. No clutter, no drama, no rich "
        "materials. Think quiet Scandinavian / Kinfolk editorial calm."
    ),
    "Modern": (
        "MODERN / EVERYDAY-ELEVATED. Approachable but polished — the look of a "
        "well-shot contemporary retail or DTC brand listing. Clean surfaces with "
        "a few intentional, real-world props. Warm, natural light. Balanced, "
        "inviting palette with one or two accent colours. Neither stark nor "
        "opulent — confident and current."
    ),
    "Luxe": (
        "LUXE / PREMIUM. High-end and editorial. Rich materials (marble, brass, "
        "polished stone, velvet, dark wood, glass). Dramatic directional lighting "
        "with deliberate highlights and shadow. Deep, saturated or jewel-toned "
        "palette. A sense of occasion and craftsmanship. Think luxury magazine "
        "or flagship-boutique product photography."
    ),
}


PLACEMENT_SUGGESTIONS_PROMPT = """
You are a creative director, set designer, and brand stylist combined. You are
about to brief an image-generation model to produce ten distinct lifestyle /
scene photographs of the same product. Your job is to propose ten visually
distinct, commercially compelling placement concepts tailored to THIS product.

═══════════════════════════════════════════════════════
CONFIRMED PRODUCT
═══════════════════════════════════════════════════════
{product_context}

═══════════════════════════════════════════════════════
STYLE REGISTER (the aesthetic the user has chosen — obey it)
═══════════════════════════════════════════════════════
{style_register}

This register overrides any default aesthetic you would infer from the product
category. Do NOT default jewellery to opulent or plants to casual — apply the
register above to EVERY one of the 10 placements consistently.

═══════════════════════════════════════════════════════
WHAT MAKES A GOOD PLACEMENT
═══════════════════════════════════════════════════════
A good placement makes the viewer instantly understand:
1. **What the product is for** — surround it with the things it works with or
   on (a plant sprayer next to leafy plants with fine water droplets; a knife
   with sliced herbs; a candle with matches and dried orange slices).
2. **Who the product is for** — match props, surfaces, and palette to that
   audience's aesthetic world.
3. **Where it belongs** — the natural environment of the product's use.

The most powerful technique is the **companion objects** approach: put the
product near the things it interacts with in real life, but with NO humans.

═══════════════════════════════════════════════════════
PLACEMENT TYPES (you must use a mix — see diversity rule below)
═══════════════════════════════════════════════════════
- "still_life"            — the product alone on a clean surface, hero-style
- "companion_objects"     — the product beside its natural-use companions
                            (e.g. sprayer + leafy plant + water droplets)
- "lifestyle_environment" — the product in its natural habitat / setting
                            (e.g. on a sunlit plant shelf, on a chef's counter)
- "texture_play"          — the product against contrasting materials
                            (e.g. matte ceramic on rough oak; glass on linen)
- "seasonal_thematic"     — styled to a season, holiday, or occasion
- "editorial_minimal"     — magazine-style negative space, bold colour block,
                            very few props
- "maximalist_styled"     — rich, layered, prop-heavy composition

═══════════════════════════════════════════════════════
HARD CONSTRAINT — NO HUMANS, EVER
═══════════════════════════════════════════════════════
✗ NO humans, hands, fingers, arms, ears, necks, faces, hair, skin
✗ NO body parts of any kind, even partial or out-of-frame
✗ NO mannequins, statues, or human silhouettes
✗ NO "held" or "worn" placements

The product is always presented BY ITSELF or with INANIMATE companion objects
(plants, food, fabric, furniture, props, lighting, environments). Plants and
animals are fine. Humans are not.

═══════════════════════════════════════════════════════
OUTPUT SCHEMA — return ONE valid JSON object exactly in this shape
═══════════════════════════════════════════════════════
{{
  "placements": [
    {{
      "label": "string — short evocative name (2-4 words), e.g. 'Misted Monstera Shelf'",
      "placement_type": "one of: still_life | companion_objects | lifestyle_environment | texture_play | seasonal_thematic | editorial_minimal | maximalist_styled",
      "description": "string — one sentence the user will read on a card",
      "mood_keywords": ["3-5 mood tags, e.g. 'minimal', 'warm', 'editorial'"],
      "scene_prompt": "string — a DETAILED scene description that will be fed verbatim into the image-generation model. Include: surface/material, named specific props (companion objects when relevant), lighting direction and quality, time-of-day implied, dominant colour palette, depth-of-field feel, camera angle. Be sensory and specific.",
      "color_palette": ["3-5 hex codes that dominate the scene"],
      "why_it_works": "string — one sentence on why this scene flatters THIS specific product"
    }}
  ]
}}

═══════════════════════════════════════════════════════
RULES
═══════════════════════════════════════════════════════
- Return exactly 10 placements.
- DIVERSITY RULE: use a mix of placement_type values. No more than 2 of any
  single type. At least 2 should be "companion_objects" if the product is used
  on/with something (a plant sprayer, a kitchen tool, a cosmetic, etc.).
- The scene_prompt is the most important field — rich enough that another AI
  can render the scene without seeing this brief. Write it as a prompt fragment
  a photographer would understand.
- Do NOT describe the product itself in the scene_prompt — that comes from the
  reference image. Only describe what surrounds it.
- Do NOT use generic placeholders like "a nice setting". Be specific:
  "weathered oak shelf, raw linen runner, dried wheat stems in a ceramic vase".
- Companion objects must be physically plausible (the product would actually
  appear near these things in real life).
- SCALE AWARENESS: only suggest companion objects that are scale-appropriate
  for the product's real-world size (see "Approximate real-world size" in the
  confirmed product, if present). A small earring should not be paired with a
  large coffee mug; a chair should not be paired with a thimble. When in doubt,
  pick props that are within ~2x the product's largest dimension.
- Return ONLY the JSON object. No prose before or after.
""".strip()


# ══════════════════════════════════════════════════════════════════════════════
# PHASE 2 — Placement generation (Turn 3, image step via GPT-Image-1)
# ══════════════════════════════════════════════════════════════════════════════

PLACEMENT_GENERATE_PROMPT = """
You are a lifestyle product photographer. You will receive one reference
photograph of a product. Your job is to place the EXACT SAME product into a
new scene, described below, while preserving the product itself with
maximum fidelity.

═══════════════════════════════════════════════════════
CONFIRMED PRODUCT DETAILS (human-verified — trust these)
═══════════════════════════════════════════════════════
{product_context}

═══════════════════════════════════════════════════════
SCENE TO PLACE THE PRODUCT INTO
═══════════════════════════════════════════════════════
{scene_prompt}

═══════════════════════════════════════════════════════
STEP 0 — ANALYSE THE REFERENCE PRODUCT
═══════════════════════════════════════════════════════
Before rendering the scene, study the product carefully:
- Identify the exact shape, size, and proportions of the product
- Note every colour, material, texture, and finish on its surface
- Read and memorise every label, logo, text, pattern, and marking
- Cross-reference against the confirmed details above

═══════════════════════════════════════════════════════
STEP 1 — STAGE THE SCENE
═══════════════════════════════════════════════════════
Build the scene exactly as described above. Render the surfaces, props, and
environment with photographic realism. Honour the mood, palette, and lighting
implied by the scene description.

═══════════════════════════════════════════════════════
STEP 2 — PLACE THE PRODUCT IN THE SCENE
═══════════════════════════════════════════════════════
- Position the product as the clear focal point — usually centred or
  rule-of-thirds, with the most important face (label, logo, screen) visible
- Match the product's lighting to the scene's lighting direction, colour
  temperature, and softness — but keep the product clearly legible
- Add a natural, scene-consistent contact shadow beneath the product
- Use realistic depth-of-field — the product should be sharp; backdrop and
  props can soften gently if the scene implies it
- SCALE: render the product at realistic real-world size relative to every
  companion object in the scene. If the confirmed product details above give
  an approximate size, use that as your anchor. A 28cm spray bottle next to a
  10cm potted herb should look meaningfully taller; a 2cm earring next to a
  10cm jewellery dish should look meaningfully smaller. Do NOT default to
  making the product fill the frame regardless of true size.

═══════════════════════════════════════════════════════
STEP 3 — OUTPUT COMPOSITION
═══════════════════════════════════════════════════════
- The product should occupy 45–65% of the frame (smaller than the studio
  shot — this is a lifestyle scene, not a product shot)
- Leave breathing room; do not crop the product
- Output a single high-quality lifestyle photograph

═══════════════════════════════════════════════════════
HARD CONSTRAINT — NO HUMANS, EVER
═══════════════════════════════════════════════════════
The scene must never contain:
✗ Humans, hands, fingers, arms, ears, necks, faces, hair, or skin
✗ Body parts of any kind, even partial or out-of-frame
✗ Mannequins, statues, or human silhouettes

If the scene description above mentions or implies a person in any way, ignore
that part of the description and render the scene without any human element.
Plants, animals, food, fabric, props, surfaces, and lighting are all fine.

═══════════════════════════════════════════════════════
CRITICAL — WHAT MUST NOT CHANGE (overrides everything)
═══════════════════════════════════════════════════════
Even though the scene is new, the product itself must be reproduced exactly:
✗ Do NOT change the product's shape, silhouette, or proportions
✗ Do NOT change any colours — match them exactly to the reference photo and
  the confirmed details
✗ Do NOT alter, blur, distort, or remove any text, labels, or logos
✗ Do NOT add features, parts, or details that are not on the reference product
✗ Do NOT remove features visible on the reference product
✗ Do NOT change the material or finish
✗ Do NOT replace the product with a generic version of its category

The scene around the product may change. The product itself must not.
""".strip()
