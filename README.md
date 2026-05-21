# QuizPrep — AI-Powered Interview Quiz Platform

Practice interview questions generated from your own study materials using AI.

🌐 **Live**: https://ravijeetchandra.github.io/quiz-app-interview/

---

## Architecture

```
Frontend (GitHub Pages)  ───►  Backend API (Render)  ───►  Groq AI (Llama 3.1 8B)
    HTML/CSS/JS                    FastAPI/Python              Free Tier
```

## Tech Stack

- **Frontend**: Vanilla HTML/CSS/JS on GitHub Pages
- **Backend**: Python FastAPI on Render (free tier)
- **Database**: PostgreSQL on Neon (free tier) or SQLite (local dev)
- **AI**: Groq API — Llama 3.1 8B (free tier, no credit card)
- **Auth**: JWT access + refresh tokens with bcrypt

## Features

- ✅ Login/Registration with JWT + refresh tokens
- ✅ Guest mode (no account needed)
- ✅ Forgot / reset password flow
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

## Live URLs

| Service | URL |
|---------|-----|
| Frontend | https://ravijeetchandra.github.io/quiz-app-interview |
| Backend API | https://quiz-prep-api.onrender.com |
| Health Check | https://quiz-prep-api.onrender.com/api/health |

## Local Development

### Prerequisites

- Python 3.12+
- Groq API key (get from [console.groq.com](https://console.groq.com) — free, no credit card)

### Backend

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your Groq API key
python -m uvicorn main:app --reload
```

### Frontend

Serve the `frontend/` directory with any static server:

```bash
python -m http.server 5500 -d ../frontend
```

## Deployment

### Backend (Render)

1. Push code to GitHub
2. Connect repo via Render Blueprint (`render.yaml` auto-configures everything)
3. Set `DATABASE_URL` (Neon PostgreSQL) and `GROQ_API_KEY` in Environment variables
4. Deploy — the service auto-builds and starts

### Frontend (GitHub Pages)

1. GitHub repo → Settings → Pages → Source: **GitHub Actions**
2. Push to `main` — included workflow auto-deploys `frontend/` to Pages
3. Site at `https://ravijeetchandra.github.io/quiz-app-interview/`

## Developer

Built by **[Ravijeet Chandra](https://github.com/ravijeetchandra)**

- GitHub: https://github.com/ravijeetchandra
- Support: https://ravijeetchandra.github.io/quiz-app-interview/pages/donate.html
