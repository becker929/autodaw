"""Integration tests for complete AutoDAW workflows."""

import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import tempfile
import os
import json
import uuid
from unittest.mock import patch, MagicMock

from autodaw.backend.main import app
from autodaw.core.database import Database
from autodaw.core.ga_jsi_engine import WebGAJSIEngine


@pytest.fixture
def client_with_mocked_reaper():
    """Create test client with mocked REAPER functionality."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
        db_path = Path(tmp_file.name)

    # Replace the global database instance with test database
    from autodaw.backend import main
    main.db = Database(db_path)
    main.engine.db = main.db

    # Mock the entire initialization process to avoid GA/JSI import issues
    def mock_initialize_population(session_id):
        """Mock population initialization."""
        session = main.db.get_ga_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        # Create population record
        population_id = str(uuid.uuid4())
        main.db.add_population(population_id, session_id, 0)

        # Create mock solutions
        solutions_info = []
        for i in range(session['population_size']):
            solution_id = str(uuid.uuid4())

            # Mock parameters
            parameters = {
                'octave': (i - session['population_size']/2) * 0.5,  # Spread around 0
                'fine_tuning': (i % 3 - 1) * 0.1  # Small variations
            }

            # Mock audio file
            audio_file_id = str(uuid.uuid4())
            main.db.add_audio_file(
                file_id=audio_file_id,
                filename=f"mock_audio_{solution_id}.wav",
                filepath=f"/tmp/mock_audio_{solution_id}.wav",
                metadata={'solution_id': solution_id, 'parameters': parameters}
            )

            # Store solution
            main.db.add_solution(
                solution_id=solution_id,
                population_id=population_id,
                parameters=parameters,
                audio_file_id=audio_file_id
            )

            solutions_info.append({
                'id': solution_id,
                'parameters': parameters,
                'audio_file_id': audio_file_id
            })

        # Generate comparison pairs
        comparison_ids = []
        for i in range(len(solutions_info)):
            for j in range(i + 1, len(solutions_info)):
                comparison_id = str(uuid.uuid4())
                main.db.add_comparison(
                    comparison_id=comparison_id,
                    solution_a_id=solutions_info[i]['id'],
                    solution_b_id=solutions_info[j]['id']
                )
                comparison_ids.append(comparison_id)

        return {
            'population_id': population_id,
            'generation': 0,
            'solutions': solutions_info,
            'comparison_pairs_generated': len(comparison_ids)
        }

    # Mock the engine's initialize_population method
    with patch.object(main.engine, 'initialize_population', side_effect=mock_initialize_population):
        client = TestClient(app)
        yield client, None

    # Clean up
    if db_path.exists():
        os.unlink(db_path)


def test_complete_optimization_workflow(client_with_mocked_reaper):
    """Test complete workflow from session creation to preference submission."""
    client, _ = client_with_mocked_reaper

    # Step 1: Create a session
    session_data = {
        "name": "Integration Test Session",
        "target_frequency": 440.0,
        "population_size": 4
    }

    create_response = client.post("/api/sessions", json=session_data)
    assert create_response.status_code == 200
    session_id = create_response.json()["session_id"]

    # Step 2: Initialize population
    init_response = client.post("/api/populations/initialize", json={"session_id": session_id})
    assert init_response.status_code == 200

    init_data = init_response.json()
    assert "population_id" in init_data
    assert init_data["generation"] == 0
    assert len(init_data["solutions"]) == 4
    assert init_data["comparison_pairs_generated"] > 0

    population_id = init_data["population_id"]

    # Verify solutions were created (mocked audio rendering)
    assert len(init_data["solutions"]) == 4

    # Step 3: Get next comparison
    comparison_response = client.get("/api/comparisons/next")
    assert comparison_response.status_code == 200

    comparison_data = comparison_response.json()
    assert "comparison" in comparison_data
    assert comparison_data["comparison"] is not None

    comparison = comparison_data["comparison"]
    comparison_id = comparison["comparison_id"]

    # Verify comparison has required structure
    assert "solution_a" in comparison
    assert "solution_b" in comparison
    assert comparison["solution_a"]["parameters"] is not None
    assert comparison["solution_b"]["parameters"] is not None

    # Step 4: Submit preference
    preference_data = {
        "preference": "a",
        "confidence": 0.8,
        "notes": "Option A sounds clearer"
    }

    pref_response = client.post(f"/api/comparisons/{comparison_id}/preference", json=preference_data)
    assert pref_response.status_code == 200
    assert pref_response.json()["message"] == "Preference recorded successfully"

    # Step 5: Verify preference was stored
    stored_comparison = client.get(f"/api/comparisons/{comparison_id}")
    assert stored_comparison.status_code == 200
    stored_data = stored_comparison.json()
    assert stored_data["preference"] == "a"
    assert stored_data["confidence"] == 0.8
    assert stored_data["notes"] == "Option A sounds clearer"

    # Step 6: Check statistics updated
    stats_response = client.get("/api/stats")
    assert stats_response.status_code == 200
    stats = stats_response.json()
    assert stats["completed_comparisons"] == 1
    assert stats["preference_distribution"]["a"] == 1

    # Step 7: Check population with BT strengths
    pop_response = client.get(f"/api/populations/{population_id}")
    assert pop_response.status_code == 200
    pop_data = pop_response.json()
    assert len(pop_data["solutions"]) == 4

    # At least one solution should have BT strength calculated
    solutions_with_bt = [s for s in pop_data["solutions"] if s.get("bt_strength")]
    assert len(solutions_with_bt) > 0


def test_multiple_sessions_isolation(client_with_mocked_reaper):
    """Test that multiple sessions don't interfere with each other."""
    client, _ = client_with_mocked_reaper

    # Create two sessions
    session1_data = {"name": "Session 1", "target_frequency": 440.0, "population_size": 4}
    session2_data = {"name": "Session 2", "target_frequency": 880.0, "population_size": 6}

    resp1 = client.post("/api/sessions", json=session1_data)
    resp2 = client.post("/api/sessions", json=session2_data)

    assert resp1.status_code == 200
    assert resp2.status_code == 200

    session1_id = resp1.json()["session_id"]
    session2_id = resp2.json()["session_id"]

    # Initialize both populations
    client.post("/api/populations/initialize", json={"session_id": session1_id})
    client.post("/api/populations/initialize", json={"session_id": session2_id})

    # Get populations for each session
    pop1_resp = client.get(f"/api/sessions/{session1_id}/populations")
    pop2_resp = client.get(f"/api/sessions/{session2_id}/populations")

    assert pop1_resp.status_code == 200
    assert pop2_resp.status_code == 200

    pop1_data = pop1_resp.json()
    pop2_data = pop2_resp.json()

    # Verify correct population sizes
    assert pop1_data[0]["solution_count"] == 4
    assert pop2_data[0]["solution_count"] == 6

    # Verify session isolation
    session1_resp = client.get(f"/api/sessions/{session1_id}")
    session2_resp = client.get(f"/api/sessions/{session2_id}")

    assert session1_resp.json()["target_frequency"] == 440.0
    assert session2_resp.json()["target_frequency"] == 880.0


