# Phase 07: Legal & Compliance

**Status:** 🟢 IMPLEMENTED (crew-level) · **Crew ID:** 7 · **Domain:** Compliance · **Agents:** 6 (frontend) / 1 crew-level call

## Current behavior

Runs as one structured LLM call through `ai/crews/spec_runner.py::run_spec_crew` (heavy tier, 12000 max tokens). This phase doc plus the agent docs listed for the crew are the system prompt; the user prompt carries a digest of the prior crews' results and the shared numbered source pool. The reply is validated against the crew's result schema (`ai/schemas/`). The "agents" are roles the one call reasons through in turn, not separate calls. If the call fails the run continues and the report marks this crew unavailable. Claims from this crew's output are checked by the [evidence ledger](../architecture/0006-evidence-ledger-and-skeptic.md).

## Intended purpose

Produce a jurisdiction-aware compliance checklist and draft (never final)
legal documents — NDA, founder agreement — with the mandatory AI-generated
disclaimer the original spec requires on every such document (see
[ai-startup-navigator-spec-v2.md §8](../../ai-startup-navigator-spec-v2.md)).

## Existing schema

[`LegalComplianceResult`](../schemas/LegalComplianceResult.json):
- `compliance_checklist`: list of [`ComplianceItem`](../schemas/ComplianceItem.json)
  (category, title, description, is_mandatory, regulatory_body).
- `draft_nda`, `draft_founder_agreement`: optional
  [`LegalDocumentDraft`](../schemas/LegalDocumentDraft.json), each carrying
  its own `disclaimer` field with a sensible default already baked in:
  *"DISCLAIMER: This document is an AI-generated draft for reference only.
  Consult a licensed attorney before signing."*
- `overall_summary`, `confidence_score`.

## Suggested agent split

| # | Agent | Doc | Natural schema target |
|---|---|---|---|
| 38 | Compliance Checklist Agent | [agent doc](../agents/38-compliance-checklist-agent.md) | `compliance_checklist` |
| 39 | Legal Document Drafter | [agent doc](../agents/39-legal-document-drafter.md) | `draft_nda` / `draft_founder_agreement` |
| 40 | Data Privacy Agent | [agent doc](../agents/40-data-privacy-agent.md) | `ComplianceItem` entries tagged privacy/GDPR/DPDP |
| 41 | Licensing Advisor | [agent doc](../agents/41-licensing-advisor.md) | `ComplianceItem` entries tagged IP/OSS licensing |
| 42 | Registration Advisor | [agent doc](../agents/42-registration-advisor.md) | `ComplianceItem` entries tagged registration/incorporation |
| 43 | Legal Summary | [agent doc](../agents/43-legal-summary.md) | `overall_summary` |

## ⚠️ Grounding is not optional here

Per the original spec's guardrail ([ai-startup-navigator-spec-v2.md §9](../../ai-startup-navigator-spec-v2.md)):
legal/compliance content must be labeled "AI-generated, verify
independently" and dated ("last verified: [date]"). Base document drafts on
well-known, permissively-licensed public templates rather than having the
model draft clauses fully from scratch — this is exactly the kind of content
where an ungrounded self-hosted model confidently inventing plausible-sounding
but wrong legal text is a real liability risk, not just a quality problem.

## Inputs (once built)

`IdeaValidationResult` (Phase 01), `StartupCategoryClassification` (for
sector-specific regulatory mapping — e.g. FinTech/HealthTech need materially
different checklists than a generic SaaS).

## Failure modes (once built)

Same schema-validation pattern as Phases 01–03, plus: a missing or malformed
disclaimer on a generated document should be treated as a **hard failure**,
not a soft validation warning, given the liability exposure.
