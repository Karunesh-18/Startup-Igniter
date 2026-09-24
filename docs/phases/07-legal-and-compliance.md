# Phase 07: Legal & Compliance

**Status:** ⚪ SPECIFIED (not built) · **Crew ID:** 7 · **Domain:** Compliance · **Agents:** 6 (frontend) / 0 backend

## Current behavior

`ai/crews/legal_compliance/tasks.py` returns a hardcoded
`LegalComplianceResult`.

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
