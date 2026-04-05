# 🎙️ AI Meeting Auto MOM Generator

> **Transform any meeting audio or transcript into structured Minutes of Meeting — instantly.**
> Powered by Groq, NVIDIA LLaMA-3.1, and spaCy.

---

## ✨ Features

| Feature | Details |
|---|---|
| 🎵 **Ultra-Fast Transcription** | Upload MP3, WAV, M4A → Transcribed in seconds via **Groq Whisper-Large-v3 API** |
| 📄 **Text Input** | Upload `.txt` file or paste transcript manually |
| 🤖 **AI Insight Extraction** | Summary, Key Decisions, Action Items (owner, priority, deadline) using **NVIDIA Llama 3.1 70B** |
| 👥 **Smart Name Detection** | spaCy NER identifies people and maps them to action items |
| 🎨 **Premium UI** | Dark/Light mode, color-coded priority cards, metrics dashboard |
| 📧 **Export for Email** | Download an email-ready **TXT** or nicely styled **PDF** report |

---

## 🚀 Quick Start

### 1. Clone / Navigate to the project

```bash
cd "AI Meeting Auto MOM Generator"
```

### 2. Create a virtual environment

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure API keys

```bash
# Copy the example env file
cp .env.example .env

# Edit .env and supply your Keys:
# GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxx
# NVIDIA_API_KEY=nvapi-xxxxxxxxxxxxxxxx
```

- Get your **free** Groq API key at: [console.groq.com](https://console.groq.com)
- Get your **free** NVIDIA API key at: [build.nvidia.com](https://build.nvidia.com)

### 5. Run the app

```bash
# Local development
streamlit run app.py

# Or use the Cloud-compatible entry point
streamlit run streamlit_app.py
```

The app opens at **http://localhost:8501** 🎉

---

## ☁️ Deployment to Streamlit Cloud

See **[DEPLOYMENT.md](./DEPLOYMENT.md)** for complete step-by-step instructions.

**Quick deploy:**
1. Push code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Deploy from your repo (main file: `streamlit_app.py`)  
4. Add API keys via Secrets settings

---

## 🗂️ Project Structure

```
ai_meeting_assistant/
│
    ├── app.py                    # Main Streamlit application
    ├── modules/
    │   ├── __init__.py
    │   ├── transcriber.py        # Audio → text (Groq Cloud API)
    │   ├── llm_engine.py         # LLM insight extraction (NVIDIA NIM)
    │   ├── action_extractor.py   # spaCy NER + action enrichment
    │   ├── pdf_exporter.py       # ReportLab PDF generation
    │   └── utils.py              # Shared helpers
    │
    ├── .streamlit/
    │   └── config.toml           # Streamlit native theme configuration
    ├── packages.txt              # Cloud deployment dependencies (ffmpeg)
    ├── .env.example              # API key template
    ├── .gitignore                # Protects secrets from being pushed
    ├── requirements.txt          # Python deployment dependencies
    └── README.md
```

---

## 🔑 Required API Keys

### Groq API (Audio Transcription)
- Handles 30-minute meeting audio in seconds.
- Free tier available at: [console.groq.com](https://console.groq.com)
- Model used: `whisper-large-v3`

### NVIDIA NIM (Meeting Insight Extraction)
- Extremely accurate 128k context window Llama model.
- Free tier available at [build.nvidia.com](https://build.nvidia.com)
- Model used: `meta/llama-3.1-70b-instruct`

Both keys must be configured securely via the `.env` file for local development.

---

## 📋 Output Format

The AI returns a structured JSON as:

```json
{
  "summary": "Clear 2-4 sentence paragraph of the meeting...",
  "decisions": [
    "Approved the Q3 budget of $500K",
    "Agreed to launch beta in July"
  ],
  "actions": [
    {
      "task": "Send updated roadmap to stakeholders",
      "owner": "Sarah",
      "priority": "High",
      "deadline": "by Friday"
    }
  ]
}
```

---

## 🧠 Architecture

```
Audio Input                      Text Input
      │                              │
      ▼                              │
┌─────────────────┐                  │
│   Groq Cloud    │                  │
│  (Transcriber)  │                  │
└─────────────────┘                  │
         │                           │
         ▼                           ▼
      ┌────────────────────────────────┐
      │        Clean Transcript        │
      │        (editable UI)           │
      └──────────────┬─────────────────┘
                     │
                     ▼
        ┌────────────────────────┐
        │  NVIDIA NIM LLaMA-3.1  │
        │  (70B Parameter Model) │
        └────────────┬───────────┘
                     │
        ┌────────────▼───────────┐
        │   Action Extractor     │
        │   (spaCy NER + match)  │
        └────────────┬───────────┘
                     │
  ┌──────────────────▼──────────────────┐
  │         Results Dashboard            │
  │  Summary │ Decisions │ Action Items  │
  └──────────────────┬──────────────────┘
                     │
        ┌────────────▼───────────┐
        │    Export: PDF / TXT    │
        └────────────────────────┘
```

---

## 🎨 Priority Color Coding

| Priority | Color |
|---|---|
| 🔴 High | `#ef4444` Red |
| 🟠 Medium | `#f97316` Orange |
| 🟢 Low | `#22c55e` Green |

---

## 🔧 Configuration Options

| Setting | Options | Default |
|---|---|---|
| Theme | Dark / Light dropdown toggle | Light |

---

## ☁️ Deployment (Streamlit Community Cloud)

This app is fully production-ready and incredibly lightweight for deployment on [Streamlit Community Cloud](https://share.streamlit.io).

1. Push this entire repository to your GitHub account (the included `.gitignore` will ensure your local `.env` keys naturally stay hidden).
2. Go to **Streamlit Community Cloud** and deploy a new app from your GitHub repository.
3. Before you hit Deploy, click on **Advanced Settings** and add your Keys into the **Secrets** box formatted exactly like this:

```toml
GROQ_API_KEY="gsk_xxxxxxxxxxxxxxxx"
NVIDIA_API_KEY="nvapi-xxxxxxxxxxxxxx"
```

4. Streamlit will securely load these into your app as environment variables dynamically.

---

## 📦 Dependencies

| Package | Purpose |
|---|---|
| `streamlit` | Web UI framework |
| `openai` | Universal API client for Groq and NVIDIA |
| `spacy` | Named Entity Recognition |
| `reportlab` | PDF generation |
| `python-dotenv` | Environment variable loading |
| `pandas` | Table display |

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -m 'Add my feature'`
4. Push: `git push origin feature/my-feature`
5. Open a Pull Request

---

## 📄 License

MIT License — free to use, modify, and distribute.

---

*Built with ❤️ using Streamlit · Whisper · NVIDIA NIM · spaCy*
# AI_Meeting_MOM_Generator
