"""
action_extractor.py — NLP-based name detection and action item enrichment.

Uses spaCy (en_core_web_sm) to detect PERSON entities in the transcript.
Enriches LLM-produced action items by matching detected names to owners.
"""

import re
import streamlit as st


# ─────────────────────────────────────────────
# spaCy model loader (cached across reruns)
# ─────────────────────────────────────────────

@st.cache_resource(show_spinner=False)
def _load_spacy_model():
    """Load and cache the spaCy English model."""
    try:
        import spacy
        try:
            nlp = spacy.load("en_core_web_sm")
        except OSError:
            # Auto-download model if not installed
            import subprocess, sys
            subprocess.run(
                [sys.executable, "-m", "spacy", "download", "en_core_web_sm"],
                check=True,
                capture_output=True,
            )
            nlp = spacy.load("en_core_web_sm")
        return nlp
    except Exception as e:
        st.warning(
            f"⚠️ spaCy not available ({e}). Name detection will be skipped. "
            "Run: `pip install spacy && python -m spacy download en_core_web_sm`"
        )
        return None


# ─────────────────────────────────────────────
# Name detection
# ─────────────────────────────────────────────

def detect_names(transcript: str) -> list[str]:
    """
    Run spaCy NER on the transcript and return all unique PERSON entity strings.

    Parameters
    ----------
    transcript : str
        The full meeting transcript.

    Returns
    -------
    list[str]
        Sorted list of unique person names detected.
    """
    nlp = _load_spacy_model()
    if nlp is None:
        return []

    # spaCy handles up to ~1M chars; chunk if necessary
    max_chars = 900_000
    text = transcript[:max_chars]
    doc = nlp(text)

    names = sorted({
        ent.text.strip()
        for ent in doc.ents
        if ent.label_ == "PERSON" and len(ent.text.strip()) > 1
    })
    return names


# ─────────────────────────────────────────────
# Owner matching
# ─────────────────────────────────────────────

def _find_best_name_match(owner_str: str, known_names: list[str]) -> str:
    """
    Given an owner string from the LLM output and a list of known names from
    the transcript, return the best matching name or 'Unassigned'.
    """
    if not owner_str or owner_str.lower() in ("unassigned", "n/a", "none", ""):
        return "Unassigned"

    owner_lower = owner_str.lower()

    # Exact match first
    for name in known_names:
        if name.lower() == owner_lower:
            return name

    # Partial match: check if owner_str is a substring of a known name or vice versa
    for name in known_names:
        if owner_lower in name.lower() or name.lower() in owner_lower:
            return name

    # If LLM gave a name not in our NER list, trust the LLM (it may have context we missed)
    if len(owner_str.split()) >= 1 and owner_str[0].isupper():
        return owner_str  # Looks like a proper noun – keep it

    return "Unassigned"


# ─────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────

def enrich_actions(actions: list[dict], transcript: str) -> tuple[list[dict], list[str]]:
    """
    Detect names in the transcript and improve owner fields in action items.

    Parameters
    ----------
    actions : list[dict]
        List of action items from the LLM (may have imprecise owner fields).
    transcript : str
        The full transcript for NER.

    Returns
    -------
    tuple[list[dict], list[str]]
        (enriched_actions, detected_names_list)
    """
    known_names = detect_names(transcript)

    enriched = []
    for action in actions:
        enriched_action = dict(action)  # copy
        raw_owner = action.get("owner", "Unassigned")
        enriched_action["owner"] = _find_best_name_match(raw_owner, known_names)
        enriched.append(enriched_action)

    return enriched, known_names
