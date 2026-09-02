# Productivity Agent API

A FastAPI wrapper around [productivity-agent](https://github.com/codeSudee/productivity-agent) — a tool-calling AI task manager — that exposes it as a secured, rate-limited HTTP service. Built to demonstrate general backend/deployment skills (auth, rate limiting, live deployment) on top of an existing AI agent, rather than another purely ML-focused project.

**Live URL:** https://productivity-agent-api.onrender.com

> Note: this runs on Render's free tier, which spins down after periods of inactivity. The first request after idle time can take 30–60 seconds while the instance wakes up.

## What it does

Wraps the agent's core `run_agent()` function (originally a CLI loop) in a small HTTP API:

- `POST /chat` — send a message, get back the agent's reply plus updated conversation history
- `GET /health` — unauthenticated health check, used by the host to confirm the service is alive

## Features

- **API key authentication** — every `/chat` request must include a valid `X-API-Key` header. Keys are mapped to client names via an `API_KEYS` environment variable (`key:name` pairs), so the service supports multiple named clients rather than a single shared secret.
- **Per-key rate limiting** — 10 requests/minute per API key, enforced with `slowapi`. Limiting is keyed on the API key itself (not the caller's IP), so two clients behind the same network don't share a limit, and a single client can't dodge the limit by rotating IPs.
- **Stateless design** — the caller sends `conversation_history` with each request and receives the updated history back. No server-side session storage, which keeps the service simple and avoids state being lost on restart/redeploy.

## Tech stack

FastAPI · Uvicorn · slowapi · OpenAI API (`gpt-4o-mini`) · python-dotenv

## Running locally

```bash
git clone https://github.com/codeSudee/productivity-agent-api.git
cd productivity-agent-api
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then fill in real values
python3 -m uvicorn main:app --reload
```

Server runs at `http://127.0.0.1:8000`.

## Example usage

```bash
# Health check (no auth required)
curl http://127.0.0.1:8000/health

# Chat (requires a valid API key)
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-key-here" \
  -d '{"message": "add a task to submit the report by Friday"}'
```

## Debugging notes

**`ModuleNotFoundError` despite the package being installed.** After installing `slowapi` inside an active virtual environment, `uvicorn main:app --reload` still failed with `ModuleNotFoundError: No module named 'slowapi'`. `pip show slowapi` confirmed it was installed correctly inside the venv, and `which python3` correctly pointed to the venv's interpreter — but `which uvicorn` resolved to a **global** uvicorn install outside the venv. Because uvicorn's `--reload` flag spawns a subprocess to run the app, that subprocess was using the global Python (which never had `slowapi` installed), not the venv's Python — even though the venv was active in the shell. Fixed by running uvicorn as a module through the venv's own Python explicitly:

```bash
python3 -m uvicorn main:app --reload
```

This guarantees the reload subprocess uses the same interpreter as the rest of the venv, regardless of what `uvicorn` resolves to on PATH.

## Possible extensions

- Persist rate-limit counters and API keys in a database instead of in-memory/env vars, so limits survive restarts and keys can be managed without redeploying
- Add per-client conversation history storage (currently stateless by design)
- Swap the free Render tier for a paid one to remove cold-start latency