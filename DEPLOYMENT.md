# 🚀 Deployment Guide for Streamlit Cloud

## Prerequisites
- Streamlit Cloud account ([streamlit.io](https://streamlit.io))
- GitHub repository with this code
- API Keys:
  - **GROQ_API_KEY** — Get from [console.groq.com](https://console.groq.com)
  - **NVIDIA_API_KEY** — Get from [build.nvidia.com](https://build.nvidia.com)

## Step 1: Push Code to GitHub

```bash
git add .
git commit -m "Prepare for Streamlit Cloud deployment"
git push origin main
```

## Step 2: Add Secrets to Streamlit Cloud

1. Go to [share.streamlit.io/settings](https://share.streamlit.io/settings)
2. Select your app from the list
3. Click **Edit secrets** (gear icon, lower right)
4. Add the following secrets:

```toml
GROQ_API_KEY = "your-groq-api-key-here"
NVIDIA_API_KEY = "your-nvidia-api-key-here"
```

5. Click **Save**

## Step 3: Deploy

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click **New app**
3. Select your GitHub repository
4. Set main file path to: `streamlit_app.py`
5. Click **Deploy**

The app will now start. Check the logs if there are any issues.

## Troubleshooting

### 📛 "Secrets not found"
- Make sure you've added `GROQ_API_KEY` and `NVIDIA_API_KEY` in Streamlit secrets
- Restart the app after adding secrets

### 📦 "Module not found"
- Check that all dependencies in `requirements.txt` are compatible
- Wait 2-3 minutes after deployment for dependencies to fully install

### 🎙️ "Audio transcription fails"
- Verify your GROQ_API_KEY is valid
- Check that you have sufficient Groq API quota
- Ensure audio file format is one of: MP3, WAV, M4A, OGG, FLAC

### 🤖 "AI insights generation fails"
- Verify your NVIDIA_API_KEY is valid
- Check your NVIDIA API quota/limits
- The app will automatically fall back to local LLM if NVIDIA fails (slower)

## API Key Limits

**GROQ** (Free tier):
- 100 requests per minute
- ~10 hours of audio per day

**NVIDIA** (Free tier):
- 100 requests per minute
- 128K context limit

Consider upgrading if you hit these limits.
