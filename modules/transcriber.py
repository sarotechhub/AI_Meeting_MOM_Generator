"""
transcriber.py — Audio-to-text transcription using Groq Cloud API.

Uses the ultra-fast Groq API (whisper-large-v3) compatible with the OpenAI client.
Automatically chunks large audio files to bypass 25MB API limits using bundled FFmpeg.
"""

import os
import glob
import tempfile
import subprocess
import shutil
import streamlit as st
from openai import OpenAI
from modules.utils import clean_text

# 25MB limit on API. We chunk every 10 mins (600 seconds)
CHUNK_LENGTH_SEC = "600"

def transcribe_audio(uploaded_file, api_key: str) -> str:
    """
    Transcribe an uploaded audio file using Groq's insanely fast Whisper API.
    Splits the audio into smaller chunks automatically if it is > 25MB.
    """
    if not api_key:
        raise ValueError("GROQ_API_KEY is missing. Please add it to your .env file.")

    client = OpenAI(
        api_key=api_key,
        base_url="https://api.groq.com/openai/v1"
    )

    # 1. Load the file to disk safely
    suffix = _get_suffix(uploaded_file.name)
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_in:
        tmp_in.write(uploaded_file.read())
        tmp_in_path = tmp_in.name

    try:
        # Check size before doing heavy chunking logic
        if os.path.getsize(tmp_in_path) <= 24 * 1024 * 1024:
            # Under 24MB, direct transcription
            with st.spinner("Processing directly via Groq API (Small file)..."):
                with open(tmp_in_path, "rb") as audio_file:
                    transcription = client.audio.transcriptions.create(
                        file=(uploaded_file.name, audio_file),
                        model="whisper-large-v3",
                        temperature=0.0
                    )
            raw_transcript = transcription.text
        else:
            # Over 24MB, use pure ffmpeg subprocess to chunk
            temp_dir = tempfile.mkdtemp()
            chunk_pattern = os.path.join(temp_dir, "chunk_%03d.mp3")
            
            ffmpeg_exe = "ffmpeg"
            command = [
                ffmpeg_exe,
                "-y",
                "-i", tmp_in_path,
                "-f", "segment",
                "-segment_time", CHUNK_LENGTH_SEC,
                "-c:a", "libmp3lame",
                "-b:a", "64k",
                chunk_pattern
            ]
            
            with st.spinner("Splitting large audio file instantly..."):
                subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # Find generated chunks and sort them
            chunk_files = sorted(glob.glob(os.path.join(temp_dir, "chunk_*.mp3")))
            
            full_transcript = []
            progress_bar = st.progress(0, text="Transcribing large file in chunks via Groq...")

            for i, chunk_path in enumerate(chunk_files):
                with open(chunk_path, "rb") as audio_file:
                    transcription = client.audio.transcriptions.create(
                        file=(f"chunk_{i}.mp3", audio_file),
                        model="whisper-large-v3",
                        temperature=0.0
                    )
                    full_transcript.append(transcription.text)
                
                progress = min(1.0, (i + 1) / len(chunk_files))
                progress_bar.progress(progress, text=f"Transcribed {i+1} of {len(chunk_files)} segments...")
                
            progress_bar.empty()
            raw_transcript = " ".join(full_transcript)
            
            # Cleanup chunk directory
            shutil.rmtree(temp_dir, ignore_errors=True)

    except Exception as e:
        raise RuntimeError(f"Audio processing failed: {e}")

    finally:
        if os.path.exists(tmp_in_path):
            try:
                os.remove(tmp_in_path)
            except OSError:
                pass

    return clean_text(raw_transcript)


def _get_suffix(filename: str) -> str:
    """Extract file extension from a filename."""
    _, ext = os.path.splitext(filename)
    return ext if ext else ".mp3"
