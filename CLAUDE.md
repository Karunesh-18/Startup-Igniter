# Startup Igniter

## DGX access (self-hosted Qwen)
Shared host: other users occupy ports 8000-8002, so we use our own range. Key auth is already set up (no password needed).

- SSH: `ssh -o BatchMode=yes sece2026-student36@aicentre.sece.ac.in` (LAN fallback: `192.168.4.99`)
- Ports: vLLM heavy Qwen3-32B `47001`, vLLM fast Qwen3-8B `47002`, backend dev API `47000`
- Tunnel from the dev PC:
  `ssh -o BatchMode=yes -o ExitOnForwardFailure=yes -o ServerAliveInterval=15 -o ServerAliveCountMax=4 -N -L 47001:localhost:47001 -L 47002:localhost:47002 sece2026-student36@aicentre.sece.ac.in`
- Start/stop servers on the DGX (`cd ~/Startup-Igniter && . .venv/bin/activate` first, or `python` is not found): `training/serve/vllm_up.sh` / `vllm_down.sh`. Currently run with `TP_HEAVY=1 GPUS_HEAVY=0 GPUS_FAST=2 GPU_UTIL=0.55 MAX_LEN=32768` via `(setsid nohup bash training/serve/vllm_up.sh > logs/vllm_up.log 2>&1 < /dev/null &)`; loading takes ~5 min. Context is 32768 (it was 8192, which truncated long crews). Check `curl localhost:47001/health`.
- Backend against the tunnel:
  `LLM_BASE_URL=http://localhost:47001/v1 LLM_BASE_URL_FAST=http://localhost:47002/v1 LLM_ALLOW_MOCK=false ALLOWED_ORIGINS=http://localhost:5173 python -m uvicorn api.main:app --host 127.0.0.1 --port 47000`
- Open the frontend as `localhost:5173`, not `127.0.0.1` (CORS).

## Conventions
- All prices in rupees (INR, paise in the DB); never use `$`.

## Architecture notes
- `ai/pipeline.py::run_pipeline` is the single entry for a 13-crew run; the API runs it in `backend/services/runner.py` as a background task (events buffered in memory, report persisted to `analyses.result`). Run ONE API process.
- Scores are 0-100 everywhere, confidence 0-1 (normalised by `ai/shared/digest.py`). Never guess scales in the UI.
- Evidence: `ai/evidence/{sources,signals,ledger}.py`. A claim is `supported` only with a verbatim quote from a fetched source.
- Plans: Free (3 analyses, redacted preview via `services/entitlements.redact`), Report ₹299 (unlocks one analysis), Pro ₹999/mo. All money is INR in paise; the LLM is told to answer in ₹ (`CURRENCY_RULE` in `ai/llm/gateway.py`).
- Auth: Supabase JWT verified against JWKS (`backend/core/auth.py`). No unverified-claims fallback anywhere.
- Supabase project `oonbpirmxlmnavycjhjt`; DB via the Session pooler (password is percent-encoded in `backend/.env`; `alembic upgrade head` works). Email confirmation is on; Google provider is off.
- Vite dev server and API may already be running from earlier sessions: check ports 5173/47000 and kill stale processes before restarting.
- When writing files from bash heredocs, backslash escapes (`\n`, `\b`) get mangled; use the Write/Edit tools for code containing them.
