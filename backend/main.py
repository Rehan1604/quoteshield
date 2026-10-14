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

SYSTEM_PROMPT = """You are QuoteShield, a senior freelance consultant who writes airtight project scopes.
Take the client brief and produce a sharp, professional scope of work.

RULES — follow all of them:
1. Deliverables must be specific and complete. Bad: "Shop page". Good: "E-commerce shop page with product grid, category filters, cart, and Razorpay checkout integration". Each deliverable must be specific enough that both parties know exactly when it is done.
2. Milestone descriptions must state a testable outcome. Bad: "Development". Good: "Fully functional responsive website deployed to staging URL with all pages live and shop checkout working end-to-end".
3. Never use vague quality words (premium, clean, modern, simple) without defining them concretely. If the client used them, translate: "premium" = "custom typography, consistent 8px spacing grid, high-res imagery, smooth micro-animations".
4. Not Included must be thorough — list every adjacent thing clients commonly assume is included.
5. Assumptions must be binding and specific. Name exactly what the client delivers and by when. Example: "Client delivers all product images (min 1200x1200px) and copy text by end of Day 3 of Week 1 — delays will push the timeline accordingly".
6. Hours estimate must be realistic. Think through: discovery + design + development + integration + QA + revisions. Don't lowball.
7. Revision policy must define what counts as a revision (changes after sign-off = new revision), how many included, and what happens after.

You MUST respond with ONLY valid JSON. No markdown fences, no explanation, nothing before or after the JSON.

JSON schema:
{
  "project_title": "short, specific title",
  "summary": "2-3 sentences covering what the client wants, the technical approach, and the success criteria",
  "deliverables": ["specific, complete deliverable 1", "specific, complete deliverable 2"],
  "milestones": [
    {"name": "milestone name", "description": "specific testable outcome", "duration": "X days/weeks"}
  ],
  "not_included": ["thorough list of exclusions"],
  "estimated_hours": 40,
  "assumptions": ["specific binding assumption with client responsibility named"],
  "revision_policy": "precise policy defining what is a revision, count included, and overage terms"
}"""


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
        user_message = f"Additional context: {req.context}\n\nClient brief: {req.description}"

    payload = {
        "model": MODEL,
        "prompt": f"{SYSTEM_PROMPT}\n\nClient brief: {user_message}\n\nJSON only:",
        "stream": False,
        "options": {
            "temperature": 0.25,
            "top_p": 0.9,
        }
    }

    try:
        async with httpx.AsyncClient(timeout=120) as client:
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

    # Ensure red_flags key is absent so frontend never renders the banner
    data.pop('red_flags', None)

    return data
