"""Basic tests for AutoDAW functionality."""

import pytest
from pathlib import Path
import tempfile
import os

from autodaw.core.database import Database


def test_database_initialization():
    """Test that database initializes correctly."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
        db_path = Path(tmp_file.name)

    try:
        db = Database(db_path)

        # Test that tables were created
        with db.get_connection() as conn:
            tables = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()

        table_names = [table[0] for table in tables]

        expected_tables = [
            'audio_files', 'populations', 'solutions', 'comparisons',
            'bt_strengths', 'ga_sessions'
        ]

        for table in expected_tables:
            assert table in table_names, f"Table {table} not found"

    finally:
        # Clean up
        if db_path.exists():
            os.unlink(db_path)


def test_session_creation():
    """Test GA session creation."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
        db_path = Path(tmp_file.name)

    try:
        db = Database(db_path)

        # Create a session
        session_id = "test_session_123"
        success = db.create_ga_session(
            session_id=session_id,
            name="Test Session",
            target_frequency=440.0,
            population_size=8
        )

        assert success

        # Retrieve the session
        session = db.get_ga_session(session_id)
        assert session is not None
        assert session['name'] == "Test Session"
        assert session['target_frequency'] == 440.0
        assert session['population_size'] == 8

    finally:
        if db_path.exists():
            os.unlink(db_path)


def test_audio_file_operations():
    """Test audio file database operations."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
        db_path = Path(tmp_file.name)

    try:
        db = Database(db_path)

        # Add an audio file
        file_id = "test_audio_123"
        success = db.add_audio_file(
            file_id=file_id,
            filename="test.wav",
            filepath="/path/to/test.wav",
            duration=3.5,
            metadata={"sample_rate": 44100}
        )

        assert success

        # Retrieve the audio file
        audio_file = db.get_audio_file(file_id)
        assert audio_file is not None
        assert audio_file['filename'] == "test.wav"
        assert audio_file['duration'] == 3.5
        assert audio_file['metadata']['sample_rate'] == 44100

    finally:
        if db_path.exists():
            os.unlink(db_path)


def test_comparison_operations():
    """Test comparison database operations."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
        db_path = Path(tmp_file.name)

    try:
        db = Database(db_path)

        # First create some solutions (we need these for comparisons)
        session_id = "test_session"
        population_id = "test_population"
        solution_a_id = "solution_a"
        solution_b_id = "solution_b"

        db.create_ga_session(session_id, "Test", population_size=4)
        db.add_population(population_id, session_id, 0)
        db.add_solution(solution_a_id, population_id, {"octave": 1.0})
        db.add_solution(solution_b_id, population_id, {"octave": 2.0})

        # Add a comparison
        comparison_id = "test_comparison_123"
        success = db.add_comparison(
            comparison_id=comparison_id,
            solution_a_id=solution_a_id,
            solution_b_id=solution_b_id
        )

        assert success

        # Check it's in pending comparisons
        pending = db.get_pending_comparisons()
        assert len(pending) == 1
        assert pending[0]['id'] == comparison_id

        # Submit a preference
        success = db.submit_comparison_preference(
            comparison_id=comparison_id,
            preference="a",
            confidence=0.8,
            notes="Option A sounds better"
        )

        assert success

        # Check it's no longer pending
        pending = db.get_pending_comparisons()
        assert len(pending) == 0

        # Check the preference was recorded
        comparison = db.get_comparison(comparison_id)
        assert comparison['preference'] == "a"
        assert comparison['confidence'] == 0.8
        assert comparison['notes'] == "Option A sounds better"

    finally:
        if db_path.exists():
            os.unlink(db_path)


if __name__ == "__main__":
    # Run basic tests
    test_database_initialization()
    test_session_creation()
    test_audio_file_operations()
    test_comparison_operations()
    print("All basic tests passed!")
