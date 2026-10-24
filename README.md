# Startup Igniter

An idea validator that shows its evidence. A founder describes an idea; thirteen AI crews analyse it, a verifier checks every claim against real sources, a skeptic argues the other side, and the result is a go / pivot / no-go verdict with the risks and the sources behind it. Ideas are saved to an account and can be refined with an AI co-founder, tracked as experiments, re-checked against the market, and pushed to GitHub, Slack or Notion.

Prices are in Indian rupees: first three analyses free, ₹299 to unlock one full report, ₹999/month for Pro.

## What is different

| | Typical idea validators | Startup Igniter |
|---|---|---|
| Claims | Unsourced LLM text | Each claim is matched to a sentence in a fetched source; only verbatim quotes count as supported. A grounding score is shown. |
| Judgement | Mostly positive | A skeptic crew writes the case against, a pre-mortem, and what evidence would change the verdict. |
| Scores | One number | Number, likely range, confidence, and share of claims sourced. |
| After the report | Nothing | Saved ideas with versions and score changes, AI co-founder that proposes edits to the idea, experiments, market watch, GitHub issues export. |
| Model | A paid API | Self-hosted Qwen3 on your own GPUs (vLLM), no per-token bill. |

## Layout

```
ai/         crews, agents, prompts, LLM gateway, evidence (sources, ledger, signals), pipeline.py
backend/    FastAPI: ideas, analyses (background runs + NDJSON progress), chat, billing, integrations
frontend/   React + Vite + Tailwind
training/   LoRA training, vLLM serving, eval harness
docs/       phase and agent specs, ADRs, ops runbooks
```

## Run locally

1. LLM: open the SSH tunnel to the vLLM servers (see `CLAUDE.md`), or point `LLM_BASE_URL` at any OpenAI-compatible server.
2. Backend (`backend/`): copy `.env.example` to `.env`, fill in Supabase and (optionally) Razorpay values, then
   `alembic upgrade head` and
   `LLM_BASE_URL=http://localhost:47001/v1 LLM_BASE_URL_FAST=http://localhost:47002/v1 uvicorn api.main:app --port 47000`
3. Frontend (`frontend/`): `.env.local` needs `VITE_SUPABASE_URL`, `VITE_SUPABASE_PUBLISHABLE_KEY` and optionally `VITE_API_BASE_URL`; then `npm install && npm run dev`.

Without an LLM server a development run produces clearly labelled placeholder data (`mode: "mock"`); production never does (`LLM_ALLOW_MOCK=false` is the default and mock runs are refused when `ENVIRONMENT=production`).

## Billing

Razorpay in INR. Set `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`, `RAZORPAY_WEBHOOK_SECRET` and point a Razorpay webhook at `POST /api/v1/billing/webhook` (events: `order.paid`, `payment.captured`, `subscription.*`). The Pro plan is created in Razorpay on first use, or set `RAZORPAY_PLAN_PRO_ID`. For development without keys, `BILLING_DEV_MODE=true` enables a simulated checkout; it is ignored in production. Prices and the free quota are `PRICE_REPORT_PAISE`, `PRICE_PRO_PAISE`, `FREE_ANALYSES`.

## Tests

```
cd backend && .venv/Scripts/python -m pytest tests ../ai/tests
cd frontend && npm run typecheck && npm run build
```

## Deploy

Backend on Fly (`fly deploy --config backend/fly.toml --dockerfile backend/Dockerfile .` from the repo root) with a single machine: analysis runs and their event buffers are held in process. The API must be able to reach the vLLM servers (reverse proxy or private network to the GPU host). Frontend is a static build (`npm run build`); set `ALLOWED_ORIGINS` and `FRONTEND_URL` on the backend to its origin.

## Limits to know

- Source gathering uses keyless web search, so coverage varies by topic; the grounding score reports it honestly.
- The claim verifier is an 8B model checking short passages against exact quotes; it can miss supported claims (never the other way, because quotes must match the source).
- Google sign-in needs the provider enabled in the Supabase dashboard; email sign-in needs the confirmation link.
