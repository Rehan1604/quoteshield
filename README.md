# ⚔️ QuoteShield

Turn a chaotic client brief into a professional scope of work — in seconds, fully offline.

## Stack
- **Frontend:** React + Vite
- **Backend:** FastAPI
- **AI:** Mistral via Ollama (runs locally, zero cloud)

## Prerequisites

1. [Ollama](https://ollama.com) installed and running
2. Mistral model pulled:
   ```
   ollama pull mistral
   ```
3. Python 3.10+ and Node 18+

## Setup

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173)

## How it works

1. Paste any messy project brief (WhatsApp message, email, voice note transcript)
2. QuoteShield sends it to Mistral running locally via Ollama
3. The model returns structured JSON — milestones, deliverables, exclusions, hours estimate
4. You get a clean scope doc you can copy and send to the client

**Your data never leaves your machine.** No API keys, no subscriptions, no monthly bill.
