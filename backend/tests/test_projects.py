"""
Tests for project CRUD and phase management.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_project(client: AsyncClient, auth_headers: dict):
    """User can create a project."""
    response = await client.post(
        "/api/v1/projects",
        json={
            "name": "TestStartup",
            "tagline": "AI for everyone",
            "description": "We build AI tools for students.",
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "TestStartup"
    assert data["current_phase"] == "idea"
    return data


@pytest.mark.asyncio
async def test_list_projects(client: AsyncClient, auth_headers: dict):
    """User's projects are listed."""
    await client.post(
        "/api/v1/projects",
        json={"name": "ListTest"},
        headers=auth_headers,
    )
    response = await client.get("/api/v1/projects", headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) >= 1


@pytest.mark.asyncio
async def test_get_project_not_found(client: AsyncClient, auth_headers: dict):
    """Requesting a non-existent project returns 404."""
    import uuid
    fake_id = uuid.uuid4()
    response = await client.get(f"/api/v1/projects/{fake_id}", headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_project(client: AsyncClient, auth_headers: dict):
    """Project name and tagline can be updated."""
    create_resp = await client.post(
        "/api/v1/projects",
        json={"name": "OldName"},
        headers=auth_headers,
    )
    project_id = create_resp.json()["id"]

    response = await client.patch(
        f"/api/v1/projects/{project_id}",
        json={"name": "NewName", "tagline": "Updated tagline"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["name"] == "NewName"


@pytest.mark.asyncio
async def test_phase_status(client: AsyncClient, auth_headers: dict):
    """Phase status endpoint returns workflow structure."""
    create_resp = await client.post(
        "/api/v1/projects",
        json={"name": "PhaseTest"},
        headers=auth_headers,
    )
    project_id = create_resp.json()["id"]

    response = await client.get(
        f"/api/v1/projects/{project_id}/phase-status",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "current_phase" in data
    assert "workflow" in data
    assert "phases" in data
    assert data["current_phase"] == "idea"


@pytest.mark.asyncio
async def test_advance_phase_before_completion(client: AsyncClient, auth_headers: dict):
    """Advancing phase when current phase is not complete returns 400."""
    create_resp = await client.post(
        "/api/v1/projects",
        json={"name": "AdvanceTest"},
        headers=auth_headers,
    )
    project_id = create_resp.json()["id"]

    response = await client.post(
        f"/api/v1/projects/{project_id}/advance-phase",
        headers=auth_headers,
    )
    # Should fail because idea phase has no output yet
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_delete_project(client: AsyncClient, auth_headers: dict):
    """Owner can delete their project."""
    create_resp = await client.post(
        "/api/v1/projects",
        json={"name": "ToDelete"},
        headers=auth_headers,
    )
    project_id = create_resp.json()["id"]

    response = await client.delete(
        f"/api/v1/projects/{project_id}",
        headers=auth_headers,
    )
    assert response.status_code == 204

    # Verify it's gone
    get_response = await client.get(
        f"/api/v1/projects/{project_id}",
        headers=auth_headers,
    )
    assert get_response.status_code == 404
