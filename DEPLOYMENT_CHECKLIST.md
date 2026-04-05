# 🚀 Streamlit Cloud Deployment Checklist

Use this checklist before deploying to Streamlit Cloud.

## Pre-Deployment (Local Testing)

- [ ] **Python 3.8+** installed (`python --version`)
- [ ] **Virtual environment** created (`python -m venv .venv`)
- [ ] **Dependencies installed** (`pip install -r requirements.txt`)
- [ ] **API keys configured** in `.env` file
  - [ ] `GROQ_API_KEY` added from [console.groq.com](https://console.groq.com)
  - [ ] `NVIDIA_API_KEY` added from [build.nvidia.com](https://build.nvidia.com)
- [ ] **App runs locally** (`streamlit run app.py`)
- [ ] **Audio transcription works** (test with a small MP3)
- [ ] **PDF export works** (generate and download)

## GitHub Setup

- [ ] **Repository created** on GitHub
- [ ] **Code pushed** to main branch
- [ ] **`.env` is NOT committed** (verify via `git status`)
- [ ] **`.gitignore` includes `.env`** (prevents secrets leak)

## Streamlit Cloud Setup

- [ ] **Streamlit account** created at [share.streamlit.io](https://share.streamlit.io)
- [ ] **GitHub connected** to Streamlit Cloud
- [ ] **Repository selected** for deployment

## Deployment Configuration

- [ ] **Main file set to**: `streamlit_app.py`
- [ ] **Branch set to**: `main` (or your primary branch)
- [ ] **Secrets added**: Click gear icon → **Manage secrets**
  ```toml
  GROQ_API_KEY = "gsk_your_actual_key_here"
  NVIDIA_API_KEY = "nvapi_your_actual_key_here"
  ```
- [ ] **Secrets saved** and app restarted

## Post-Deployment Testing

- [ ] **App loads** without errors
- [ ] **Sidebar renders** correctly
- [ ] **Input section** accepts audio/text
- [ ] **Generate button** appears and responds
- [ ] **PDF export** button works and downloads file
- [ ] **No 404 errors** (check browser console)
- [ ] **No red error boxes** on UI

## Common Issues & Fixes

| Issue | Solution |
|-------|----------|
| "Module not found: spacy" | Reinstall: `pip install spacy` |
| "File not found: streamlit_app.py" | Make sure `streamlit_app.py` exists in repo root |
| "API keys missing" | Check secrets are added in Streamlit settings |
| "FFmpeg not found" | System FFmpeg is provided; `packages.txt` has `ffmpeg` |
| "Audio not transcribing" | Check GROQ_API_KEY in secrets is valid |
| "Insights not generating" | Check NVIDIA_API_KEY in secrets is valid |
| "spaCy model not found" | App auto-downloads on first run; may take 30 seconds |
| "PDF export fails" | Ensure reportlab is installed (in requirements.txt) |

## Useful Commands

```bash
# Test if dependencies load
python -c "import streamlit; import spacy; import openai; print('✅ All imports OK')"

# Validate Python syntax
python -m py_compile app.py modules/*.py

# Check file sizes (Cloud limit: ~1GB total)
du -sh .

# View Streamlit logs locally
streamlit run app.py --logger.level=debug
```

## Important Notes

- **Secrets are private**: Never commit `.env` file
- **Free tier limits**:
  - Groq: ~100 req/min, ~10 hrs audio/day
  - NVIDIA: ~100 req/min, 128K context
- **Timeout**: Streamlit Cloud reconnects after 30 mins of inactivity (normal)
- **File uploads**: Max 500MB per file (configured in `config.toml`)

## Support

- [Streamlit Docs](https://docs.streamlit.io)
- [Groq Console](https://console.groq.com)
- [NVIDIA Build](https://build.nvidia.com)
- [GitHub Issues](https://github.com/YOUR_REPO) (replace with your repo URL)

---

✅ **Ready to deploy!** Push your code and share your app link.
