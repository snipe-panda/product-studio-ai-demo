"""
utils.py — Base64 encoding, image resizing, and format helpers.
No OpenAI calls here. PIL is allowed for I/O and resizing only.
"""

import base64
import io

from PIL import Image


def resize_image(source, max_dim: int = 1024) -> Image.Image:
    """Resize so neither dimension exceeds max_dim, preserving aspect ratio."""
    img = Image.open(source).convert("RGBA")
    img.thumbnail((max_dim, max_dim), Image.LANCZOS)
    return img


def pil_to_bytes(img: Image.Image, format: str = "PNG") -> bytes:
    """Convert a PIL Image to raw bytes."""
    buf = io.BytesIO()
    img.save(buf, format=format)
    return buf.getvalue()


def b64_to_pil(b64_string: str) -> Image.Image:
    """Decode a base64 string (as returned by the OpenAI API) into a PIL Image."""
    img_bytes = base64.b64decode(b64_string)
    return Image.open(io.BytesIO(img_bytes))
