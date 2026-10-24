# Local development

## One command (Windows)

Run `dev.cmd` from the repo root. It:

1. Opens the DGX SSH tunnel (ports 47001 and 47002) in its own window.
2. Starts the backend on 47000 with the tunnel's LLM URLs,
   `LLM_ALLOW_MOCK=false` and `ALLOWED_ORIGINS=http://localhost:5173`.
3. Starts the frontend (`npm run dev`) on 5173.
4. Waits 15 seconds, then curls `/health` on 47001, 47002 and 47000 and `/` on
   5173, printing `[ OK ]` or `[FAIL]` for each.

A step is skipped when its port is already listening, so re-running is safe.

It does **not** start vLLM on the DGX. If the vLLM lines show `[FAIL]`, bring
the servers up per [dgx-runbook.md](dgx-runbook.md) (`training/serve/vllm_up.sh`,
about 5 minutes to load). A `[FAIL]` right after a cold start can also just
mean the service is still starting; re-run the script.

Open `http://localhost:5173`, not `127.0.0.1`.

## Manual

The individual commands (tunnel, backend, frontend) are in the root
`CLAUDE.md` and `README.md`. Run only one API process: run state is held in
memory ([ADR 0006](../architecture/0006-evidence-ledger-and-skeptic.md)).
