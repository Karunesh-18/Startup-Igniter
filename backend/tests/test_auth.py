"""
Tests for auth endpoints.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient):
    """A new user can register and receive a JWT."""
    response = await client.post("/api/v1/auth/register", json={
        "email": "new@example.com",
        "name": "New Founder",
        "password": "securepass123",
        "role": "student",
    })
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert "user_id" in data


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    """Registering with a duplicate email returns 409."""
    body = {"email": "dup@example.com", "name": "A", "password": "pass1234"}
    await client.post("/api/v1/auth/register", json=body)
    response = await client.post("/api/v1/auth/register", json=body)
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    """User can login after registration."""
    await client.post("/api/v1/auth/register", json={
        "email": "login@example.com",
        "name": "Login User",
        "password": "mypassword1",
    })
    response = await client.post("/api/v1/auth/login", json={
        "email": "login@example.com",
        "password": "mypassword1",
    })
    assert response.status_code == 200
    assert "access_token" in response.json()


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    """Wrong password returns 401."""
    await client.post("/api/v1/auth/register", json={
        "email": "wrongpw@example.com",
        "name": "User",
        "password": "correct123",
    })
    response = await client.post("/api/v1/auth/login", json={
        "email": "wrongpw@example.com",
        "password": "wrong",
    })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me(client: AsyncClient, auth_headers: dict, test_user: dict):
    """Authenticated user can fetch their profile."""
    response = await client.get("/api/v1/auth/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user["user"].email
    assert data["name"] == "Test Founder"


@pytest.mark.asyncio
async def test_get_me_unauthorized(client: AsyncClient):
    """Unauthenticated request to /me returns 403 or 401."""
    response = await client.get("/api/v1/auth/me")
    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Health endpoint returns 200."""
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