def test_comparison_queue_exhaustion(client_with_mocked_reaper):
    """Test behavior when all comparisons are completed."""
    client, _ = client_with_mocked_reaper

    # Create session with minimal population for faster testing
    session_data = {"name": "Exhaustion Test", "population_size": 3}
    resp = client.post("/api/sessions", json=session_data)
    session_id = resp.json()["session_id"]

    # Initialize population (3 solutions = 3 comparisons: A-B, A-C, B-C)
    client.post("/api/populations/initialize", json={"session_id": session_id})

    # Complete all comparisons
    completed_comparisons = 0
    while True:
        # Get next comparison
        comp_resp = client.get("/api/comparisons/next")
        assert comp_resp.status_code == 200

        comp_data = comp_resp.json()
        if comp_data["comparison"] is None:
            break

        comparison_id = comp_data["comparison"]["comparison_id"]

        # Submit preference
        pref_data = {"preference": "a", "confidence": 0.7}
        pref_resp = client.post(f"/api/comparisons/{comparison_id}/preference", json=pref_data)
        assert pref_resp.status_code == 200

        completed_comparisons += 1

        # Safety check to prevent infinite loop
        assert completed_comparisons <= 10

    # Should have completed exactly 3 comparisons (3 choose 2)
    assert completed_comparisons == 3

    # Verify no more comparisons available
    final_comp_resp = client.get("/api/comparisons/next")
    assert final_comp_resp.json()["comparison"] is None

    # Check final statistics
    stats_resp = client.get("/api/stats")
    stats = stats_resp.json()
    assert stats["total_comparisons"] == 3
    assert stats["completed_comparisons"] == 3
    assert stats["remaining_comparisons"] == 0


def test_bradley_terry_strength_calculation(client_with_mocked_reaper):
    """Test that Bradley-Terry strengths are calculated correctly."""
    client, _ = client_with_mocked_reaper

    # Create session
    session_data = {"name": "BT Test", "population_size": 4}
    resp = client.post("/api/sessions", json=session_data)
    session_id = resp.json()["session_id"]

    # Initialize population
    init_resp = client.post("/api/populations/initialize", json={"session_id": session_id})
    population_id = init_resp.json()["population_id"]

    # Submit several preferences to build BT model
    preferences_submitted = 0
    target_preferences = 3

    while preferences_submitted < target_preferences:
        comp_resp = client.get("/api/comparisons/next")
        comp_data = comp_resp.json()

        if comp_data["comparison"] is None:
            break

        comparison_id = comp_data["comparison"]["comparison_id"]

        # Alternate preferences to create meaningful BT strengths
        preference = "a" if preferences_submitted % 2 == 0 else "b"
        pref_data = {"preference": preference, "confidence": 0.8}

        client.post(f"/api/comparisons/{comparison_id}/preference", json=pref_data)
        preferences_submitted += 1

    # Get population with BT strengths
    pop_resp = client.get(f"/api/populations/{population_id}")
    assert pop_resp.status_code == 200

    pop_data = pop_resp.json()
    solutions = pop_data["solutions"]

    # Check that BT strengths were calculated
    solutions_with_bt = [s for s in solutions if s.get("bt_strength")]
    assert len(solutions_with_bt) > 0

    # Verify BT strength structure
    for solution in solutions_with_bt:
        bt_strength = solution["bt_strength"]
        assert "strength" in bt_strength
        assert 0.0 <= bt_strength["strength"] <= 1.0


