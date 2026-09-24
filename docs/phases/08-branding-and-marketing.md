# Phase 08: Branding & Marketing

**Status:** ⚪ SPECIFIED (not built) · **Crew ID:** 8 · **Domain:** Identity · **Agents:** 5 (frontend) / 0 backend

## Current behavior

`ai/crews/branding_marketing/tasks.py` returns a hardcoded
`BrandingMarketingResult` with literal brand-name suggestions (`"Igniter OS"`,
`"LaunchScale AI"`, `"VenturePulse"`) — see the file directly for the full
current fixture.

## Intended purpose

Produce brand name candidates, a tagline, positioning strategy, copywriting
angles, and a go-to-market channel strategy grounded in the category and
target customers already identified in Phases 01–02.

## Existing schema

[`BrandingMarketingResult`](../schemas/BrandingMarketingResult.json):
`brand_name_suggestions`, `tagline`, `brand_positioning`,
`copywriting_angles`, `launch_channel_strategy`, `confidence_score`.

## Suggested agent split

| # | Agent | Doc | Natural schema target |
|---|---|---|---|
| 44 | Brand & Marketing Agent | [agent doc](../agents/44-brand-and-marketing-agent.md) | `brand_positioning` |
| 45 | Naming Advisor | [agent doc](../agents/45-naming-advisor.md) | `brand_name_suggestions`, `tagline` |
| 46 | Marketing Strategy Agent | [agent doc](../agents/46-marketing-strategy-agent.md) | `copywriting_angles` |
| 47 | Go-To-Market Agent | [agent doc](../agents/47-go-to-market-agent.md) | `launch_channel_strategy` |
| 48 | Digital Marketing Agent | [agent doc](../agents/48-digital-marketing-agent.md) | new field needed (paid ads/SEO specifics) |

Only 5 agents here (not 6, unlike most other crews) — there is no
"Summary" agent for this crew in the frontend taxonomy. Building this crew
per-agent should decide whether to add one (for consistency with every
other crew) or have the Brand & Marketing Agent double as the synthesizer.

## Inputs (once built)

`IdeaValidationResult` (Phase 01), `MarketResearchResult` (Phase 02,
particularly `CustomerPersona` and `CompetitorDiscovery` for differentiated
positioning).

## Failure modes (once built)

Trademark/naming conflict checking is out of scope for an LLM call alone —
`brand_name_suggestions` should be flagged as unverified candidates, not
cleared names, until checked against a real trademark database.
