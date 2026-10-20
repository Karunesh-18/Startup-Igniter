"""Tests for the NDJSON streaming analysis endpoint.

Uses mock_mode=True throughout -- these are unit tests of the streaming
plumbing (does it yield the right event sequence, in the right order, with
the right final result shape), not integration tests of the AI crews
themselves (those are covered in ai/tests/).
"""

import json

import pytest


CREW_KEYS = [
    "idea_validation", "market_research", "research_patent", "feasibility", "business_planning",
    "product_development", "legal_compliance", "branding_marketing", "funding", "growth_scaling",
    "community", "reporting",
]


@pytest.mark.asyncio
async def test_stream_yields_started_then_twelve_crew_events_then_result(client):
    events = []
    async with client.stream(
        "POST",
        "/api/v1/analysis/run/stream",
        json={"idea_text": "An AI tool that reviews legal contracts for small businesses.", "mock_mode": True},
    ) as response:
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("application/x-ndjson")
        async for line in response.aiter_lines():
            if line.strip():
                events.append(json.loads(line))

    types = [e["type"] for e in events]
    assert types == ["started"] + ["crew_complete"] * 12 + ["result"]

    crew_events = [e for e in events if e["type"] == "crew_complete"]
    assert [e["crew"] for e in crew_events] == CREW_KEYS
    assert all(e["result"] and e["label"] for e in crew_events)

    result = events[-1]["result"]
    assert result["status"] == "success"
    for key in CREW_KEYS:
        assert result[key], key
    assert result["funding"] == crew_events[CREW_KEYS.index("funding")]["result"]
    assert 0 < result["overall_readiness_score"] <= 100


@pytest.mark.asyncio
async def test_stream_started_event_lists_all_twelve_crew_labels(client):
    async with client.stream(
        "POST",
        "/api/v1/analysis/run/stream",
        json={"idea_text": "A marketplace connecting farmers directly with restaurants.", "mock_mode": True},
    ) as response:
        first_line = await response.aiter_lines().__anext__()

    started = json.loads(first_line)
    assert started["type"] == "started"
    assert started["crews"] == [
        "Idea Validation", "Market Research", "Research & Patent", "Technical Feasibility",
        "Business Planning", "Product Development", "Legal & Compliance", "Branding & Marketing",
        "Funding Readiness", "Growth & Scaling", "Community & Ecosystem", "Executive Reporting",
    ]
    assert started["project_id"]


@pytest.mark.asyncio
async def test_stream_result_is_also_retrievable_via_get(client):
    """The streamed result is cached the same way /run's is -- GET /{project_id} works identically."""
    project_id = "proj-stream-test-001"
    events = []
    async with client.stream(
        "POST",
        "/api/v1/analysis/run/stream",
        json={
            "idea_text": "A subscription box for zero-waste home cleaning refills.",
            "project_id": project_id,
            "mock_mode": True,
        },
    ) as response:
        async for line in response.aiter_lines():
            if line.strip():
                events.append(json.loads(line))

    get_response = await client.get(f"/api/v1/analysis/{project_id}")
    assert get_response.status_code == 200
    assert get_response.json()["project_id"] == project_id
    assert get_response.json() == events[-1]["result"]
