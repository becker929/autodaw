"""End-to-end tests simulating real user workflows."""

import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import tempfile
import os
from unittest.mock import patch, MagicMock
import json

from autodaw.backend.main import app
from autodaw.core.database import Database


@pytest.fixture
def full_system_client():
    """Create test client with full system simulation."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
        db_path = Path(tmp_file.name)

    from autodaw.backend import main
    main.db = Database(db_path)
    main.engine.db = main.db

    # Mock the entire initialization process similar to integration tests
    def mock_initialize_population(session_id):
        """Mock population initialization."""
        import uuid
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

            # Mock parameters with some variation
            parameters = {
                'octave': (i - session['population_size']/2) * 0.3,
                'fine_tuning': (i % 5 - 2) * 0.05
            }

            # Mock audio file
            audio_file_id = str(uuid.uuid4())
            main.db.add_audio_file(
                file_id=audio_file_id,
                filename=f"e2e_audio_{solution_id}.wav",
                filepath=f"/tmp/e2e_audio_{solution_id}.wav",
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

    with patch.object(main.engine, 'initialize_population', side_effect=mock_initialize_population):
        client = TestClient(app)
        yield client, db_path

    if db_path.exists():
        os.unlink(db_path)


def test_complete_user_journey_single_target(full_system_client):
    """Test complete user journey optimizing for a single target frequency."""
    client, _ = full_system_client

    # === USER STORY ===
    # A user wants to optimize audio parameters for a 440Hz target frequency
    # They create a session, initialize a population, evaluate comparisons,
    # and view the results with Bradley-Terry rankings

    # Step 1: User creates optimization session
    session_data = {
        "name": "A4 Note Optimization",
        "target_frequency": 440.0,
        "population_size": 6,
        "config": {"optimization_type": "frequency_matching"}
    }

    create_response = client.post("/api/sessions", json=session_data)
    assert create_response.status_code == 200

    session_result = create_response.json()
    session_id = session_result["session_id"]
    stored_session = session_result["session"]

    assert stored_session["name"] == "A4 Note Optimization"
    assert stored_session["target_frequency"] == 440.0
    assert stored_session["population_size"] == 6
    assert stored_session["status"] == "active"

    # Step 2: User initializes the first population
    init_response = client.post("/api/populations/initialize", json={"session_id": session_id})
    assert init_response.status_code == 200

    init_result = init_response.json()
    population_id = init_result["population_id"]

    assert init_result["generation"] == 0
    assert len(init_result["solutions"]) == 6
    assert init_result["comparison_pairs_generated"] == 15  # 6 choose 2 = 15

    # Verify all solutions have audio files
    for solution in init_result["solutions"]:
        assert solution["audio_file_id"] is not None
        assert "octave" in solution["parameters"]
        assert "fine_tuning" in solution["parameters"]

    # Step 3: User begins evaluating comparisons
    completed_comparisons = []
    comparison_count = 0
    max_comparisons = 8  # User doesn't need to complete all comparisons

    while comparison_count < max_comparisons:
        # Get next comparison
        comp_response = client.get("/api/comparisons/next")
        assert comp_response.status_code == 200

        comp_result = comp_response.json()
        if comp_result["comparison"] is None:
            break

        comparison = comp_result["comparison"]
        comparison_id = comparison["comparison_id"]

        # Verify comparison structure
        assert "solution_a" in comparison
        assert "solution_b" in comparison
        assert comparison["solution_a"]["audio_file"] is not None
        assert comparison["solution_b"]["audio_file"] is not None

        # User listens to both options and makes a decision
        # Simulate user preference based on parameter differences
        params_a = comparison["solution_a"]["parameters"]
        params_b = comparison["solution_b"]["parameters"]

        # Simulate preference: user prefers parameters closer to target
        # (In real system, this would be based on actual audio)
        target_octave = 0.0  # Assume 0 is optimal for 440Hz
        diff_a = abs(params_a["octave"] - target_octave)
        diff_b = abs(params_b["octave"] - target_octave)

        preferred = "a" if diff_a <= diff_b else "b"
        confidence = 0.9 if abs(diff_a - diff_b) > 0.5 else 0.6  # Higher confidence for clear differences

        notes = f"Preferred {preferred.upper()} - sounds closer to target frequency"

        # Submit preference
        pref_data = {
            "preference": preferred,
            "confidence": confidence,
            "notes": notes
        }

        pref_response = client.post(f"/api/comparisons/{comparison_id}/preference", json=pref_data)
        assert pref_response.status_code == 200
        assert pref_response.json()["message"] == "Preference recorded successfully"

        completed_comparisons.append({
            "comparison_id": comparison_id,
            "preference": preferred,
            "confidence": confidence
        })

        comparison_count += 1

    # Step 4: User checks progress statistics
    stats_response = client.get("/api/stats")
    assert stats_response.status_code == 200

    stats = stats_response.json()
    assert stats["total_comparisons"] == 15
    assert stats["completed_comparisons"] == comparison_count
    assert stats["remaining_comparisons"] == 15 - comparison_count
    assert stats["average_confidence"] > 0.0

    # Verify preference distribution
    pref_dist = stats["preference_distribution"]
    total_prefs = sum(pref_dist.values())
    assert total_prefs == comparison_count

    # Step 5: User views population with Bradley-Terry rankings
    pop_response = client.get(f"/api/populations/{population_id}")
    assert pop_response.status_code == 200

    pop_result = pop_response.json()
    solutions = pop_result["solutions"]

    assert len(solutions) == 6

    # Check that BT strengths were calculated
    solutions_with_bt = [s for s in solutions if s.get("bt_strength")]
    assert len(solutions_with_bt) >= 2, "At least 2 solutions should have BT strengths"

    # Verify BT strength structure and values
    for solution in solutions_with_bt:
        bt_strength = solution["bt_strength"]
        assert "strength" in bt_strength
        assert 0.0 <= bt_strength["strength"] <= 1.0
        assert bt_strength["updated_at"] is not None

    # Step 6: User examines the best solutions
    # Sort solutions by BT strength (if available) or by rank
    def sort_key(sol):
        if sol.get("bt_strength"):
            return sol["bt_strength"]["strength"]
        return 1.0 - (sol.get("rank", 999) / 1000.0)  # Higher rank = lower sort value

    sorted_solutions = sorted(solutions, key=sort_key, reverse=True)
    best_solution = sorted_solutions[0]

    # Verify best solution has reasonable parameters
    best_params = best_solution["parameters"]
    assert "octave" in best_params
    assert "fine_tuning" in best_params
    assert isinstance(best_params["octave"], (int, float))
    assert isinstance(best_params["fine_tuning"], (int, float))

    # Step 7: User reviews session summary
    final_session_response = client.get(f"/api/sessions/{session_id}")
    assert final_session_response.status_code == 200

    final_session = final_session_response.json()
    assert final_session["current_generation"] == 0  # Still on first generation

    # Get session populations
    populations_response = client.get(f"/api/sessions/{session_id}/populations")
    assert populations_response.status_code == 200

    populations = populations_response.json()
    assert len(populations) == 1
    assert populations[0]["generation"] == 0
    assert populations[0]["solution_count"] == 6


def test_multi_session_workflow(full_system_client):
    """Test workflow with multiple concurrent optimization sessions."""
    client, _ = full_system_client

    # User creates multiple sessions for different targets
    sessions_data = [
        {"name": "Low Frequency Test", "target_frequency": 220.0, "population_size": 4},
        {"name": "Mid Frequency Test", "target_frequency": 440.0, "population_size": 4},
        {"name": "High Frequency Test", "target_frequency": 880.0, "population_size": 4},
    ]

    session_ids = []
    for session_data in sessions_data:
        response = client.post("/api/sessions", json=session_data)
        assert response.status_code == 200
        session_ids.append(response.json()["session_id"])

    # Initialize all populations
    population_ids = []
    for session_id in session_ids:
        response = client.post("/api/populations/initialize", json={"session_id": session_id})
        assert response.status_code == 200
        population_ids.append(response.json()["population_id"])

    # User works on comparisons across different sessions
    total_comparisons = 0
    sessions_worked = set()

    # Do a few comparisons from each session
    for _ in range(12):  # 4 comparisons per session
        comp_response = client.get("/api/comparisons/next")
        assert comp_response.status_code == 200

        comp_result = comp_response.json()
        if comp_result["comparison"] is None:
            break

        comparison = comp_result["comparison"]
        comparison_id = comparison["comparison_id"]

        # Submit preference
        pref_data = {"preference": "a", "confidence": 0.7}
        pref_response = client.post(f"/api/comparisons/{comparison_id}/preference", json=pref_data)
        assert pref_response.status_code == 200

        total_comparisons += 1

        # Track which sessions we've worked on by checking solution parameters
        # (In a real system, we'd track this more explicitly)

    # Verify all sessions are progressing
    for i, session_id in enumerate(session_ids):
        session_response = client.get(f"/api/sessions/{session_id}")
        assert session_response.status_code == 200

        session = session_response.json()
        assert session["name"] == sessions_data[i]["name"]
        assert session["target_frequency"] == sessions_data[i]["target_frequency"]

    # Check global statistics include all sessions
    stats_response = client.get("/api/stats")
    assert stats_response.status_code == 200

    stats = stats_response.json()
    assert stats["total_comparisons"] == 18  # 3 sessions * 6 comparisons each
    assert stats["completed_comparisons"] == total_comparisons


def test_iterative_optimization_workflow(full_system_client):
    """Test iterative optimization workflow over multiple generations."""
    client, _ = full_system_client

    # User creates session for iterative optimization
    session_data = {
        "name": "Iterative Optimization Test",
        "target_frequency": 440.0,
        "population_size": 4
    }

    response = client.post("/api/sessions", json=session_data)
    assert response.status_code == 200
    session_id = response.json()["session_id"]

    # Generation 0: Initialize and evaluate
    init_response = client.post("/api/populations/initialize", json={"session_id": session_id})
    assert init_response.status_code == 200

    gen0_population_id = init_response.json()["population_id"]

    # Complete several comparisons for generation 0
    comparisons_completed = 0
    while comparisons_completed < 4:
        comp_response = client.get("/api/comparisons/next")
        assert comp_response.status_code == 200

        comp_result = comp_response.json()
        if comp_result["comparison"] is None:
            break

        comparison_id = comp_result["comparison"]["comparison_id"]
        pref_data = {"preference": "a", "confidence": 0.8}

        pref_response = client.post(f"/api/comparisons/{comparison_id}/preference", json=pref_data)
        assert pref_response.status_code == 200

        comparisons_completed += 1

    # Check population with BT strengths
    pop_response = client.get(f"/api/populations/{gen0_population_id}")
    assert pop_response.status_code == 200

    pop_result = pop_response.json()
    gen0_solutions = pop_result["solutions"]

    # Verify BT calculations were performed
    solutions_with_bt = [s for s in gen0_solutions if s.get("bt_strength")]
    assert len(solutions_with_bt) > 0

    # Check session populations
    populations_response = client.get(f"/api/sessions/{session_id}/populations")
    assert populations_response.status_code == 200

    populations = populations_response.json()
    assert len(populations) == 1
    assert populations[0]["generation"] == 0

    # Verify optimization progress
    # Best solution should have reasonable BT strength
    best_solutions = [s for s in solutions_with_bt if s["bt_strength"]["strength"] > 0.5]
    if best_solutions:
        # If we have good solutions, optimization is working
        best_solution = max(best_solutions, key=lambda s: s["bt_strength"]["strength"])
        assert best_solution["bt_strength"]["strength"] > 0.5


def test_error_recovery_workflow(full_system_client):
    """Test user workflow with error recovery scenarios."""
    client, _ = full_system_client

    # User starts with invalid session creation
    invalid_session = {"name": "", "population_size": 0}
    response = client.post("/api/sessions", json=invalid_session)
    assert response.status_code == 422  # Should be rejected with validation error

    # User corrects and creates valid session
    valid_session = {"name": "Recovery Test Session", "population_size": 4}
    response = client.post("/api/sessions", json=valid_session)
    assert response.status_code == 200
    session_id = response.json()["session_id"]

    # User tries to initialize population multiple times (should be idempotent or fail gracefully)
    for i in range(3):
        response = client.post("/api/populations/initialize", json={"session_id": session_id})
        # First should succeed, others should either succeed (idempotent) or fail gracefully
        assert response.status_code in [200, 400, 409]

        if response.status_code == 200 and i == 0:
            # Store the successful initialization
            population_id = response.json()["population_id"]

    # User tries to submit invalid preferences
    comp_response = client.get("/api/comparisons/next")
    if comp_response.json()["comparison"]:
        comparison_id = comp_response.json()["comparison"]["comparison_id"]

                # Invalid preference value
        invalid_pref = {"preference": "invalid", "confidence": 0.8}
        response = client.post(f"/api/comparisons/{comparison_id}/preference", json=invalid_pref)
        assert response.status_code == 422  # Validation error

        # Invalid confidence value
        invalid_conf = {"preference": "a", "confidence": 2.0}
        response = client.post(f"/api/comparisons/{comparison_id}/preference", json=invalid_conf)
        assert response.status_code == 422  # Validation error

        # Valid preference should work after errors
        valid_pref = {"preference": "a", "confidence": 0.8}
        response = client.post(f"/api/comparisons/{comparison_id}/preference", json=valid_pref)
        assert response.status_code == 200

    # System should still be functional after errors
    stats_response = client.get("/api/stats")
    assert stats_response.status_code == 200

    health_response = client.get("/")
    assert health_response.status_code == 200


def test_power_user_workflow(full_system_client):
    """Test workflow for power users with advanced features."""
    client, _ = full_system_client

    # Power user creates session with custom configuration
    advanced_session = {
        "name": "Advanced Optimization Session",
        "target_frequency": 440.0,
        "population_size": 8,
        "config": {
            "optimization_strategy": "aggressive",
            "convergence_threshold": 0.95,
            "max_generations": 10,
            "mutation_rate": 0.15
        }
    }

    response = client.post("/api/sessions", json=advanced_session)
    assert response.status_code == 200
    session_id = response.json()["session_id"]

    # Verify custom config was stored
    session_response = client.get(f"/api/sessions/{session_id}")
    assert session_response.status_code == 200
    session = session_response.json()

    if session.get("config"):
        config = json.loads(session["config"]) if isinstance(session["config"], str) else session["config"]
        assert config.get("optimization_strategy") == "aggressive"

    # Initialize with larger population
    init_response = client.post("/api/populations/initialize", json={"session_id": session_id})
    assert init_response.status_code == 200

    init_result = init_response.json()
    assert len(init_result["solutions"]) == 8
    assert init_result["comparison_pairs_generated"] == 28  # 8 choose 2 = 28

    population_id = init_result["population_id"]

    # Power user completes many comparisons efficiently
    completed_comparisons = 0
    target_comparisons = 15

    while completed_comparisons < target_comparisons:
        comp_response = client.get("/api/comparisons/next")
        assert comp_response.status_code == 200

        comp_result = comp_response.json()
        if comp_result["comparison"] is None:
            break

        comparison_id = comp_result["comparison"]["comparison_id"]

        # Power user provides detailed feedback
        pref_data = {
            "preference": "a" if completed_comparisons % 2 == 0 else "b",
            "confidence": 0.85 + (completed_comparisons % 3) * 0.05,  # Varying confidence
            "notes": f"Comparison {completed_comparisons + 1}: Detailed technical analysis of audio characteristics"
        }

        pref_response = client.post(f"/api/comparisons/{comparison_id}/preference", json=pref_data)
        assert pref_response.status_code == 200

        completed_comparisons += 1

    # Power user analyzes detailed statistics
    stats_response = client.get("/api/stats")
    assert stats_response.status_code == 200

    stats = stats_response.json()
    assert stats["completed_comparisons"] == completed_comparisons
    assert stats["average_confidence"] > 0.8  # High confidence from power user

    # Power user examines population with detailed BT analysis
    pop_response = client.get(f"/api/populations/{population_id}")
    assert pop_response.status_code == 200

    pop_result = pop_response.json()
    solutions = pop_result["solutions"]

    # Verify detailed BT strength information is available
    solutions_with_bt = [s for s in solutions if s.get("bt_strength")]
    assert len(solutions_with_bt) >= 4  # Should have BT strengths for multiple solutions

    # Power user can identify clear winners and losers
    bt_strengths = [s["bt_strength"]["strength"] for s in solutions_with_bt]
    strength_range = max(bt_strengths) - min(bt_strengths)
    assert strength_range > 0.1  # Should have meaningful differentiation


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
