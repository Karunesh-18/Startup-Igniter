# Community Peer Review Agent

**Crew:** [Community & Ecosystem](../phases/11-community-and-ecosystem.md) (COMM) · **Role:** Peer Review · **Status:** 🟢 IMPLEMENTED (crew-level)

## Implementation

This agent is a role inside the **Community & Ecosystem** crew, which runs as one
structured LLM call (`ai/crews/spec_runner.py::run_spec_crew`) validated
against the crew's result schema in `ai/schemas/`. The agent is not a
separate call; this document and the
[Phase 11](../phases/11-community-and-ecosystem.md) doc are part of the
crew's system prompt. Crew code: `ai/crews/community/`.

## Where this fits

Part of the **Community & Ecosystem** crew (Network), agent 58 of 66
in the canonical taxonomy (see [docs/README.md](../README.md)).
