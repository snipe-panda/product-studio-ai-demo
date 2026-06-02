"""
styles.py — Kira visual layer for the demo build.

One CSS block, injected once from app.py via inject_css(). Streamlit's native
theme (.streamlit/config.toml) handles base colours; this file handles fonts,
chrome-hiding, typography, buttons, and the reusable component classes
(.kira-eyebrow, .kira-hero, .kira-chip, the stepper) used across the stages.
"""

import streamlit as st

# Design tokens kept in one place so the whole UI shifts together.
_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Space+Mono:wght@400;700&family=Inter:wght@400;500;600&display=swap');

:root {
  --kira-bg:        #0B0B0C;
  --kira-surface:   #161618;
  --kira-surface-2: #1D1D20;
  --kira-border:    #2A2A2E;
  --kira-text:      #EDEDED;
  --kira-muted:     #8A8A8F;
  --kira-amber:     #F2B24C;
  --kira-amber-soft:#F5C77E;
  --font-display: 'Space Grotesk', system-ui, sans-serif;
  --font-mono:    'Space Mono', ui-monospace, monospace;
  --font-body:    'Inter', system-ui, sans-serif;
}

/* ── Hide Streamlit chrome ──────────────────────────────────────────────── */
#MainMenu, footer, [data-testid="stToolbar"], [data-testid="stDecoration"],
[data-testid="stStatusWidget"] { display: none !important; }
header[data-testid="stHeader"] { background: transparent; height: 0; }

/* ── Canvas + layout width ──────────────────────────────────────────────── */
.stApp { background: var(--kira-bg); }
.block-container {
  max-width: 1100px;
  padding-top: 2.5rem;
  padding-bottom: 4rem;
}

/* ── Typography ─────────────────────────────────────────────────────────── */
html, body, [class*="css"], .stMarkdown, p, label, .stText {
  font-family: var(--font-body);
  color: var(--kira-text);
}
h1, h2, h3, h4 { font-family: var(--font-display); letter-spacing: -0.01em; }
h1 { font-weight: 700; }
a { color: var(--kira-amber-soft); }

/* ── Reusable Kira component classes ────────────────────────────────────── */
.kira-eyebrow {
  font-family: var(--font-mono);
  font-size: 0.72rem;
  letter-spacing: 0.22em;
  text-transform: uppercase;
  color: var(--kira-muted);
  margin-bottom: 0.9rem;
}
.kira-hero {
  font-family: var(--font-display);
  font-size: clamp(2.4rem, 5vw, 3.6rem);
  line-height: 1.02;
  font-weight: 700;
  margin: 0 0 1.1rem 0;
}
.kira-hero em {
  font-style: italic;
  color: var(--kira-amber-soft);
  font-weight: 600;
}
.kira-sub {
  font-size: 1.05rem;
  line-height: 1.55;
  color: #C9C9CE;
  max-width: 34ch;
}
.kira-chips { display: flex; flex-wrap: wrap; gap: 1.2rem; margin-top: 1.6rem; }
.kira-chip {
  display: inline-flex; align-items: center; gap: 0.45rem;
  font-size: 0.9rem; color: var(--kira-text);
}
.kira-chip .ic { color: var(--kira-amber); }

/* Brand lockup in the header */
.kira-brand { display: flex; align-items: center; gap: 0.6rem; }
.kira-brand .mark {
  width: 30px; height: 30px; border-radius: 9px;
  background: linear-gradient(140deg, var(--kira-amber), #E8943B);
  display: inline-flex; align-items: center; justify-content: center;
  color: #1a1205; font-weight: 700; box-shadow: 0 0 18px rgba(242,178,76,0.35);
}
.kira-brand .name {
  font-family: var(--font-display); font-weight: 700; font-size: 1.35rem;
  color: var(--kira-text);
}

/* ── Buttons → pills ────────────────────────────────────────────────────── */
.stButton > button, .stDownloadButton > button {
  border-radius: 999px;
  font-family: var(--font-body);
  font-weight: 600;
  border: 1px solid var(--kira-border);
  transition: transform 0.05s ease, border-color 0.15s ease;
}
.stButton > button:hover, .stDownloadButton > button:hover {
  border-color: var(--kira-amber);
}
.stButton > button:active { transform: translateY(1px); }
/* Primary buttons get the amber fill (kind="primary") */
.stButton > button[kind="primary"] {
  background: var(--kira-amber);
  color: #1a1205;
  border: none;
}
.stButton > button[kind="primary"]:hover { background: var(--kira-amber-soft); }

/* ── Inputs + cards ─────────────────────────────────────────────────────── */
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea {
  background: var(--kira-surface);
  border: 1px solid var(--kira-border);
  border-radius: 10px;
  color: var(--kira-text);
}
[data-testid="stExpander"] {
  border: 1px solid var(--kira-border);
  border-radius: 12px;
  background: var(--kira-surface);
}
/* Bordered containers (placement cards) */
[data-testid="stVerticalBlockBorderWrapper"] {
  border-radius: 16px !important;
  border-color: var(--kira-border) !important;
  background: var(--kira-surface);
}

/* ── Dropzone (file uploader) ───────────────────────────────────────────── */
[data-testid="stFileUploaderDropzone"] {
  background: var(--kira-surface);
  border: 1.5px dashed var(--kira-border);
  border-radius: 18px;
  padding: 2.2rem 1.5rem;
  min-height: 220px;
}
[data-testid="stFileUploaderDropzone"]:hover { border-color: var(--kira-amber); }

/* ── Stepper ────────────────────────────────────────────────────────────── */
.kira-stepper { display: flex; align-items: center; gap: 0.4rem; margin: 0.2rem 0 1.6rem; }
.kira-step { display: flex; align-items: center; gap: 0.55rem; }
.kira-step .num {
  width: 26px; height: 26px; border-radius: 999px;
  display: inline-flex; align-items: center; justify-content: center;
  font-family: var(--font-mono); font-size: 0.8rem; font-weight: 700;
  border: 1px solid var(--kira-border); color: var(--kira-muted);
}
.kira-step .lbl { font-size: 0.95rem; color: var(--kira-muted); }
.kira-step.done .num   { border-color: var(--kira-amber); color: var(--kira-amber); }
.kira-step.active .num { background: var(--kira-amber); color: #1a1205; border: none; }
.kira-step.active .lbl { color: var(--kira-text); font-weight: 600; }
.kira-step-sep { flex: 0 0 28px; height: 1px; background: var(--kira-border); }
</style>
"""


def inject_css() -> None:
    """Inject the Kira CSS layer. Call once, right after st.set_page_config()."""
    st.markdown(_CSS, unsafe_allow_html=True)
