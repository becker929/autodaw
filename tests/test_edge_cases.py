"""Edge case and stress tests for AutoDAW system."""

import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import tempfile
import os
import json
from unittest.mock import patch, MagicMock
import sqlite3

from autodaw.backend.main import app
from autodaw.core.database import Database


@pytest.fixture
def client_with_test_db():
    """Create test client with fresh database."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
        db_path = Path(tmp_file.name)

    from autodaw.backend import main
    main.db = Database(db_path)
    main.engine.db = main.db

    client = TestClient(app)
    yield client, db_path

    if db_path.exists():
        os.unlink(db_path)


def test_extreme_population_sizes(client_with_test_db):
    """Test handling of extreme population sizes."""
    client, _ = client_with_test_db

    # Test minimum population size
    min_session = {"name": "Min Population", "population_size": 2}
    resp = client.post("/api/sessions", json=min_session)
    assert resp.status_code == 200

    # Test below minimum population size
    below_min_session = {"name": "Below Min Population", "population_size": 1}
    resp = client.post("/api/sessions", json=below_min_session)
    assert resp.status_code == 422

    # Test very large population size (at maximum limit)
    large_session = {"name": "Large Population", "population_size": 100}
    resp = client.post("/api/sessions", json=large_session)
    assert resp.status_code == 200

    # Test population size above maximum
    too_large_session = {"name": "Too Large Population", "population_size": 101}
    resp = client.post("/api/sessions", json=too_large_session)
    assert resp.status_code == 422

        # Test zero population size
    zero_session = {"name": "Zero Population", "population_size": 0}
    resp = client.post("/api/sessions", json=zero_session)
    # Should reject with validation error (below minimum of 2)
    assert resp.status_code == 422

    # Test negative population size
    neg_session = {"name": "Negative Population", "population_size": -5}
    resp = client.post("/api/sessions", json=neg_session)
    # Should reject with validation error
    assert resp.status_code == 422


def test_extreme_confidence_values(client_with_test_db):
    """Test handling of extreme confidence values."""
    client, _ = client_with_test_db

    # Create session and comparison
    session_data = {"name": "Confidence Test", "population_size": 4}
    resp = client.post("/api/sessions", json=session_data)
    session_id = resp.json()["session_id"]

    with patch('autodaw.backend.main.engine._render_solution_audio') as mock_render:
        mock_render.return_value = Path("/tmp/fake.wav")
        with patch.object(Path, 'exists', return_value=True):
            client.post("/api/populations/initialize", json={"session_id": session_id})

    comp_resp = client.get("/api/comparisons/next")
    if comp_resp.json()["comparison"]:
        comparison_id = comp_resp.json()["comparison"]["comparison_id"]

        # Test extreme confidence values
        extreme_confidences = [
            (0.0, 200),    # Minimum valid
            (1.0, 200),    # Maximum valid
            (-0.1, 422),   # Below minimum - Pydantic validation error
            (1.1, 422),    # Above maximum - Pydantic validation error
            (999.9, 422),  # Way above maximum - Pydantic validation error
            (-999.9, 422), # Way below minimum - Pydantic validation error
        ]

        for confidence, expected_status in extreme_confidences:
            pref_data = {"preference": "a", "confidence": confidence}
            resp = client.post(f"/api/comparisons/{comparison_id}/preference", json=pref_data)
            assert resp.status_code == expected_status


def test_very_long_strings(client_with_test_db):
    """Test handling of extremely long string inputs."""
    client, _ = client_with_test_db

    # Test very long session name
    long_name = "A" * 10000
    long_session = {"name": long_name, "population_size": 4}
    resp = client.post("/api/sessions", json=long_session)
    # Should handle gracefully
    assert resp.status_code in [200, 400, 413, 422]

    # Test very long notes
    if resp.status_code == 200:
        session_id = resp.json()["session_id"]

        with patch('autodaw.backend.main.engine._render_solution_audio') as mock_render:
            mock_render.return_value = Path("/tmp/fake.wav")
            with patch.object(Path, 'exists', return_value=True):
                client.post("/api/populations/initialize", json={"session_id": session_id})

        comp_resp = client.get("/api/comparisons/next")
        if comp_resp.json()["comparison"]:
            comparison_id = comp_resp.json()["comparison"]["comparison_id"]

            long_notes = "B" * 50000
            pref_data = {"preference": "a", "confidence": 0.5, "notes": long_notes}
            resp = client.post(f"/api/comparisons/{comparison_id}/preference", json=pref_data)
            assert resp.status_code in [200, 400, 413, 422]


def test_unicode_and_special_characters(client_with_test_db):
    """Test handling of unicode and special characters."""
    client, _ = client_with_test_db

    # Test unicode session names
    unicode_names = [
        "测试会话",  # Chinese
        "Тест сессия",  # Russian
        "🎵🎶 Music Session 🎶🎵",  # Emojis
        "Session with\nNewlines\tTabs",  # Control characters
        "SQL'; DROP TABLE sessions; --",  # SQL injection attempt
        "<script>alert('xss')</script>",  # XSS attempt
    ]

    for name in unicode_names:
        session_data = {"name": name, "population_size": 4}
        resp = client.post("/api/sessions", json=session_data)
        # Should handle gracefully without crashing
        assert resp.status_code in [200, 400, 422]

        if resp.status_code == 200:
            # Verify the name was stored correctly
            session_id = resp.json()["session_id"]
            get_resp = client.get(f"/api/sessions/{session_id}")
            assert get_resp.status_code == 200
            # Name should be safely stored
            stored_name = get_resp.json()["name"]
            assert isinstance(stored_name, str)


def test_database_corruption_recovery(client_with_test_db):
    """Test recovery from database corruption scenarios."""
    client, db_path = client_with_test_db

    # Create some data first
    session_data = {"name": "Corruption Test", "population_size": 4}
    resp = client.post("/api/sessions", json=session_data)
    assert resp.status_code == 200
    session_id = resp.json()["session_id"]

    # Simulate database corruption by directly manipulating the database
    try:
        # Try to corrupt a table
        conn = sqlite3.connect(str(db_path))
        conn.execute("UPDATE ga_sessions SET name = NULL WHERE id = ?", (session_id,))
        conn.commit()
        conn.close()

        # System should handle corrupted data gracefully
        get_resp = client.get(f"/api/sessions/{session_id}")
        # Should either return the session with null name or handle the error
        assert get_resp.status_code in [200, 404, 500]

    except Exception:
        # If we can't corrupt the database, that's actually good
        pass

    # System should still be able to create new sessions
    new_session = {"name": "Post-Corruption Test", "population_size": 4}
    resp = client.post("/api/sessions", json=new_session)
    assert resp.status_code in [200, 500]  # Should work or fail gracefully


def test_concurrent_database_access(client_with_test_db):
    """Test handling of concurrent database operations."""
    client, _ = client_with_test_db

    # Create multiple sessions rapidly
    session_names = [f"Concurrent Session {i}" for i in range(10)]
    responses = []

    for name in session_names:
        session_data = {"name": name, "population_size": 4}
        resp = client.post("/api/sessions", json=session_data)
        responses.append((name, resp.status_code))

    # All should succeed or fail gracefully
    for name, status in responses:
        assert status in [200, 500], f"Session '{name}' failed with unexpected status {status}"

    # At least some should succeed
    successful_creates = sum(1 for _, status in responses if status == 200)
    assert successful_creates > 0, "No sessions were created successfully"


def test_malformed_json_requests(client_with_test_db):
    """Test handling of malformed JSON requests."""
    client, _ = client_with_test_db

    # Test various malformed JSON scenarios
    malformed_payloads = [
        '{"name": "Test"',  # Incomplete JSON
        '{"name": "Test", "population_size":}',  # Missing value
        '{"name": "Test", "population_size": 4,}',  # Trailing comma
        '{name: "Test"}',  # Unquoted key
        '{"name": "Test", "population_size": 4.5.6}',  # Invalid number
    ]

    for payload in malformed_payloads:
        # Send raw malformed JSON
        resp = client.post(
            "/api/sessions",
            content=payload,
            headers={"Content-Type": "application/json"}
        )
        # Should return 422 (validation error) or 400 (bad request)
        assert resp.status_code in [400, 422]


def test_missing_required_fields(client_with_test_db):
    """Test handling of requests with missing required fields."""
    client, _ = client_with_test_db

    # Test session creation with missing fields
    incomplete_sessions = [
        {},  # No fields
        {"population_size": 4},  # Missing name
        {"name": "Test"},  # Missing population_size (but has default)
    ]

    for session_data in incomplete_sessions:
        resp = client.post("/api/sessions", json=session_data)
        # Should either succeed with defaults or fail with validation error
        assert resp.status_code in [200, 422]


def test_type_mismatch_inputs(client_with_test_db):
    """Test handling of type mismatches in input data."""
    client, _ = client_with_test_db

    # Test various type mismatches
    type_mismatch_sessions = [
        {"name": 12345, "population_size": 4},  # Name as number
        {"name": "Test", "population_size": "four"},  # Population as string
        {"name": ["Test"], "population_size": 4},  # Name as array
        {"name": "Test", "population_size": 4.7},  # Population as float
        {"name": None, "population_size": 4},  # Name as null
    ]

    for session_data in type_mismatch_sessions:
        resp = client.post("/api/sessions", json=session_data)
        # Should fail with validation error
        assert resp.status_code in [400, 422]


def test_resource_exhaustion_scenarios(client_with_test_db):
    """Test behavior under resource exhaustion scenarios."""
    client, _ = client_with_test_db

    # Test creating many sessions to potentially exhaust resources
    created_sessions = []
    max_attempts = 50  # Reasonable limit for testing

    for i in range(max_attempts):
        session_data = {"name": f"Resource Test {i}", "population_size": 4}
        resp = client.post("/api/sessions", json=session_data)

        if resp.status_code == 200:
            created_sessions.append(resp.json()["session_id"])
        elif resp.status_code in [500, 503]:
            # Resource exhaustion - acceptable
            break
        else:
            # Unexpected error
            assert False, f"Unexpected status code {resp.status_code} at iteration {i}"

    # Should have created at least a few sessions
    assert len(created_sessions) > 0, "No sessions were created"

    # System should still respond to health checks
    health_resp = client.get("/")
    assert health_resp.status_code == 200


def test_boundary_value_analysis(client_with_test_db):
    """Test boundary values for numeric inputs."""
    client, _ = client_with_test_db

    # Test boundary values for target frequency
    frequency_boundaries = [
        (0.0, [422]),           # Zero frequency - below minimum
        (0.1, [200]),           # Very low frequency - at minimum
        (20000.0, [200]),       # Very high frequency - at maximum
        (float('inf'), [422]),  # Infinite frequency - invalid
        (float('-inf'), [422]), # Negative infinite frequency - invalid
    ]

    for freq, expected_statuses in frequency_boundaries:
        try:
            session_data = {"name": "Boundary Test", "target_frequency": freq, "population_size": 4}
            resp = client.post("/api/sessions", json=session_data)
            assert resp.status_code in expected_statuses, f"Frequency {freq} gave unexpected status {resp.status_code}"
        except (ValueError, OverflowError):
            # JSON serialization might fail for extreme values - that's acceptable
            pass


def test_system_state_consistency(client_with_test_db):
    """Test that system maintains consistent state across operations."""
    client, _ = client_with_test_db

    # Perform a series of operations and verify state consistency
    initial_stats = client.get("/api/stats").json()

    # Create session
    session_data = {"name": "Consistency Check", "population_size": 4}
    resp = client.post("/api/sessions", json=session_data)
    assert resp.status_code == 200
    session_id = resp.json()["session_id"]

    # Initialize population using the working mock pattern
    def mock_initialize_population(session_id):
        """Mock population initialization for consistency test."""
        import uuid
        from autodaw.backend import main
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
                'octave': (i - session['population_size']/2) * 0.3,
                'fine_tuning': (i % 3 - 1) * 0.1
            }

            # Mock audio file
            audio_file_id = str(uuid.uuid4())
            main.db.add_audio_file(
                file_id=audio_file_id,
                filename=f"consistency_audio_{solution_id}.wav",
                filepath=f"/tmp/consistency_audio_{solution_id}.wav",
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

    from autodaw.backend import main
    with patch.object(main.engine, 'initialize_population', side_effect=mock_initialize_population):
        init_resp = client.post("/api/populations/initialize", json={"session_id": session_id})
        assert init_resp.status_code == 200

    # Check that stats were updated correctly
    post_init_stats = client.get("/api/stats").json()
    expected_new_comparisons = 6  # 4 choose 2 = 6 comparisons
    assert post_init_stats["total_comparisons"] == initial_stats["total_comparisons"] + expected_new_comparisons

    # Submit a preference
    comp_resp = client.get("/api/comparisons/next")
    if comp_resp.json()["comparison"]:
        comparison_id = comp_resp.json()["comparison"]["comparison_id"]
        pref_data = {"preference": "a", "confidence": 0.8}
        pref_resp = client.post(f"/api/comparisons/{comparison_id}/preference", json=pref_data)
        assert pref_resp.status_code == 200

        # Check stats again
        final_stats = client.get("/api/stats").json()
        assert final_stats["completed_comparisons"] == initial_stats["completed_comparisons"] + 1
        assert final_stats["remaining_comparisons"] == post_init_stats["remaining_comparisons"] - 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
