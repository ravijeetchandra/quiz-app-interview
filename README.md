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

- ✅ **Two quiz modes**: By Resume (auto-detect domain) or By Topic (pick from domains)
- ✅ Login/Registration with JWT + refresh tokens
- ✅ Guest mode (no account needed)
- ✅ Forgot / reset password flow
- ✅ Upload PDF, DOCX, TXT files (study material or resume)
- ✅ Auto domain detection from resume content via AI
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

## How It Works

### 📄 By Resume
1. Upload your resume (PDF/DOCX/TXT)
2. AI auto-detects your domain (Data Science, Cybersecurity, etc.)
3. Questions are generated about that domain, tailored to your experience level
4. Take the quiz and get evaluated

### 📚 By Topic
1. Pick an interview domain from the list
2. AI generates general knowledge questions about that domain
3. No file upload needed — start practicing immediately
4. Take the quiz and get evaluated

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
