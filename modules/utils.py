"""
utils.py — Shared helper utilities for the AI Meeting Assistant.
"""

import re
import textwrap
from datetime import datetime


# ─────────────────────────────────────────────
# Text Chunking
# ─────────────────────────────────────────────

def chunk_text(text: str, max_words: int = 1800) -> list[str]:
    """
    Split a large transcript into overlapping word-based chunks
    so that no chunk exceeds roughly max_words words.
    Overlap of 50 words keeps context between chunks.
    """
    words = text.split()
    if len(words) <= max_words:
        return [text]

    chunks = []
    step = max_words - 50  # 50-word overlap
    for i in range(0, len(words), step):
        chunk = " ".join(words[i : i + max_words])
        chunks.append(chunk)
        if i + max_words >= len(words):
            break
    return chunks


# ─────────────────────────────────────────────
# Text Cleanup
# ─────────────────────────────────────────────

def clean_text(text: str) -> str:
    """
    Remove excess whitespace and normalize line breaks in a transcript.
    """
    # Collapse multiple blank lines to a single blank line
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Strip trailing spaces per line
    lines = [line.rstrip() for line in text.splitlines()]
    return "\n".join(lines).strip()


# ─────────────────────────────────────────────
# Timestamp
# ─────────────────────────────────────────────

def format_timestamp() -> str:
    """Return a human-readable timestamp string."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def slug_timestamp() -> str:
    """Return a slug-safe timestamp for file names."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


# ─────────────────────────────────────────────
# HTML Name Highlighting
# ─────────────────────────────────────────────

def highlight_names_in_text(text: str, names: list[str]) -> str:
    """
    Wrap detected person names with bold HTML tags in a plain-text transcript.
    Returns an HTML string safe for st.markdown.
    """
    if not names:
        return text

    # Sort longest names first to avoid partial replacements
    sorted_names = sorted(set(names), key=len, reverse=True)
    for name in sorted_names:
        escaped = re.escape(name)
        text = re.sub(
            rf"\b{escaped}\b",
            f"<strong style='color:#6366f1;'>{name}</strong>",
            text,
        )
    return text


# ─────────────────────────────────────────────
# Priority Color
# ─────────────────────────────────────────────

PRIORITY_COLORS = {
    "high": "#ef4444",
    "medium": "#f97316",
    "low": "#22c55e",
}


def priority_color(priority: str) -> str:
    """Return the hex color string for a given priority label."""
    return PRIORITY_COLORS.get(priority.lower(), "#94a3b8")


def priority_badge_html(priority: str) -> str:
    """Return a small colored HTML badge span for a priority value."""
    color = priority_color(priority)
    label = priority.capitalize()
    return (
        f"<span style='"
        f"background:{color}22; color:{color}; border:1px solid {color}; "
        f"border-radius:12px; padding:2px 10px; font-size:0.78rem; font-weight:600;'>"
        f"{label}</span>"
    )


# ─────────────────────────────────────────────
# JSON sanitizer
# ─────────────────────────────────────────────

def extract_json_block(raw: str) -> str:
    """
    Extract the first JSON object from a raw LLM response that may
    contain surrounding prose or markdown fences.
    """
    # Try to find a JSON block between ```json ... ``` fences
    fence_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL)
    if fence_match:
        return fence_match.group(1)

    # Otherwise find the outermost { ... }
    start = raw.find("{")
    end = raw.rfind("}")
    if start != -1 and end != -1 and end > start:
        return raw[start : end + 1]

    return raw  # Return as-is; will fail JSON parse downstream
