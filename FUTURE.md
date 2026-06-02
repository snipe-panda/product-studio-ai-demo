# FUTURE.md — deferred ideas for the Kira demo

Things intentionally left out of the current build, captured so they aren't lost.

## Flow / UX
- **Before/after drag-slider** comparison on the Enhance stage, instead of the
  side-by-side columns.
- **Refine panel with history** — show the chain of adjustments applied, let the
  user step back to an earlier render rather than overwriting.
- **Inline "send to placements"** — skip the extra screen; offer placement
  scenes directly under the enhanced result.
- **True cross-refresh persistence** — today `stage` is mirrored to `?stage=`,
  but image bytes + results are lost on a hard browser refresh. Would need
  `localStorage` (e.g. `streamlit-js-eval`) or server-side storage keyed by a
  session id.

## Capability
- **Model / mannequin / on-body placements** — currently a hard "no humans"
  rule (image-edit models are unreliable with anatomy). Adding `in_use` /
  `on_body` / `on_mannequin` placement types would need: prompt guidance biased
  to partial/cropped human elements, a "product stays sharpest" reinforcement,
  a per-render opt-in, and a manual eval pass before shipping.
- **Batch catalogue** — the Kira mockup showed multi-product batch processing,
  a credits economy, brand kit, and pricing. This build is single-product by
  design; those are separate features, not styling.

## Notes
- This repo is the **demo build**: image model locked to `gpt-image-2` / medium.
  The development repo (`product-studio-ai-spec`) keeps the model selectors and
  cheaper defaults for iteration. Prompt improvements made there must be ported
  here manually — the two repos do not auto-sync.
