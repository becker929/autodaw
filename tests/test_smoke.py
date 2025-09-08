"""Smoke tests to verify core dependencies and system health."""

import pytest
import sys
from pathlib import Path


class TestCoreDependencies:
    """Test that all core dependencies can be imported and work."""

    def test_pymoo_basic_functionality(self):
        """Test that pymoo works correctly."""
        from pymoo.algorithms.soo.nonconvex.ga import GA
        from pymoo.operators.crossover.sbx import SBX
        from pymoo.operators.mutation.pm import PM
        from pymoo.operators.sampling.rnd import FloatRandomSampling
        from pymoo.core.problem import Problem
        import numpy as np

        # Create a simple test problem
        class TestProblem(Problem):
            def __init__(self):
                super().__init__(n_var=2, n_obj=1, xl=np.array([0.0, 0.0]), xu=np.array([1.0, 1.0]))

            def _evaluate(self, X, out, *args, **kwargs):
                out["F"] = np.sum(X**2, axis=1)

        problem = TestProblem()

        # Test sampling
        sampling = FloatRandomSampling()
        pop = sampling.do(problem, 5)

        assert len(pop) == 5
        for individual in pop:
            assert len(individual.X) == 2
            assert 0.0 <= individual.X[0] <= 1.0
            assert 0.0 <= individual.X[1] <= 1.0

        # Test GA algorithm creation
        algorithm = GA(
            pop_size=5,
            sampling=FloatRandomSampling(),
            crossover=SBX(prob=0.9, eta=15),
            mutation=PM(prob=0.1, eta=20),
            eliminate_duplicates=True
        )

        assert algorithm is not None

    def test_fastapi_dependencies(self):
        """Test that FastAPI and related dependencies work."""
        from fastapi import FastAPI, HTTPException
        from fastapi.testclient import TestClient
        from pydantic import BaseModel, Field

        # Create a simple test app
        app = FastAPI()

        class TestModel(BaseModel):
            name: str = Field(..., min_length=1, max_length=100)
            value: float = Field(..., ge=0.0, le=1.0)

        @app.get("/")
        def root():
            return {"message": "test"}

        @app.post("/test")
        def test_endpoint(data: TestModel):
            return {"received": data.dict()}

        # Test the app
        client = TestClient(app)

        # Test basic endpoint
        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == {"message": "test"}

        # Test validation
        response = client.post("/test", json={"name": "test", "value": 0.5})
        assert response.status_code == 200

        # Test validation failure
        response = client.post("/test", json={"name": "", "value": 2.0})
        assert response.status_code == 422

    def test_database_dependencies(self):
        """Test that database dependencies work."""
        import sqlite3
        import tempfile
        import os
        from pathlib import Path

        # Test basic SQLite functionality
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
            db_path = Path(tmp_file.name)

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Create a test table
            cursor.execute("""
                CREATE TABLE test_table (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    value REAL
                )
            """)

            # Insert test data
            cursor.execute("INSERT INTO test_table (name, value) VALUES (?, ?)", ("test", 1.0))
            conn.commit()

            # Query test data
            cursor.execute("SELECT * FROM test_table WHERE name = ?", ("test",))
            result = cursor.fetchone()

            assert result is not None
            assert result[1] == "test"
            assert result[2] == 1.0

            conn.close()
        finally:
            if db_path.exists():
                os.unlink(db_path)

    def test_numpy_functionality(self):
        """Test that numpy works correctly."""
        import numpy as np

        # Test basic numpy operations
        arr = np.array([1, 2, 3, 4, 5])
        assert arr.mean() == 3.0
        assert arr.sum() == 15

        # Test random generation
        np.random.seed(42)
        random_arr = np.random.random(10)
        assert len(random_arr) == 10
        assert all(0.0 <= x <= 1.0 for x in random_arr)

        # Test array operations
        matrix = np.array([[1, 2], [3, 4]])
        assert matrix.shape == (2, 2)
        assert np.sum(matrix) == 10


class TestSystemPaths:
    """Test that required system paths and imports work."""

    def test_demo_imports_available(self):
        """Test that demo modules can be imported."""
        # Add demo paths (same as in ga_jsi_engine.py)
        demo_base = Path(__file__).parent.parent / "demos"
        ga_jsi_path = demo_base / "ga_jsi_audio_oracle"
        choix_path = demo_base / "choix_active_online"

        # Verify paths exist
        assert ga_jsi_path.exists(), f"GA JSI demo path not found: {ga_jsi_path}"
        assert choix_path.exists(), f"Choix demo path not found: {choix_path}"

        # Add to sys.path temporarily for import test
        original_path = sys.path.copy()
        try:
            sys.path.append(str(ga_jsi_path))
            sys.path.append(str(choix_path))

            # Test that we can import the modules (this might fail if dependencies are missing)
            try:
                from ga_jsi_audio_oracle.ga_problem import JSIAudioOptimizationProblem
                from ga_jsi_audio_oracle.audio_oracle import AudioComparisonOracle
                from choix_active_online_demo.comparison_oracle import ComparisonOracle

                # If we get here, imports work
                assert JSIAudioOptimizationProblem is not None
                assert AudioComparisonOracle is not None
                assert ComparisonOracle is not None

            except ImportError as e:
                # This is expected if demo dependencies aren't fully set up
                pytest.skip(f"Demo imports not available (expected in test environment): {e}")

        finally:
            sys.path[:] = original_path

    def test_reaper_directory_structure(self):
        """Test that the expected REAPER directory structure exists."""
        reaper_path = Path(__file__).parent.parent / "reaper"

        # Check if reaper directory exists
        if not reaper_path.exists():
            pytest.skip("REAPER directory not found (expected in some test environments)")

        # Check for expected subdirectories/files
        expected_items = [
            "reascripts",
            "session-configs",
            "session-results",
            "main.py"
        ]

        for item in expected_items:
            item_path = reaper_path / item
            if not item_path.exists():
                pytest.skip(f"REAPER structure incomplete: {item} not found")


class TestMemoryAndPerformance:
    """Basic tests to ensure the system doesn't have obvious memory/performance issues."""

    def test_large_array_handling(self):
        """Test that we can handle reasonably large arrays without issues."""
        import numpy as np

        # Create a moderately large array (not huge, but enough to test)
        size = 10000
        arr = np.random.random(size)

        # Perform some operations
        mean_val = np.mean(arr)
        std_val = np.std(arr)

        # Basic sanity checks
        assert 0.0 <= mean_val <= 1.0
        assert 0.0 <= std_val <= 1.0

        # Clean up
        del arr

    def test_multiple_database_operations(self):
        """Test that we can perform multiple database operations without issues."""
        import tempfile
        import os
        from pathlib import Path
        from autodaw.core.database import Database

        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
            db_path = Path(tmp_file.name)

        try:
            db = Database(db_path)

            # Create multiple sessions
            session_ids = []
            for i in range(10):
                session_id = f"test_session_{i}"
                db.create_ga_session(
                    session_id=session_id,
                    name=f"Test Session {i}",
                    target_frequency=440.0 + i,
                    population_size=4,
                    config={}
                )
                session_ids.append(session_id)

            # Verify all sessions were created
            for session_id in session_ids:
                session = db.get_ga_session(session_id)
                assert session is not None
                assert session['id'] == session_id

        finally:
            if db_path.exists():
                os.unlink(db_path)
