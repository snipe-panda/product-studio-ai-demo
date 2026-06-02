# ◆ Kira — Product Studio (demo build)

**One phone photo in. Studio listing out.**

Kira turns a crooked, badly-lit phone snapshot into a clean, studio-quality
e-commerce listing image — then suggests lifestyle scenes to place it in. Every
transformation is done through OpenAI image + vision models, not classical
computer vision.

> This is the **demo build** — a polished, user-facing snapshot with the image
> model locked to the flagship for consistent output. The development repo
> (`product-studio-ai-spec`) keeps the model/quality selectors and cheaper
> defaults for iteration. See [`FUTURE.md`](./FUTURE.md) for deferred ideas.

---

## The flow

A guided four-stage pipeline (state lives in `st.session_state`):

1. **Upload** — drop a JPG/PNG product photo.
2. **Identify** — GPT-4o Vision describes the product (type, material, colour,
   size, features, do-not-alter list). You review and correct it.
3. **Enhance** — the photo is straightened, the background swapped for a clean
   studio backdrop, and studio lighting added — guided by the confirmed details.
   A refine box lets you iterate ("soften the shadow", "warmer background").
4. **Place** — GPT-4o proposes 10 lifestyle scenes tailored to the product, in
   your chosen aesthetic register (**Understated / Modern / Luxe**). Pick one and
   Kira renders the product into that scene.

No humans, hands, or mannequins ever appear in generated scenes (image models
are unreliable with anatomy) — placements use companion objects and environments
instead.

---

## Stack

| Layer | Choice |
|---|---|
| UI | Streamlit (single app) + a custom CSS theme layer (`styles.py`) |
| Image model | **`gpt-image-2` / medium / 1024×1024** (locked, no selector) |
| Vision + suggestions | GPT-4o |
| Image I/O | Pillow (resize / base64 only — never the enhancement itself) |
| Secrets | `python-dotenv` locally, Streamlit secrets when deployed |

### File layout
```
app.py             # UI + the four-stage state machine
styles.py          # Kira CSS theme (fonts, chrome-hiding, components)
image_pipeline.py  # gpt-image-2 calls (enhance, context-enhance, placement)
vision.py          # GPT-4o recognition + placement suggestions
prompts.py         # every prompt string + STYLE_REGISTERS
utils.py           # base64 / resize helpers
.streamlit/config.toml  # native dark + amber theme
```

---

## Run it locally

Requires Python 3.12+, an OpenAI API key with `gpt-image-2` access, and
[`uv`](https://docs.astral.sh/uv/).

```bash
git clone git@github.com:snipe-panda/product-studio-ai-demo.git
cd product-studio-ai-demo
cp .env.example .env          # paste your OPENAI_API_KEY into .env

uv run --with streamlit --with python-dotenv --with Pillow --with openai \
  streamlit run app.py
```

Or with pip: `pip install -r requirements.txt && streamlit run app.py`.

> **Cost note:** this build uses `gpt-image-2` at medium quality — roughly
> **$0.07–0.15 per generated image**. Each Enhance and each Placement render is
> one call. Use deliberately.

---

## Deploy (Streamlit Cloud)

1. The repo is already public.
2. At [share.streamlit.io](https://share.streamlit.io) → **New app** → point at
   this repo and `app.py`.
3. **Settings → Secrets**, paste:
   ```toml
   OPENAI_API_KEY = "sk-..."
   ```
4. Deploy. The same code runs locally (`.env`) and on Cloud (secrets) unchanged.
