"""QuoteShield API — turns messy client briefs into professional scope docs via Groq."""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import httpx
import json
import re
import os

app = FastAPI(title="QuoteShield API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

# Tried in order. If Groq retires one, the next is used automatically.
# Override on Render with env var GROQ_MODELS="model-a,model-b".
DEFAULT_MODELS = ["openai/gpt-oss-20b", "openai/gpt-oss-120b"]
MODELS = [m.strip() for m in os.environ.get("GROQ_MODELS", ",".join(DEFAULT_MODELS)).split(",") if m.strip()]

SYSTEM_PROMPT = """You are QuoteShield, a senior freelance consultant who writes airtight project scopes.
Take the client brief and produce a sharp, professional scope of work.

RULES — follow all of them:
1. Deliverables must be specific and complete. Bad: "Shop page". Good: "E-commerce shop page with product grid, category filters, cart, and Razorpay checkout integration". Each deliverable must be specific enough that both parties know exactly when it is done.
2. Milestone descriptions must state a testable outcome. Bad: "Development". Good: "Fully functional responsive website deployed to staging URL with all pages live and shop checkout working end-to-end".
3. Never use vague quality words (premium, clean, modern, simple) without defining them concretely. If the client used them, translate: "premium" = "custom typography, consistent 8px spacing grid, high-res imagery, smooth micro-animations".
4. Not Included must be thorough (at least 5 items) — list every adjacent thing clients commonly assume is included.
5. Assumptions must be binding and specific (at least 3). Name exactly what the client delivers and by when, including any accounts, API keys or credentials the project depends on.
6. Hours estimate must be realistic: discovery + design + development + integration + QA + revisions. Don't lowball.
7. Revision policy must define what counts as a revision (changes after sign-off = new revision), how many rounds are included, and what happens after.
8. If the brief is not in English, still write the scope in English.
9. If the freelancer gives a tone or hourly rate in the additional context, respect it.

Respond with ONLY a JSON object with exactly these keys:
{
  "project_title": "short, specific title",
  "summary": "2-3 sentences covering what the client wants, the technical approach, and the success criteria",
  "deliverables": ["specific, complete deliverable"],
  "milestones": [{"name": "milestone name", "description": "specific testable outcome", "duration": "X days/weeks"}],
  "not_included": ["exclusion"],
  "estimated_hours": 40,
  "assumptions": ["specific binding assumption with client responsibility named"],
  "revision_policy": "precise policy defining what is a revision, count included, and overage terms"
}"""


class ProjectRequest(BaseModel):
    description: str = Field(..., max_length=5000)
    context: str = Field("", max_length=2000)


@app.get("/")
def root():
    return {"status": "QuoteShield running", "models": MODELS}


@app.get("/health")
def health():
    return {"groq_key": bool(os.environ.get("GROQ_API_KEY")), "models": MODELS}


# ── Output normalisation: guarantees the frontend always gets the right shape ──

def _str_list(value) -> list:
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, list):
        return []
    out = []
    for item in value:
        if isinstance(item, str) and item.strip():
            out.append(item.strip())
        elif isinstance(item, dict):
            text = " — ".join(str(v) for v in item.values() if v)
            if text:
                out.append(text)
    return out


def _hours(value) -> int:
    if isinstance(value, (int, float)):
        return max(0, int(round(value)))
    if isinstance(value, str):
        nums = [float(n) for n in re.findall(r"\d+(?:\.\d+)?", value)]
        if nums:
            return int(round(sum(nums) / len(nums)))  # "60-80" -> 70
    return 0


def normalise(data: dict) -> dict:
    milestones = []
    for m in data.get("milestones") or []:
        if isinstance(m, dict):
            milestones.append({
                "name": str(m.get("name") or m.get("title") or "Milestone").strip(),
                "description": str(m.get("description") or m.get("outcome") or "").strip(),
                "duration": str(m.get("duration") or m.get("timeline") or "TBD").strip(),
            })
        elif isinstance(m, str) and m.strip():
            milestones.append({"name": m.strip(), "description": "", "duration": "TBD"})

    policy = data.get("revision_policy") or ""
    if isinstance(policy, dict):
        policy = " ".join(f"{k}: {v}" for k, v in policy.items())
    elif isinstance(policy, list):
        policy = " ".join(map(str, policy))

    return {
        "project_title": str(data.get("project_title") or data.get("title") or "Project Scope").strip(),
        "summary": str(data.get("summary") or "").strip(),
        "deliverables": _str_list(data.get("deliverables")),
        "milestones": milestones,
        "not_included": _str_list(data.get("not_included") or data.get("exclusions")),
        "estimated_hours": _hours(data.get("estimated_hours")),
        "assumptions": _str_list(data.get("assumptions")),
        "revision_policy": str(policy).strip(),
    }


def extract_json(raw: str):
    cleaned = re.sub(r"```(?:json)?|```", "", raw or "").strip()
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if not match:
        return None
    try:
        parsed = json.loads(match.group())
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        return None


async def call_groq(client, api_key, model, user_message, json_mode):
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        "temperature": 0.3,
        "max_completion_tokens": 4096,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
    if model.startswith("openai/gpt-oss"):
        payload["reasoning_effort"] = "low"
    return await client.post(
        GROQ_URL,
        json=payload,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
    )


@app.post("/generate")
async def generate_scope(req: ProjectRequest):
    if not req.description.strip():
        raise HTTPException(status_code=400, detail="Description cannot be empty")

    api_key = os.environ.get("GROQ_API_KEY", "").strip()
    if not api_key:
        raise HTTPException(status_code=500, detail="Server is missing GROQ_API_KEY")

    user_message = f"Client brief:\n{req.description.strip()}"
    if req.context.strip():
        user_message = f"Additional context from the freelancer:\n{req.context.strip()}\n\n{user_message}"
    user_message += "\n\nReturn only the JSON object."

    last_error = "Unknown error"
    async with httpx.AsyncClient(timeout=60) as client:
        for model in MODELS:
            for json_mode in (True, False):
                try:
                    resp = await call_groq(client, api_key, model, user_message, json_mode)
                except httpx.TimeoutException:
                    last_error = f"{model} timed out"
                    break
                except httpx.HTTPError as e:
                    last_error = f"Network error reaching Groq: {e}"
                    break

                if resp.status_code == 401:
                    raise HTTPException(status_code=502, detail="Groq rejected the API key — check GROQ_API_KEY on Render")
                if resp.status_code == 429:
                    raise HTTPException(status_code=429, detail="Rate limit hit — wait a minute and try again")

                if resp.status_code != 200:
                    body = resp.text[:300]
                    last_error = f"{model}: {resp.status_code} {body}"
                    # JSON mode rejected / JSON validation failed -> retry same model in plain mode
                    if json_mode and resp.status_code == 400 and "decommissioned" not in body.lower():
                        continue
                    break  # model retired / unavailable -> try next model

                try:
                    content = resp.json()["choices"][0]["message"].get("content") or ""
                except (KeyError, IndexError, ValueError):
                    last_error = f"{model}: unexpected response shape"
                    break

                data = extract_json(content)
                if data is None:
                    last_error = f"{model}: returned non-JSON output"
                    continue  # retry without JSON mode, then next model

                result = normalise(data)
                if not result["deliverables"] and not result["milestones"]:
                    last_error = f"{model}: returned an empty scope"
                    continue
                return result

    raise HTTPException(status_code=502, detail=f"Couldn't generate a scope right now. {last_error}")
