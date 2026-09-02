import os
from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException, Request, Depends
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from agent import run_agent

load_dotenv()

# Parse API_KEYS from .env: "key1:name1,key2:name2" -> {"key1": "name1", "key2": "name2"}
def load_api_keys():
    raw = os.getenv("API_KEYS", "")
    keys = {}
    for pair in raw.split(","):
        pair = pair.strip()
        if not pair:
            continue
        key, _, name = pair.partition(":")
        keys[key.strip()] = name.strip() or "unknown"
    return keys

API_KEYS = load_api_keys()


def get_api_key_identity(request: Request):
    """Used by the rate limiter to key limits per API key instead of per IP."""
    return request.headers.get("x-api-key", get_remote_address(request))


limiter = Limiter(key_func=get_api_key_identity)

app = FastAPI(title="Productivity Agent API")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


def verify_api_key(x_api_key: str = Header(...)):
    """Dependency: validates the X-API-Key header and returns the client name."""
    if x_api_key not in API_KEYS:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return API_KEYS[x_api_key]


class ChatRequest(BaseModel):
    message: str
    conversation_history: list = []


class ChatResponse(BaseModel):
    reply: str
    conversation_history: list


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
@limiter.limit("10/minute")
def chat(request: Request, body: ChatRequest, client_name: str = Depends(verify_api_key)):
    history = list(body.conversation_history)
    reply = run_agent(body.message, history)
    return ChatResponse(reply=reply, conversation_history=history)