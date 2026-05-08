"""
Tests for the Mergington High School API endpoints.
Uses the AAA (Arrange-Act-Assert) testing pattern.
"""

import pytest
from httpx import ASGITransport, AsyncClient

from src.app import app, activities


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activity participants before each test to avoid state leakage."""
    original = {
        name: list(details["participants"]) for name, details in activities.items()
    }
    yield
    for name, details in activities.items():
        details["participants"] = original[name]


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ─── GET / ────────────────────────────────────────────────────────────────────


@pytest.mark.anyio
async def test_root_redirects_to_index(client):
    # Arrange — no special setup needed

    # Act
    response = await client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


# ─── GET /activities ──────────────────────────────────────────────────────────


@pytest.mark.anyio
async def test_get_activities_returns_all(client):
    # Arrange
    expected_count = len(activities)

    # Act
    response = await client.get("/activities")
    data = response.json()

    # Assert
    assert response.status_code == 200
    assert len(data) == expected_count


@pytest.mark.anyio
async def test_get_activities_contains_expected_fields(client):
    # Arrange
    required_fields = {"description", "schedule", "max_participants", "participants"}

    # Act
    response = await client.get("/activities")
    data = response.json()

    # Assert
    for name, details in data.items():
        assert required_fields.issubset(details.keys()), f"{name} missing fields"


@pytest.mark.anyio
async def test_get_activities_includes_known_activity(client):
    # Arrange
    known_activity = "Chess Club"

    # Act
    response = await client.get("/activities")
    data = response.json()

    # Assert
    assert known_activity in data
    assert data[known_activity]["max_participants"] == 12


# ─── POST /activities/{name}/signup ───────────────────────────────────────────


@pytest.mark.anyio
async def test_signup_success(client):
    # Arrange
    activity_name = "Chess Club"
    new_email = "newstudent@mergington.edu"

    # Act
    response = await client.post(
        f"/activities/{activity_name}/signup?email={new_email}"
    )

    # Assert
    assert response.status_code == 200
    assert new_email in response.json()["message"]
    assert new_email in activities[activity_name]["participants"]


@pytest.mark.anyio
async def test_signup_duplicate_returns_400(client):
    # Arrange
    activity_name = "Chess Club"
    existing_email = "michael@mergington.edu"  # already a participant

    # Act
    response = await client.post(
        f"/activities/{activity_name}/signup?email={existing_email}"
    )

    # Assert
    assert response.status_code == 400
    assert "already signed up" in response.json()["detail"].lower()


@pytest.mark.anyio
async def test_signup_nonexistent_activity_returns_404(client):
    # Arrange
    fake_activity = "Underwater Basket Weaving"
    email = "test@mergington.edu"

    # Act
    response = await client.post(
        f"/activities/{fake_activity}/signup?email={email}"
    )

    # Assert
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


# ─── DELETE /activities/{name}/signup ─────────────────────────────────────────


@pytest.mark.anyio
async def test_unregister_success(client):
    # Arrange
    activity_name = "Chess Club"
    email = "michael@mergington.edu"  # already a participant

    # Act
    response = await client.delete(
        f"/activities/{activity_name}/signup?email={email}"
    )

    # Assert
    assert response.status_code == 200
    assert email in response.json()["message"]
    assert email not in activities[activity_name]["participants"]


@pytest.mark.anyio
async def test_unregister_not_signed_up_returns_400(client):
    # Arrange
    activity_name = "Chess Club"
    email = "unknown@mergington.edu"

    # Act
    response = await client.delete(
        f"/activities/{activity_name}/signup?email={email}"
    )

    # Assert
    assert response.status_code == 400
    assert "not signed up" in response.json()["detail"].lower()


@pytest.mark.anyio
async def test_unregister_nonexistent_activity_returns_404(client):
    # Arrange
    fake_activity = "Nonexistent Club"
    email = "test@mergington.edu"

    # Act
    response = await client.delete(
        f"/activities/{fake_activity}/signup?email={email}"
    )

    # Assert
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