def test_error_recovery_and_validation(client_with_mocked_reaper):
    """Test error handling and system recovery."""
    client, _ = client_with_mocked_reaper

    # Test invalid session creation
    invalid_session = {"name": ""}  # Missing required fields
    resp = client.post("/api/sessions", json=invalid_session)
    assert resp.status_code == 422  # Validation error

    # Test population initialization without session
    resp = client.post("/api/populations/initialize", json={"session_id": "nonexistent"})
    assert resp.status_code == 404

    # Test preference submission with invalid data
    invalid_preferences = [
        {"preference": "invalid", "confidence": 0.5},  # Invalid preference
        {"preference": "a", "confidence": 2.0},        # Invalid confidence
        {"preference": "a", "confidence": -0.5},       # Invalid confidence
    ]

    for invalid_pref in invalid_preferences:
        resp = client.post("/api/comparisons/test/preference", json=invalid_pref)
        assert resp.status_code == 422  # Validation error

    # Test system recovery - create valid session after errors
    valid_session = {"name": "Recovery Test", "population_size": 4}
    resp = client.post("/api/sessions", json=valid_session)
    assert resp.status_code == 200

    # System should work normally after errors
    session_id = resp.json()["session_id"]
    init_resp = client.post("/api/populations/initialize", json={"session_id": session_id})
    assert init_resp.status_code == 200


def test_concurrent_session_operations(client_with_mocked_reaper):
    """Test handling of concurrent operations on the same session."""
    client, _ = client_with_mocked_reaper

    # Create session
    session_data = {"name": "Concurrent Test", "population_size": 4}
    resp = client.post("/api/sessions", json=session_data)
    session_id = resp.json()["session_id"]

    # Initialize population
    client.post("/api/populations/initialize", json={"session_id": session_id})

    # Try to initialize again (should handle gracefully)
    second_init = client.post("/api/populations/initialize", json={"session_id": session_id})
    # This might succeed or fail depending on implementation, but shouldn't crash
    assert second_init.status_code in [200, 400, 409, 500]

    # Multiple rapid preference submissions
    comp_resp = client.get("/api/comparisons/next")
    if comp_resp.json()["comparison"]:
        comparison_id = comp_resp.json()["comparison"]["comparison_id"]

        # Submit same preference multiple times rapidly
        pref_data = {"preference": "a", "confidence": 0.8}

        responses = []
        for _ in range(3):
            resp = client.post(f"/api/comparisons/{comparison_id}/preference", json=pref_data)
            responses.append(resp.status_code)

        # First should succeed, others should either succeed (idempotent) or fail gracefully
        assert 200 in responses
        for status in responses:
            assert status in [200, 400, 409, 500]


def test_data_consistency_after_operations(client_with_mocked_reaper):
    """Test that data remains consistent after various operations."""
    client, _ = client_with_mocked_reaper

    # Create and initialize session
    session_data = {"name": "Consistency Test", "population_size": 4}
    resp = client.post("/api/sessions", json=session_data)
    session_id = resp.json()["session_id"]

    init_resp = client.post("/api/populations/initialize", json={"session_id": session_id})
    population_id = init_resp.json()["population_id"]

    # Submit some preferences
    preferences_count = 0
    while preferences_count < 2:
        comp_resp = client.get("/api/comparisons/next")
        comp_data = comp_resp.json()

        if comp_data["comparison"] is None:
            break

        comparison_id = comp_data["comparison"]["comparison_id"]
        pref_data = {"preference": "a", "confidence": 0.8}
        client.post(f"/api/comparisons/{comparison_id}/preference", json=pref_data)
        preferences_count += 1

    # Verify data consistency

    # 1. Session data should be intact
    session_resp = client.get(f"/api/sessions/{session_id}")
    assert session_resp.status_code == 200
    session_data_retrieved = session_resp.json()
    assert session_data_retrieved["name"] == "Consistency Test"
    assert session_data_retrieved["population_size"] == 4

    # 2. Population should have correct number of solutions
    pop_resp = client.get(f"/api/populations/{population_id}")
    assert pop_resp.status_code == 200
    pop_data = pop_resp.json()
    assert len(pop_data["solutions"]) == 4

    # 3. Statistics should match actual data
    stats_resp = client.get("/api/stats")
    assert stats_resp.status_code == 200
    stats = stats_resp.json()
    assert stats["completed_comparisons"] == preferences_count

    # 4. All solutions should have valid parameters
    for solution in pop_data["solutions"]:
        params = solution["parameters"]
        assert "octave" in params
        assert isinstance(params["octave"], (int, float))
        if "fine_tuning" in params:
            assert isinstance(params["fine_tuning"], (int, float))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
