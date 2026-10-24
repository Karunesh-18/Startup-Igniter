# Product: accounts, API, billing, integrations

How the saved, multi-idea product around the pipeline works. The pipeline
itself is described in [ADR 0006](architecture/0006-evidence-ledger-and-skeptic.md).

## Accounts and auth

- Supabase Auth. The backend verifies the Supabase JWT against the project's
  JWKS (`backend/core/auth.py`). There is no unverified-claims fallback.
- Email confirmation is on; the Google provider is off.
- RLS is enabled by migration `0002`; ownership is also checked in the API.
- Database: Supabase Postgres through the Session pooler. Migrations:
  `alembic upgrade head` from `backend/`.

## Ideas and analyses

- An **idea** has many versioned **analyses**. `POST /ideas/{id}/analyses`
  returns 202 and starts a background run (`backend/services/runner.py`,
  max 2 concurrent runs, 6 starts per hour per user).
- Progress is an NDJSON event stream (`GET /analyses/{id}/events`) buffered in
  memory, so a closed tab can reconnect. The finished report is stored in
  `analyses.result`. `POST /analyses/{id}/cancel` stops a run between crews.
- `POST /ideas/{id}/rescan` re-checks the market for an existing idea.
- Experiments (`/ideas/{id}/experiments`, `/experiments/seed`) turn the
  skeptic's testable hypotheses into trackable items.

## Plans (all INR, stored in paise)

| Plan | Price | Gets |
|---|---|---|
| Free | ₹0 | 3 analyses, redacted preview (`services/entitlements.redact`) |
| Report | ₹299 once | Unlocks the full report for one analysis |
| Pro | ₹999/month | Everything, plus chat, integrations, experiments, export |

`PRO_FEATURES = {chat, integrations, experiments, export}`. A blocked call
returns HTTP 402 with `{code: "upgrade_required", feature, message}`, which
the UI turns into an upgrade prompt. The LLM is told to answer in ₹
(`CURRENCY_RULE` in `ai/llm/gateway.py`). Never use `$` anywhere.

## Billing (Razorpay)

`/billing`: `GET /me`, `POST /report-order`, `POST /subscribe`,
`POST /verify`, `POST /cancel`, `GET /payments`, `POST /webhook` (idempotent),
and `POST /dev-activate` for development only.

## Co-founder chat (Pro)

`GET`/`POST /ideas/{id}/chat`. The assistant can propose edits to the idea;
`POST /chat/messages/{id}/proposal` accepts or dismisses one.

## Integrations and export (Pro)

- `GET`/`PUT`/`DELETE /integrations/{provider}` store a provider connection.
- `POST /analyses/{id}/push/github` and `/push/{provider}` (Slack, Notion,
  webhook) send the report out. Outbound URLs go through
  `backend/services/netsafe.py` to block internal addresses.
- `GET /analyses/{id}/export` and `/export/*`: Markdown and PDF
  (`services/report_export.py`).

## Frontend

Vite + React in `frontend/`. Routes cover auth, dashboard, idea page (with
skeptic and evidence tabs), pricing, billing and integrations. Open it as
`http://localhost:5173`, not `127.0.0.1` (CORS).

## Tests and CI

`.github/workflows/ci.yml` runs backend and AI tests, the frontend typecheck
and a check that no `$` prices exist. Backend API tests:
`backend/tests/test_product_api.py`; pipeline and evidence tests:
`ai/tests/test_evidence_and_pipeline.py`.
