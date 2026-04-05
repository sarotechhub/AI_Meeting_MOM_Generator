"""
llm_engine.py — LLM-powered meeting insight extraction.

Primary:  NVIDIA NIM API  (meta/llama-3.1-70b-instruct)
Fallback: HuggingFace transformers pipeline (local, CPU)

Both paths return the same structured JSON dict.
"""

import json
import os
import re
import streamlit as st
from modules.utils import chunk_text, extract_json_block


# ─────────────────────────────────────────────
# Prompt template
# ─────────────────────────────────────────────

SYSTEM_PROMPT = """You are an elite, highly precise meeting analyst and minute-taker.
Your mission is to analyze meeting transcripts with absolute accuracy and 100% comprehensive extraction. 
You MUST NOT miss any action items, decisions, or critical context. Capture every detail accurately.
Always respond with a single valid JSON object. No explanation, no markdown fences."""

USER_PROMPT_TEMPLATE = """Analyze the following meeting transcript and return ONLY a JSON object in this exact structure:

{{
  "summary": "Executive summary formatted exclusively as professional email bullet points (e.g. using •). Format it ready to be copy-pasted into an email dispatch.",
  "decisions": [
    "Decision 1",
    "Decision 2"
  ],
  "actions": [
    {{
      "task": "Specific task description",
      "owner": "Person's name if mentioned, otherwise Unassigned",
      "priority": "High or Medium or Low",
      "deadline": "Date or timeframe if mentioned, otherwise null"
    }}
  ]
}}

Rules:
- Exhaustively extract ALL action items, even implicit or softly stated ones. Leave absolutely nothing out.
- Ensure every final decision or consensus point is captured accurately and entirely.
- For priority: High = urgent/critical, Medium = important but not urgent, Low = nice-to-have.
- For owner: use the exact name mentioned in the transcript. If unclear, write "Unassigned".
- For deadline: use the exact phrase from the transcript (e.g., "by Friday", "end of Q2"). If not mentioned, use null.
- Decisions are resolved conclusions, not pending tasks. Do not hallucinate or omit data.

Meeting Transcript:
{transcript}"""


# ─────────────────────────────────────────────
# NVIDIA NIM API (primary)
# ─────────────────────────────────────────────

def _call_nvidia_api(transcript: str, api_key: str) -> dict:
    """Call NVIDIA NIM endpoint via the OpenAI-compatible SDK."""
    from openai import OpenAI
    
    if not api_key or not api_key.strip():
        raise ValueError(
            "NVIDIA_API_KEY is missing or empty. "
            "Please configure it in Streamlit secrets or .env file."
        )

    client = OpenAI(
        base_url="https://integrate.api.nvidia.com/v1",
        api_key=api_key,
    )

    user_msg = USER_PROMPT_TEMPLATE.format(transcript=transcript)

    try:
        response = client.chat.completions.create(
            model="meta/llama-3.1-70b-instruct",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.1,
            max_tokens=2048,
        )
    except Exception as e:
        error_msg = str(e)
        if "401" in error_msg or "Unauthorized" in error_msg:
            raise ValueError(
                "NVIDIA API key is invalid or expired. "
                "Please check your API key at build.nvidia.com"
            )
        elif "429" in error_msg:
            raise ValueError(
                "NVIDIA API rate limit exceeded. Please wait a moment and try again."
            )
        else:
            raise ValueError(f"NVIDIA API error: {error_msg}")

    raw = response.choices[0].message.content
    return _parse_llm_response(raw)


# ─────────────────────────────────────────────
# HuggingFace Transformers fallback (local)
# ─────────────────────────────────────────────

@st.cache_resource(show_spinner=False)
def _load_hf_pipeline(hf_model: str = "mistralai/Mistral-7B-Instruct-v0.3"):
    """Load and cache a HuggingFace text-generation pipeline."""
    try:
        from transformers import pipeline
        pipe = pipeline(
            "text-generation",
            model=hf_model,
            max_new_tokens=1024,
            temperature=0.2,
            do_sample=True,
            trust_remote_code=True,
        )
        return pipe
    except Exception as e:
        st.warning(f"⚠️ HuggingFace pipeline failed to load: {e}")
        return None


