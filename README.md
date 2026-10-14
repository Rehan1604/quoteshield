# ⚔️ QuoteShield

Paste a chaotic client brief — a WhatsApp message, a rambling email, a voice-note transcript — and get a professional scope of work in seconds: specific deliverables, testable milestones, a thorough "not included" list, binding assumptions, an hours estimate and a revision policy.

**Live:** https://quoteshield-ten.vercel.app

## Stack
- **Frontend:** React + Vite (Vercel)
- **Backend:** FastAPI (Render)
- **AI:** open-weight `gpt-oss-20b` on Groq, with automatic fallback to `gpt-oss-120b`

## Run locally

### Backend
```bash
cd backend
pip install -r requirements.txt
# get a free key at https://console.groq.com
export GROQ_API_KEY=your_key        # PowerShell: $env:GROQ_API_KEY="your_key"
uvicorn main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
# point at your local backend (defaults to the hosted one)
echo VITE_API_URL=http://localhost:8000 > .env.local
npm run dev
```

## Deploy
- **Render** (root `backend`): build `pip install -r requirements.txt`, start `uvicorn main:app --host 0.0.0.0 --port $PORT`, env var `GROQ_API_KEY`. Optional `GROQ_MODELS` to override the model list.
- **Vercel** (root `frontend`): framework Vite. Optional env var `VITE_API_URL`.

## Reliability
- Models are tried in order; a retired or unavailable model falls through to the next one.
- JSON mode is used when supported, with a plain-text retry if it's rejected.
- Model output is normalised server-side so the UI always gets a valid scope shape.
