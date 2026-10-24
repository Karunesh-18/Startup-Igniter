# Digital Marketing Agent

**Crew:** [Branding & Marketing](../phases/08-branding-and-marketing.md) (BRND) · **Role:** Paid Ads & SEO · **Status:** 🟢 IMPLEMENTED (crew-level)

## Implementation

This agent is a role inside the **Branding & Marketing** crew, which runs as one
structured LLM call (`ai/crews/spec_runner.py::run_spec_crew`) validated
against the crew's result schema in `ai/schemas/`. The agent is not a
separate call; this document and the
[Phase 08](../phases/08-branding-and-marketing.md) doc are part of the
crew's system prompt. Crew code: `ai/crews/branding_marketing/`.

## Where this fits

Part of the **Branding & Marketing** crew (Identity), agent 48 of 66
in the canonical taxonomy (see [docs/README.md](../README.md)).
