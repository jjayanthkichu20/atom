# Atom Premier — Executive AI Career Co-Pilot

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

A luxury AI-powered job application co-pilot built with Flask + SQLite + OpenAI GPT-4o.  
Live clone of [JobAlchemy Atom](https://atom.jobalchemy.ai) with a bespoke dark-gold luxury UI.

## ✨ Features

- 🤖 **AI Career Co-Pilot** — GPT-4o-mini powered chat (fallback agent if credits exhausted)
- 📄 **CV Upload** — PDF, DOCX, TXT parsing with automatic skill extraction & match recalibration
- 💎 **Luxury Dark UI** — Cinzel fonts, gold accents, holographic orb, glassmorphism cards
- 🏛️ **SQLite Database** — All applications, messages, jobs & profiles persist across sessions
- 🛡️ **Human-in-the-Loop** — Review every application before it's committed to the database
- 📥 **PDF Resume Generator** — ATS-optimised executive dossier download per job
- ⚡ **4 Curated Jobs** — Stripe, Linear, Anthropic, Vercel (recalibrated after CV upload)

## 🚀 Quick Start (Local)

```bash
# 1. Clone
git clone https://github.com/<YOUR_USERNAME>/atom.git
cd atom

# 2. Install dependencies
pip install flask requests pypdf python-docx reportlab

# 3. Set your OpenAI key (optional — fallback agent works without it)
copy .env.example .env
# Edit .env and paste your key

# 4. Run
python app.py
```

Open **http://localhost:5000/chat/029c1815-a1a1-48e6-929b-1f6909f28fd5**

## 🌐 Deploy Free on Render.com

1. Fork this repo
2. Go to [render.com](https://render.com) → New → Web Service → connect your fork
3. Render auto-detects `render.yaml` — just click **Deploy**
4. Set environment variable `OPENAI_API_KEY` in Render dashboard → Environment

## 🔑 Environment Variables

| Variable | Description | Required |
|---|---|---|
| `OPENAI_API_KEY` | Your OpenAI key (`sk-proj-...`) | Optional (fallback active) |
| `GEMINI_API_KEY` | Google Gemini key (`AIzaSy...`) | Optional |
| `PORT` | Server port (default `5000`) | Optional |
| `FLASK_SECRET_KEY` | Session secret | Optional |

## 📂 Project Structure

```
atom/
├── app.py              # Flask backend — all routes & AI logic
├── database.py         # SQLite layer — all DB functions
├── templates/
│   └── index.html      # Single-page luxury UI
├── static/
│   ├── css/atom.css    # Full luxury dark theme
│   └── js/atom.js      # Frontend logic — chat, apply, CV upload
├── requirements.txt    # Python dependencies
├── render.yaml         # Render.com deployment config
└── .env.example        # Environment variable template
```

## 🛠️ API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/session/<id>` | Load session history, jobs & profile |
| POST | `/api/chat` | Send message to Atom AI |
| POST | `/api/upload-cv` | Upload & parse CV (PDF/DOCX/TXT) |
| POST | `/api/apply` | Commit job application to database |
| GET | `/api/applications` | List all tracked applications |
| GET | `/api/db-inspect` | View SQLite table counts |
| POST | `/api/verify-key` | Test API key connection |
| GET | `/api/download-cv/<job_id>` | Download ATS-formatted PDF resume |

## 📄 License

MIT — free to use, fork, and deploy.