def _call_hf_pipeline(transcript: str, hf_model: str) -> dict:
    """Run local HF text-generation pipeline."""
    pipe = _load_hf_pipeline(hf_model)
    if pipe is None:
        raise RuntimeError("No LLM backend available. Provide an NVIDIA API key or install transformers.")

    prompt = f"<s>[INST] {SYSTEM_PROMPT}\n\n{USER_PROMPT_TEMPLATE.format(transcript=transcript)} [/INST]"
    result = pipe(prompt)
    raw = result[0]["generated_text"]

    # Strip the prompt from the response if present
    if "[/INST]" in raw:
        raw = raw.split("[/INST]", 1)[-1].strip()

    return _parse_llm_response(raw)


# ─────────────────────────────────────────────
# Response parser
# ─────────────────────────────────────────────

def _parse_llm_response(raw: str) -> dict:
    """Extract and validate JSON from raw LLM output."""
    cleaned = extract_json_block(raw)
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"LLM returned invalid JSON.\n\nRaw response:\n{raw}\n\nError: {e}"
        )

    # Validate / normalise structure
    if "summary" not in data:
        data["summary"] = "No summary generated."
    if "decisions" not in data or not isinstance(data["decisions"], list):
        data["decisions"] = []
    if "actions" not in data or not isinstance(data["actions"], list):
        data["actions"] = []

    # Normalise action items
    for action in data["actions"]:
        action.setdefault("task", "Unspecified task")
        action.setdefault("owner", "Unassigned")
        action.setdefault("priority", "Medium")
        action.setdefault("deadline", None)
        # Normalise priority capitalisation
        action["priority"] = action["priority"].capitalize()
        if action["priority"] not in ("High", "Medium", "Low"):
            action["priority"] = "Medium"

    return data


# ─────────────────────────────────────────────
# Long transcript handler (chunking + merging)
# ─────────────────────────────────────────────

def _merge_chunk_results(results: list[dict]) -> dict:
    """Merge multiple chunk results into a single coherent insights dict."""
    merged_summary_parts = []
    merged_decisions = []
    merged_actions = []

    for r in results:
        if r.get("summary"):
            merged_summary_parts.append(r["summary"])
        merged_decisions.extend(r.get("decisions", []))
        merged_actions.extend(r.get("actions", []))

    # Deduplicate decisions (case-insensitive)
    seen = set()
    deduped_decisions = []
    for d in merged_decisions:
        key = d.strip().lower()
        if key not in seen:
            seen.add(key)
            deduped_decisions.append(d)

    return {
        "summary": " ".join(merged_summary_parts),
        "decisions": deduped_decisions,
        "actions": merged_actions,
    }


# ─────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────

def generate_meeting_insights(
    transcript: str,
    nvidia_api_key: str = "",
    hf_model: str = "mistralai/Mistral-7B-Instruct-v0.3",
) -> dict:
    """
    Analyze a (possibly long) transcript and return structured meeting insights.

    Parameters
    ----------
    transcript : str
        Full meeting transcript text.
    nvidia_api_key : str
        NVIDIA NIM API key. If empty, falls back to HuggingFace.
    hf_model : str
        HuggingFace model ID for local fallback.

    Returns
    -------
    dict
        {"summary": str, "decisions": list[str], "actions": list[dict]}
    """
    # Llama 3.1 70B supports 128K context length. Expand from 1.8k words to 25k words 
    # to process almost any meeting globally in one shot without losing fragmented context.
    chunks = chunk_text(transcript, max_words=25000)
    results = []

    for i, chunk in enumerate(chunks):
        if nvidia_api_key.strip():
            result = _call_nvidia_api(chunk, nvidia_api_key.strip())
        else:
            result = _call_hf_pipeline(chunk, hf_model)
        results.append(result)

    if len(results) == 1:
        return results[0]

    return _merge_chunk_results(results)
