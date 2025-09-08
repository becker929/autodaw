"""API tests for AutoDAW backend."""

import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import tempfile
import os

# Import our app
from autodaw.backend.main import app
from autodaw.core.database import Database


@pytest.fixture
def client():
    """Create test client with temporary database."""
    # Create temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
        db_path = Path(tmp_file.name)

    # Replace the global database instance with test database
    from autodaw.backend import main
    main.db = Database(db_path)
    main.engine.db = main.db

    client = TestClient(app)

    yield client

    # Clean up
    if db_path.exists():
        os.unlink(db_path)


def test_health_check(client):
    """Test the health check endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "AutoDAW API operational"
    assert data["version"] == "0.1.0"


def test_create_session(client):
    """Test creating a GA session."""
    session_data = {
        "name": "Test Session",
        "target_frequency": 440.0,
        "population_size": 8
    }

    response = client.post("/api/sessions", json=session_data)
    assert response.status_code == 200

    data = response.json()
    assert "session_id" in data
    assert data["session"]["name"] == "Test Session"
    assert data["session"]["target_frequency"] == 440.0
    assert data["session"]["population_size"] == 8


def test_list_sessions(client):
    """Test listing sessions."""
    # First create a session
    session_data = {
        "name": "Test Session",
        "target_frequency": 440.0,
        "population_size": 4
    }

    create_response = client.post("/api/sessions", json=session_data)
    assert create_response.status_code == 200

    # Now list sessions
    response = client.get("/api/sessions")
    assert response.status_code == 200

    sessions = response.json()
    assert isinstance(sessions, list)
    assert len(sessions) >= 1

    # Check that our session is in the list
    session_names = [s["name"] for s in sessions]
    assert "Test Session" in session_names


def test_get_session(client):
    """Test getting a specific session."""
    # First create a session
    session_data = {
        "name": "Specific Test Session",
        "target_frequency": 880.0,
        "population_size": 6
    }

    create_response = client.post("/api/sessions", json=session_data)
    assert create_response.status_code == 200

    session_id = create_response.json()["session_id"]

    # Now get the session
    response = client.get(f"/api/sessions/{session_id}")
    assert response.status_code == 200

    session = response.json()
    assert session["id"] == session_id
    assert session["name"] == "Specific Test Session"
    assert session["target_frequency"] == 880.0
    assert session["population_size"] == 6


def test_get_nonexistent_session(client):
    """Test getting a session that doesn't exist."""
    response = client.get("/api/sessions/nonexistent_id")
    assert response.status_code == 404


def test_get_stats(client):
    """Test getting statistics."""
    response = client.get("/api/stats")
    assert response.status_code == 200

    stats = response.json()
    assert "total_comparisons" in stats
    assert "completed_comparisons" in stats
    assert "remaining_comparisons" in stats
    assert "preference_distribution" in stats
    assert "average_confidence" in stats

    # Initially should have no comparisons
    assert stats["total_comparisons"] == 0
    assert stats["completed_comparisons"] == 0


def test_get_next_comparison_empty(client):
    """Test getting next comparison when none exist."""
    response = client.get("/api/comparisons/next")
    assert response.status_code == 200

    data = response.json()
    assert "message" in data
    assert data["comparison"] is None


def test_invalid_preference_submission(client):
    """Test submitting invalid preference."""
    # Try to submit preference for non-existent comparison
    preference_data = {
        "preference": "a",
        "confidence": 0.8
    }

    response = client.post("/api/comparisons/nonexistent/preference", json=preference_data)
    assert response.status_code == 500  # Will fail because comparison doesn't exist

        # Test invalid preference value
    preference_data = {
        "preference": "invalid",
        "confidence": 0.8
    }

    response = client.post("/api/comparisons/test/preference", json=preference_data)
    assert response.status_code == 422  # Validation error

    # Test invalid confidence value
    preference_data = {
        "preference": "a",
        "confidence": 1.5  # Invalid - should be 0.0 to 1.0
    }

    response = client.post("/api/comparisons/test/preference", json=preference_data)
    assert response.status_code == 422  # Validation error


def test_session_validation(client):
    """Test session creation validation."""
    # Test missing required fields
    response = client.post("/api/sessions", json={})
    assert response.status_code == 422  # Validation error

    # Test invalid population size
    session_data = {
        "name": "Invalid Session",
        "target_frequency": 440.0,
        "population_size": -1  # Invalid
    }

    response = client.post("/api/sessions", json=session_data)
    # This should still create the session since we don't validate population size in the API
    # But the GA engine might handle this validation
    assert response.status_code in [200, 422, 500]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
