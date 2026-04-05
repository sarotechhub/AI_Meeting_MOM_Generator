"""
app.py — AI Meeting Auto MOM Generator
Main Streamlit application entry point.
"""

import json
import os
import time

import streamlit as st
from dotenv import load_dotenv

from modules.action_extractor import enrich_actions
from modules.llm_engine import generate_meeting_insights
from modules.pdf_exporter import export_pdf
from modules.transcriber import transcribe_audio
from modules.utils import (
    clean_text,
    format_timestamp,
    highlight_names_in_text,
    priority_badge_html,
    priority_color,
    slug_timestamp,
)

# ─────────────────────────────────────────────
# Environment
# ─────────────────────────────────────────────
load_dotenv()

# ─────────────────────────────────────────────
# Page config (MUST be first Streamlit call)
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="AI Meeting MOM Generator",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded",   # sidebar always open on load
)

# ─────────────────────────────────────────────
# Session-state defaults
# ─────────────────────────────────────────────
def _init_session():
    defaults = {
        "transcript": "",
        "insights": None,
        "detected_names": [],
        "dark_mode": False,
        "processing": False,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

_init_session()

# ─────────────────────────────────────────────
# CSS — Premium dark/light theme
# ─────────────────────────────────────────────
DARK_BG = "#0f0e17"
DARK_CARD = "#1c1b2e"
DARK_BORDER = "#2d2b55"
DARK_TEXT = "#e2e0ff"
DARK_MUTED = "#9090b8"
LIGHT_BG = "#f8f7ff"
LIGHT_CARD = "#ffffff"
LIGHT_BORDER = "#e0dff8"
LIGHT_TEXT = "#1e1b4b"
LIGHT_MUTED = "#6b7280"


def _inject_css(dark: bool):
    bg = DARK_BG if dark else LIGHT_BG
    card = DARK_CARD if dark else LIGHT_CARD
    border = DARK_BORDER if dark else LIGHT_BORDER
    text = DARK_TEXT if dark else LIGHT_TEXT
    muted = DARK_MUTED if dark else LIGHT_MUTED
    input_bg = "#16152a" if dark else "#f1f0fa"

    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

        /* ── Global reset ── */
        html, body, [class*="css"] {{
            font-family: 'Inter', sans-serif !important;
            background-color: {bg} !important;
            color: {text} !important;
        }}
        .stApp {{ background-color: {bg} !important; }}

        /* ── Sidebar ── */
        section[data-testid="stSidebar"] {{
            background-color: {card} !important;
            border-right: 1px solid {border};
        }}
        section[data-testid="stSidebar"] * {{
            color: {text} !important;
        }}

        /* ── Main content padding ── */
        .main .block-container {{
            padding: 1.8rem 2.5rem 3rem 2.5rem;
            max-width: 1200px;
        }}

        /* ── Card component ── */
        .mom-card {{
            background: {card};
            border: 1px solid {border};
            border-radius: 16px;
            padding: 1.5rem 1.8rem;
            margin-bottom: 1.2rem;
            box-shadow: 0 4px 24px rgba(99,102,241,0.07);
            transition: box-shadow 0.2s ease;
        }}
        .mom-card:hover {{
            box-shadow: 0 8px 32px rgba(99,102,241,0.15);
        }}

        /* ── Section headings ── */
        .mom-section-title {{
            font-size: 1rem;
            font-weight: 700;
            color: #6366f1;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-bottom: 0.8rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}

        /* ── Hero header ── */
        .mom-hero {{
            background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 50%, #2563eb 100%);
            border-radius: 20px;
            padding: 2.5rem 2rem;
            margin-bottom: 2rem;
            text-align: center;
            position: relative;
            overflow: hidden;
        }}
        .mom-hero::before {{
            content: '';
            position: absolute;
            top: -50%; left: -50%;
            width: 200%; height: 200%;
            background: radial-gradient(circle, rgba(255,255,255,0.05) 0%, transparent 60%);
            animation: pulse-bg 4s ease-in-out infinite;
        }}
        @keyframes pulse-bg {{
            0%, 100% {{ transform: scale(1); opacity: 0.5; }}
            50% {{ transform: scale(1.1); opacity: 1; }}
        }}
        .mom-hero h1 {{
            font-size: 2.2rem;
            font-weight: 800;
            color: white !important;
            margin: 0 0 0.4rem 0;
            letter-spacing: -0.02em;
        }}
        .mom-hero p {{
            color: rgba(255,255,255,0.8) !important;
            font-size: 1rem;
            margin: 0;
        }}

        /* ── Action item cards ── */
        .action-card {{
            background: {card};
            border: 1px solid {border};
            border-left: 4px solid;
            border-radius: 10px;
            padding: 1rem 1.2rem;
            margin-bottom: 0.75rem;
            transition: transform 0.15s ease;
        }}
        .action-card:hover {{
            transform: translateX(3px);
        }}
        .action-meta {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.6rem;
            margin-top: 0.5rem;
            align-items: center;
        }}
        .meta-chip {{
            background: {input_bg};
            border: 1px solid {border};
            border-radius: 20px;
            padding: 2px 10px;
            font-size: 0.78rem;
            color: {muted};
            font-weight: 500;
        }}

        /* ── Decision items ── */
        .decision-item {{
            display: flex;
            gap: 0.75rem;
            align-items: flex-start;
            padding: 0.6rem 0;
            border-bottom: 1px solid {border};
            color: {text};
            font-size: 0.95rem;
        }}
        .decision-item:last-child {{ border-bottom: none; }}
        .decision-dot {{
            width: 8px; height: 8px;
            background: #6366f1;
            border-radius: 50%;
            margin-top: 6px;
            flex-shrink: 0;
        }}

        /* ── Transcript ── */
        .stTextArea textarea {{
            font-family: 'JetBrains Mono', monospace !important;
            font-size: 0.85rem !important;
            background-color: {input_bg} !important;
            color: {text} !important;
            border: 1px solid {border} !important;
            border-radius: 10px !important;
        }}

        /* ── Buttons ── */
        .stButton > button {{
            background: linear-gradient(135deg, #6366f1, #7c3aed) !important;
            color: white !important;
            border: none !important;
            border-radius: 10px !important;
            padding: 0.6rem 1.8rem !important;
            font-weight: 600 !important;
            font-size: 0.95rem !important;
            letter-spacing: 0.01em !important;
            transition: all 0.2s ease !important;
            box-shadow: 0 4px 16px rgba(99,102,241,0.35) !important;
        }}
        .stButton > button:hover {{
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 24px rgba(99,102,241,0.5) !important;
        }}
        .stButton > button:active {{
            transform: translateY(0) !important;
        }}

        /* ── Download buttons ── */
        .stDownloadButton > button {{
            background: transparent !important;
            color: #6366f1 !important;
            border: 1.5px solid #6366f1 !important;
            border-radius: 10px !important;
            font-weight: 600 !important;
            transition: all 0.2s ease !important;
        }}
        .stDownloadButton > button:hover {{
            background: rgba(99,102,241,0.1) !important;
            transform: translateY(-1px) !important;
        }}

        /* ── Expander ── */
        .streamlit-expanderHeader {{
            background: {card} !important;
            border-radius: 10px !important;
            color: {text} !important;
            font-weight: 600 !important;
        }}

        /* ── Metrics ── */
        [data-testid="stMetricValue"] {{
            font-size: 2rem !important;
            font-weight: 700 !important;
            color: #6366f1 !important;
        }}
        [data-testid="stMetricLabel"] {{
            color: {muted} !important;
            font-size: 0.8rem !important;
        }}

        /* ── File uploader ── */
        [data-testid="stFileUploader"] {{
            background: {input_bg} !important;
            border: 1.5px dashed {border} !important;
            border-radius: 12px !important;
            padding: 1rem !important;
        }}

        /* ── Spinner ── */
        .stSpinner > div {{ border-top-color: #6366f1 !important; }}

        /* ── Info/success/warning boxes ── */
        .stInfo {{ background: rgba(99,102,241,0.1) !important; border-left-color: #6366f1 !important; }}

        /* ── Scrollbar ── */
        ::-webkit-scrollbar {{ width: 6px; height: 6px; }}
        ::-webkit-scrollbar-track {{ background: transparent; }}
        ::-webkit-scrollbar-thumb {{ background: {border}; border-radius: 3px; }}

        /* ── Divider ── */
        hr {{ border-color: {border} !important; }}

        /* ── Hide Streamlit footer branding ── */
        footer {{ visibility: hidden; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────
# UI Components
# ─────────────────────────────────────────────

def render_hero():
    st.markdown(
        """
        <div class="mom-hero">
            <h1>🎙️ AI Meeting MOM Generator</h1>
            <p>Transform any meeting transcript or audio into structured Minutes of Meeting — instantly.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar() -> dict:
    """Render sidebar controls and return config dict."""
    with st.sidebar:
        st.markdown("## ⚙️ Configuration")
        st.divider()

        # Dark / light mode
        dark_mode = st.toggle("🌙 Dark Mode", value=st.session_state.dark_mode)
        if dark_mode != st.session_state.dark_mode:
            st.session_state.dark_mode = dark_mode
            st.rerun()

        st.divider()
        st.markdown("### 📘 About")
        st.info(
            "**AI Meeting MOM Generator** uses Groq (Whisper-Large) for transcription, "
            "NVIDIA LLaMA-3.1 for insight extraction, and spaCy for name detection.\n\n"
            "No data is stored server-side.",
            icon="ℹ️",
        )
        
        st.markdown(
            """
            <div style="margin-top: 2rem; text-align: center; color: #a1a1aa; font-size: 0.85rem;">
                Built by <strong>Saravanakumar</strong>
            </div>
            """, 
            unsafe_allow_html=True
        )

    return {
        "dark_mode": dark_mode,
    }


def render_input_section():
    """Render the input area and populate st.session_state.transcript."""
    st.markdown("## 📥 Input")

    tab_audio, tab_txt, tab_manual = st.tabs(
        ["🎵 Audio File", "📄 Text File", "✏️ Manual Input"]
    )

    # ── Audio Upload ──
    with tab_audio:
        uploaded_audio = st.file_uploader(
            "Upload an audio recording",
            type=["mp3", "wav", "m4a", "ogg", "flac"],
            help="Supports MP3, WAV, M4A, OGG, FLAC",
        )
        if uploaded_audio:
            st.audio(uploaded_audio)
            if st.button("🎙️ Transcribe Audio", key="btn_transcribe"):
                groq_key = os.getenv("GROQ_API_KEY", "").strip()
                if not groq_key:
                    st.error("❌ Groq API key is missing! Add `GROQ_API_KEY=xxx` to your .env file.")
                else:
                    try:
                        transcript = transcribe_audio(uploaded_audio, api_key=groq_key)
                        st.session_state.transcript = transcript
                        st.success("✅ Transcription complete!")
                    except Exception as e:
                        st.error(f"Transcription failed: {e}")

    # ── Text File Upload ──
    with tab_txt:
        uploaded_txt = st.file_uploader(
            "Upload a .txt transcript",
            type=["txt"],
            key="txt_uploader",
        )
        if uploaded_txt:
            raw = uploaded_txt.read().decode("utf-8", errors="replace")
            st.session_state.transcript = clean_text(raw)
            st.success(f"✅ Loaded {len(raw.split())} words from file.")

    # ── Manual Input ──
    with tab_manual:
        manual_text = st.text_area(
            "Paste or type your transcript here",
            height=200,
            placeholder="John: Let's start the meeting. Sarah, can you share the Q3 numbers?...",
            key="manual_textarea",
        )
        if st.button("📋 Use This Text", key="btn_use_manual"):
            if manual_text.strip():
                st.session_state.transcript = clean_text(manual_text)
                st.success("✅ Transcript saved.")
            else:
                st.warning("Please enter some text.")


def render_transcript_viewer():
    """Display transcript in an editable text area."""
    if not st.session_state.transcript:
        return

    st.markdown("---")
    st.markdown("## 📝 Transcript")

    col_info, col_stats = st.columns([3, 1])
    with col_info:
        st.caption("Edit the transcript below before generating insights.")
    with col_stats:
        word_count = len(st.session_state.transcript.split())
        st.caption(f"**{word_count:,}** words")

    edited = st.text_area(
        "transcript_editor",
        value=st.session_state.transcript,
        height=280,
        label_visibility="collapsed",
        key="transcript_editor_area",
    )
    # Keep session in sync with edits
    if edited != st.session_state.transcript:
        st.session_state.transcript = edited

    # Name highlights preview
    if st.session_state.detected_names:
        with st.expander("👥 Detected People in Transcript", expanded=False):
            names_html = " &nbsp; ".join(
                f"<strong style='color:#6366f1'>👤 {n}</strong>"
                for n in st.session_state.detected_names
            )
            st.markdown(names_html, unsafe_allow_html=True)


def render_generate_button() -> bool:
    """Render the generate button. Returns True if clicked."""
    if not st.session_state.transcript:
        return False

    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        clicked = st.button(
            "✨ Generate Meeting Insights",
            use_container_width=True,
            key="btn_generate",
        )
    return clicked


def render_insights_dashboard(insights: dict, transcript: str):
    """Render the full results dashboard."""
    st.markdown("---")
    st.markdown("## 📊 Meeting Intelligence Dashboard")

    # ── Metrics strip ──────────────────────────────────
    decisions = insights.get("decisions", [])
    actions = insights.get("actions", [])
    owners = {a.get("owner", "Unassigned") for a in actions if a.get("owner") != "Unassigned"}
    high_priority = sum(1 for a in actions if a.get("priority", "").lower() == "high")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("📋 Decisions", len(decisions))
    m2.metric("🎯 Action Items", len(actions))
    m3.metric("👥 Owners", len(owners))
    m4.metric("🔴 High Priority", high_priority)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Summary card ──────────────────────────────────
    summary_html = insights.get("summary", "No summary generated.").replace("\n", "<br>")
    st.markdown(
        f"""
        <div class='mom-card'>
            <div class='mom-section-title'>📋 Meeting Summary</div>
            <div style='line-height:1.75; margin:0; font-size:0.97rem;'>
                {summary_html}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Two-column: Decisions + Action Items ───────────
    col_left, col_right = st.columns([1, 1], gap="large")

    with col_left:
        st.markdown(
            "<div class='mom-section-title'>✅ Key Decisions</div>",
            unsafe_allow_html=True,
        )
        if decisions:
            items_html = "".join(
                f"<div class='decision-item'>"
                f"<div class='decision-dot'></div>"
                f"<span>{d}</span>"
                f"</div>"
                for d in decisions
            )
            st.markdown(
                f"<div class='mom-card'>{items_html}</div>",
                unsafe_allow_html=True,
            )
        else:
            st.info("No key decisions were extracted.")

    with col_right:
        st.markdown(
            "<div class='mom-section-title'>🎯 Action Items</div>",
            unsafe_allow_html=True,
        )
        if actions:
            for action in actions:
                priority = action.get("priority", "Medium")
                border_col = priority_color(priority)
                badge = priority_badge_html(priority)
                deadline = action.get("deadline") or "No deadline"
                owner = action.get("owner", "Unassigned")
                task = action.get("task", "")

                st.markdown(
                    f"""
                    <div class='action-card' style='border-left-color:{border_col};'>
                        <div style='font-weight:600; font-size:0.95rem; margin-bottom:0.3rem;'>{task}</div>
                        <div class='action-meta'>
                            {badge}
                            <span class='meta-chip'>👤 {owner}</span>
                            <span class='meta-chip'>📅 {deadline}</span>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.info("No action items were extracted.")

    # ── Action Items as Table (expandable) ────────────
    if actions:
        with st.expander("📊 View as Table", expanded=False):
            import pandas as pd
            df = pd.DataFrame(actions)
            df.columns = [c.capitalize() for c in df.columns]
            st.dataframe(df, use_container_width=True, hide_index=True)

    # ── Export section ─────────────────────────────────
    render_export_section(insights, transcript)


def render_export_section(insights: dict, transcript: str):
    """Render the export buttons row."""
    st.markdown("---")
    st.markdown("## 💾 Export Report")
    st.caption("Download the full MOM report in your preferred format.")

    slug = slug_timestamp()
    col_pdf, col_txt = st.columns(2)

    # PDF
    with col_pdf:
        try:
            pdf_bytes = export_pdf(insights)
            st.download_button(
                label="📄 Download PDF",
                data=pdf_bytes,
                file_name=f"MOM_{slug}.pdf",
                mime="application/pdf",
                use_container_width=True,
                key="dl_pdf",
            )
        except Exception as e:
            st.error(f"PDF generation failed: {e}")

    # TXT
    with col_txt:
        txt_content = _build_txt_report(insights)
        st.download_button(
            label="📝 Download TXT (Email Format)",
            data=txt_content.encode("utf-8"),
            file_name=f"MOM_{slug}.txt",
            mime="text/plain",
            use_container_width=True,
            key="dl_txt",
        )


def _build_txt_report(insights: dict) -> str:
    """Build a plain-text MOM report string formatted as an email."""
    lines = [
        "MEETING MINUTES SUMMARY",
        "",
        insights.get("summary", "No summary generated.").strip(),
        "",
    ]
    
    decisions = insights.get("decisions", [])
    if decisions:
        lines += ["KEY DECISIONS:"]
        for d in decisions:
            lines.append(f"- {d}")
        lines.append("")

    actions = insights.get("actions", [])
    if actions:
        lines += ["ACTION ITEMS:"]
        for a in actions:
            dead = a.get("deadline") or "N/A"
            lines.append(
                f"- {a.get('task','')} (Owner: {a.get('owner','Unassigned')} | Deadline: {dead})"
            )
        
    return "\n".join(lines)


# ─────────────────────────────────────────────
# Main orchestration
# ─────────────────────────────────────────────

def main():
    config = render_sidebar()
    _inject_css(config["dark_mode"])
    render_hero()
    render_input_section()
    render_transcript_viewer()

    # API key loaded silently from environment — never exposed in UI
    nvidia_key = os.getenv("NVIDIA_API_KEY", "").strip()

    if render_generate_button():
        with st.spinner("🧠 Analyzing transcript with AI... please wait"):
            try:
                t0 = time.time()
                raw_insights = generate_meeting_insights(
                    st.session_state.transcript,
                    nvidia_api_key=nvidia_key,
                )
                enriched_actions, detected_names = enrich_actions(
                    raw_insights.get("actions", []),
                    st.session_state.transcript,
                )
                raw_insights["actions"] = enriched_actions
                st.session_state.insights = raw_insights
                st.session_state.detected_names = detected_names
                elapsed = time.time() - t0
                st.success(f"✅ Insights generated in {elapsed:.1f}s")
            except Exception as e:
                st.error(f"❌ Generation failed: {e}")
                st.exception(e)

    if st.session_state.insights:
        render_insights_dashboard(
            st.session_state.insights,
            st.session_state.transcript,
        )


if __name__ == "__main__":
    main()
