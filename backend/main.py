from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import json
import re

app = FastAPI(title="QuoteShield API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "mistral"

SYSTEM_PROMPT = """You are QuoteShield. Turn client briefs into tight, professional scope-of-work JSON.

RULES:
1. Deliverables: specific and complete. NOT "Shop page" — YES "E-commerce shop page with product grid, filters, cart, Razorpay checkout".
2. Milestones: testable outcome only. NOT "Development" — YES "Responsive site deployed to staging with all pages and checkout live".
3. No vague words (premium/clean/modern) — translate them concretely.
4. not_included: thorough — every adjacent service clients assume is included.
5. assumptions: binding — name exactly what client delivers and by when.
6. estimated_hours: realistic (discovery + design + dev + QA + revisions).
7. revision_policy: define what IS a revision, count included, cost after.

Reply with ONLY this JSON, no fences:
{"project_title":"...","summary":"2-3 sentences: what, how, success criteria","deliverables":["..."],"milestones":[{"name":"...","description":"testable outcome","duration":"X days"}],"not_included":["..."],"estimated_hours":0,"assumptions":["..."],"revision_policy":"..."}"""


class ProjectRequest(BaseModel):
    description: str
    context: str = ""


@app.get("/")
def root():
    return {"status": "QuoteShield running", "model": MODEL}


@app.get("/health")
async def health():
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get("http://localhost:11434/api/tags")
            models = [m["name"] for m in r.json().get("models", [])]
            return {"ollama": "ok", "models": models}
    except Exception as e:
        return {"ollama": "unreachable", "error": str(e)}


@app.post("/generate")
async def generate_scope(req: ProjectRequest):
    if not req.description.strip():
        raise HTTPException(status_code=400, detail="Description cannot be empty")

    user_message = req.description
    if req.context:
        user_message = f"Additional context: {req.context}\n\nProject description: {req.description}"

    payload = {
        "model": MODEL,
        "prompt": f"{SYSTEM_PROMPT}\n\nClient brief: {user_message}\n\nRespond with only the JSON object:",
        "stream": False,
        "options": {
            "temperature": 0.25,
            "top_p": 0.9,
            "num_predict": 1200,
        }
    }

    try:
        async with httpx.AsyncClient(timeout=180) as client:
            response = await client.post(OLLAMA_URL, json=payload)
            response.raise_for_status()
    except httpx.ConnectError:
        raise HTTPException(
            status_code=503,
            detail="Cannot reach Ollama. Make sure it's running: ollama serve"
        )
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Model took too long to respond")

    raw = response.json().get("response", "")

    # Strip markdown fences if model wraps anyway
    cleaned = re.sub(r"```(?:json)?|```", "", raw).strip()

    # Find the JSON object
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if not match:
        raise HTTPException(
            status_code=422,
            detail=f"Model didn't return valid JSON. Raw: {raw[:300]}"
        )

    try:
        data = json.loads(match.group())
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=422, detail=f"JSON parse error: {e}")

    data.pop('red_flags', None)

    return data
