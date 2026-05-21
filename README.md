# QuizPrep — AI-Powered Interview Quiz Platform

Practice interview questions generated from your own study materials using AI.

## Architecture

```
Frontend (GitHub Pages)  ───►  Backend API (Render)  ───►  Google Gemini AI
    HTML/CSS/JS                    FastAPI/Python              Free Tier
```

## Tech Stack

- **Frontend**: Vanilla HTML/CSS/JS on GitHub Pages
- **Backend**: Python FastAPI on Render (free tier)
- **Database**: PostgreSQL on Neon (free tier) or SQLite (local dev)
- **AI**: Google Gemini 2.5 Flash API (free tier, no credit card)

## Setup

### 1. Prerequisites
- Python 3.10+
- Google Gemini API key (get from [Google AI Studio](https://aistudio.google.com/) — free, no credit card)

### 2. Local Development

```bash
# Backend
cd backend
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your Gemini API key
python -m uvicorn main:app --reload

# Frontend
# Serve frontend/ directory with any static server
# e.g., python -m http.server 5500 -d ../frontend
```

### 3. Deploy Backend (Render)

1. Push code to GitHub
2. Connect repo to [Render](https://render.com) (free, no credit card)
3. Create a new **Web Service** → select your repo
4. Set:
   - **Root Directory**: `backend`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables (see `.env.example`)
6. Create a **PostgreSQL database** on Render (free for 90 days) or use [Neon](https://neon.tech) (free forever)

### 4. Deploy Frontend (GitHub Pages)

1. In your GitHub repo → Settings → Pages → Source: **GitHub Actions**
2. Push changes to `main` — the included workflow auto-deploys `frontend/` to Pages
3. Your site will be at `https://your-username.github.io/quiz-prep`

### 5. Connect Frontend to Backend

Edit `frontend/js/api.js` and change `API_BASE`:
- Local: `http://localhost:8000`
- Production: `https://your-app.onrender.com`

## Features

- ✅ Login/Registration with JWT + refresh tokens
- ✅ Guest mode (no account needed)
- ✅ Upload PDF, DOCX, TXT files
- ✅ Domain verification against document content
- ✅ AI-generated MCQs (10 or 20 questions)
- ✅ Optional 2 long-answer questions
- ✅ 30s timer per MCQ, 2min per long question
- ✅ AI evaluation of long answers
- ✅ Section-wise performance breakdown
- ✅ Pass/Fail with custom passing percentage
- ✅ Quiz history dashboard with score trends
- ✅ Auto-login with "Remember Me"
- ✅ Dark/light mode
- ✅ Mobile-responsive
- ✅ Confetti on pass, encouragement on fail
