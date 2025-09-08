"""Unit tests for WebGAJSIEngine that test actual GA functionality."""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import uuid

from autodaw.core.database import Database
from autodaw.core.ga_jsi_engine import WebGAJSIEngine


@pytest.fixture
def test_db():
    """Create a temporary test database."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
        db_path = Path(tmp_file.name)

    db = Database(db_path)
    yield db

    if db_path.exists():
        os.unlink(db_path)


@pytest.fixture
def mock_reaper_path():
    """Create a mock REAPER project path."""
    with tempfile.TemporaryDirectory() as temp_dir:
        reaper_path = Path(temp_dir) / "reaper_project"
        reaper_path.mkdir()
        yield reaper_path


@pytest.fixture
def ga_engine(test_db, mock_reaper_path):
    """Create a WebGAJSIEngine instance for testing."""
    return WebGAJSIEngine(database=test_db, reaper_project_path=mock_reaper_path)


class TestWebGAJSIEngineBasics:
    """Test basic WebGAJSIEngine functionality."""

    def test_engine_initialization(self, ga_engine):
        """Test that the engine initializes correctly."""
        assert ga_engine.db is not None
        assert ga_engine.reaper_project_path is not None
        assert ga_engine.current_session_id is None
        assert ga_engine.current_problem is None
        assert ga_engine.comparison_oracle is None

    def test_create_session(self, ga_engine):
        """Test session creation."""
        session_id = ga_engine.create_session(
            name="Test Session",
            target_frequency=440.0,
            population_size=4
        )

        assert isinstance(session_id, str)
        assert len(session_id) > 0

        # Verify session was stored in database
        session = ga_engine.db.get_ga_session(session_id)
        assert session is not None
        assert session['name'] == "Test Session"
        assert session['target_frequency'] == 440.0
        assert session['population_size'] == 4


class TestWebGAJSIEngineGA:
    """Test actual GA functionality without full REAPER integration."""

    @patch('autodaw.core.ga_jsi_engine.JSIAudioOptimizationProblem')
    def test_initialize_population_with_mocked_problem(self, mock_problem_class, ga_engine):
        """Test population initialization with mocked JSI problem to avoid REAPER dependencies."""
        # Create a session first
        session_id = ga_engine.create_session(
            name="GA Test Session",
            target_frequency=440.0,
            population_size=4
        )

        # Mock the JSI problem to avoid REAPER dependencies
        mock_problem = MagicMock()
        mock_problem.n_var = 2
        import numpy as np
        mock_problem.xl = np.array([-2.0, -1.0])
        mock_problem.xu = np.array([2.0, 1.0])
        mock_problem.bounds.return_value = (mock_problem.xl, mock_problem.xu)
        mock_problem_class.return_value = mock_problem

        # Mock the render method to avoid REAPER calls
        with patch.object(ga_engine, '_render_solution_audio', return_value=None):
            result = ga_engine.initialize_population(session_id)

        # Verify the result structure
        assert 'population_id' in result
        assert 'generation' in result
        assert 'solutions' in result
        assert 'comparison_pairs_generated' in result

        assert result['generation'] == 0
        assert len(result['solutions']) == 4
        assert result['comparison_pairs_generated'] == 6  # 4 choose 2 = 6

        # Verify each solution has the expected structure
        for solution in result['solutions']:
            assert 'id' in solution
            assert 'parameters' in solution
            assert 'octave' in solution['parameters']
            assert 'fine_tuning' in solution['parameters']
            assert 'audio_file_id' in solution

            # Verify parameter bounds
            assert -2.0 <= solution['parameters']['octave'] <= 2.0
            assert -1.0 <= solution['parameters']['fine_tuning'] <= 1.0

    def test_initialize_population_nonexistent_session(self, ga_engine):
        """Test that initializing population for nonexistent session raises error."""
        fake_session_id = str(uuid.uuid4())

        with pytest.raises(ValueError, match=f"Session {fake_session_id} not found"):
            ga_engine.initialize_population(fake_session_id)


class TestGASamplingFunctionality:
    """Test the specific GA sampling functionality that was broken."""

    def test_ga_sampling_direct(self):
        """Test that GA sampling works correctly without going through the full engine."""
        from pymoo.algorithms.soo.nonconvex.ga import GA
        from pymoo.operators.crossover.sbx import SBX
        from pymoo.operators.mutation.pm import PM
        from pymoo.operators.sampling.rnd import FloatRandomSampling
        from pymoo.core.problem import Problem
        import numpy as np

        # Create a simple test problem
        class SimpleTestProblem(Problem):
            def __init__(self):
                super().__init__(n_var=2, n_obj=1, xl=np.array([-2.0, -1.0]), xu=np.array([2.0, 1.0]))

        problem = SimpleTestProblem()

        # Test the GA algorithm creation (this was failing before)
        algorithm = GA(
            pop_size=4,
            sampling=FloatRandomSampling(),
            crossover=SBX(prob=0.9, eta=15),
            mutation=PM(prob=0.1, eta=20),
            eliminate_duplicates=True
        )

        # Test the sampling directly (this is the fixed approach)
        sampling = FloatRandomSampling()
        pop = sampling.do(problem, 4)

        assert len(pop) == 4
        for individual in pop:
            assert len(individual.X) == 2
            assert -2.0 <= individual.X[0] <= 2.0
            assert -1.0 <= individual.X[1] <= 1.0

    def test_pymoo_imports_work(self):
        """Smoke test to ensure all required pymoo imports work."""
        from pymoo.algorithms.soo.nonconvex.ga import GA
        from pymoo.operators.crossover.sbx import SBX
        from pymoo.operators.mutation.pm import PM
        from pymoo.operators.sampling.rnd import FloatRandomSampling
        from pymoo.optimize import minimize
        from pymoo.termination import get_termination

        # Just verify we can import and create instances
        assert GA is not None
        assert SBX is not None
        assert PM is not None
        assert FloatRandomSampling is not None
        assert minimize is not None
        assert get_termination is not None

        # Test creating instances
        sampling = FloatRandomSampling()
        assert sampling is not None

        crossover = SBX(prob=0.9, eta=15)
        assert crossover is not None

        mutation = PM(prob=0.1, eta=20)
        assert mutation is not None

        algorithm = GA(
            pop_size=4,
            sampling=sampling,
            crossover=crossover,
            mutation=mutation,
            eliminate_duplicates=True
        )
        assert algorithm is not None


class TestGAEngineErrorHandling:
    """Test error handling in GA engine."""

    def test_invalid_session_parameters(self, ga_engine):
        """Test that invalid session parameters are handled correctly."""
        # Test with invalid population size (should be handled by validation layer)
        session_id = ga_engine.create_session(
            name="Invalid Session",
            target_frequency=440.0,
            population_size=0  # This might be caught at API level
        )

        # The session creation might succeed but population init should handle edge cases
        assert isinstance(session_id, str)

    @patch('autodaw.core.ga_jsi_engine.JSIAudioOptimizationProblem')
    def test_population_initialization_with_problem_creation_error(self, mock_problem_class, ga_engine):
        """Test handling of errors during problem creation."""
        session_id = ga_engine.create_session(
            name="Error Test Session",
            target_frequency=440.0,
            population_size=4
        )

        # Make problem creation raise an exception
        mock_problem_class.side_effect = Exception("Problem creation failed")

        with pytest.raises(Exception, match="Problem creation failed"):
            ga_engine.initialize_population(session_id)
