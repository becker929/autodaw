"""
Test suite for audio comparison API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_root_endpoint():
    """Test the root health check endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert "Audio Comparison API operational" in response.json()["message"]

def test_get_audio_files():
    """Test retrieving all audio files."""
    response = client.get("/api/audio-files")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_next_comparison():
    """Test retrieving next comparison pair."""
    response = client.get("/api/comparisons/next")
    assert response.status_code == 200
    # Should return a comparison pair or null

def test_get_stats():
    """Test retrieving comparison statistics."""
    response = client.get("/api/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_comparisons" in data
    assert "completed_comparisons" in data
    assert "preference_distribution" in data

def test_submit_preference():
    """Test submitting a preference for a comparison."""
    # First get a comparison
    comparison_response = client.get("/api/comparisons/next")
    if comparison_response.json() is None:
        pytest.skip("No comparisons available")

    comparison = comparison_response.json()

    # Submit preference
    preference_data = {
        "comparison_id": comparison["id"],
        "preference": "a",
        "confidence": 0.8,
        "notes": "Test preference"
    }

    response = client.post(f"/api/comparisons/{comparison['id']}/preference",
                          json=preference_data)
    assert response.status_code == 200
    assert "successfully" in response.json()["message"]

def test_invalid_preference():
    """Test submitting invalid preference data."""
    # Get a comparison first
    comparison_response = client.get("/api/comparisons/next")
    if comparison_response.json() is None:
        pytest.skip("No comparisons available")

    comparison = comparison_response.json()

    # Submit invalid preference
    invalid_data = {
        "comparison_id": comparison["id"],
        "preference": "invalid",
        "confidence": 0.8
    }

    response = client.post(f"/api/comparisons/{comparison['id']}/preference",
                          json=invalid_data)
    assert response.status_code == 400
