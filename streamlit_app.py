"""
streamlit_app.py — Entry point for Streamlit Cloud deployment.

This file redirects to app.py for Streamlit Cloud compatibility.
Streamlit Cloud looks for streamlit_app.py by default.
"""

from app import *  # noqa: F401, F403
