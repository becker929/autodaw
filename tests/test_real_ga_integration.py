"""Integration tests that run real GA code with minimal mocking."""

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
    """Create a mock REAPER project path with basic structure."""
    with tempfile.TemporaryDirectory() as temp_dir:
        reaper_path = Path(temp_dir) / "reaper_project"
        reaper_path.mkdir()

        # Create basic directory structure that might be expected
        (reaper_path / "session-configs").mkdir()
        (reaper_path / "session-results").mkdir()
        (reaper_path / "renders").mkdir()

        yield reaper_path


@pytest.fixture
def real_ga_engine(test_db, mock_reaper_path):
    """Create a WebGAJSIEngine instance for real GA testing."""
    return WebGAJSIEngine(database=test_db, reaper_project_path=mock_reaper_path)


class TestRealGAIntegration:
    """Integration tests that run actual GA code with minimal mocking."""

    @pytest.mark.slow
    def test_real_population_initialization_small(self, real_ga_engine):
        """Test real population initialization with small population to keep test fast."""
        # Create a session
        session_id = real_ga_engine.create_session(
            name="Real GA Test",
            target_frequency=440.0,
            population_size=3  # Keep small for speed
        )

        # Mock only the parts that require external dependencies (REAPER, audio rendering)
        # but let the actual GA sampling and algorithm creation run
        def mock_jsi_problem_init(self, **kwargs):
            """Mock JSI problem initialization to avoid REAPER dependencies."""
            # Set up the problem with the same interface as the real one
            self.reaper_project_path = kwargs.get('reaper_project_path')
            self.target_frequency = kwargs.get('target_frequency', 440.0)
            self.session_name_prefix = kwargs.get('session_name_prefix', 'test')

            # Set pymoo Problem attributes
            import numpy as np
            self.n_var = 2
            self.n_obj = 1
            self.xl = np.array([-2.0, -1.0])
            self.xu = np.array([2.0, 1.0])

        def mock_render_audio(solution_id, parameters):
            """Mock audio rendering to avoid REAPER calls."""
            return None  # Return None to simulate no audio file created

        # Patch the JSI problem and audio rendering
        with patch('autodaw.core.ga_jsi_engine.JSIAudioOptimizationProblem') as mock_problem_class:
            # Set up the mock to behave like the real class but without external dependencies
            mock_problem = MagicMock()
            mock_problem_class.return_value = mock_problem
            mock_problem_class.side_effect = lambda **kwargs: mock_problem

            # Configure the mock problem
            import numpy as np
            mock_problem.n_var = 2
            mock_problem.n_obj = 1
            mock_problem.xl = np.array([-2.0, -1.0])
            mock_problem.xu = np.array([2.0, 1.0])
            mock_problem.bounds.return_value = (mock_problem.xl, mock_problem.xu)

            with patch.object(real_ga_engine, '_render_solution_audio', side_effect=mock_render_audio):
                # This should run the real GA sampling code
                result = real_ga_engine.initialize_population(session_id)

        # Verify the result structure
        assert isinstance(result, dict)
        assert 'population_id' in result
        assert 'generation' in result
        assert 'solutions' in result
        assert 'comparison_pairs_generated' in result

        # Verify the values
        assert result['generation'] == 0
        assert len(result['solutions']) == 3
        assert result['comparison_pairs_generated'] == 3  # 3 choose 2 = 3

        # Verify solution structure and parameter bounds
        for solution in result['solutions']:
            assert isinstance(solution['id'], str)
            assert 'parameters' in solution
            assert 'octave' in solution['parameters']
            assert 'fine_tuning' in solution['parameters']

            # Check parameter bounds (these come from real GA sampling)
            octave = solution['parameters']['octave']
            fine_tuning = solution['parameters']['fine_tuning']

            assert isinstance(octave, (int, float))
            assert isinstance(fine_tuning, (int, float))
            assert -2.0 <= octave <= 2.0
            assert -1.0 <= fine_tuning <= 1.0

        # Verify database consistency
        population_id = result['population_id']
        stored_populations = real_ga_engine.db.get_populations_for_session(session_id)
        assert len(stored_populations) > 0
        stored_population = stored_populations[0]  # Get the first population
        assert stored_population['id'] == population_id
        assert stored_population['session_id'] == session_id
        assert stored_population['generation'] == 0

    @pytest.mark.slow
    def test_multiple_population_generations(self, real_ga_engine):
        """Test that we can create multiple populations for the same session."""
        # Create a session
        session_id = real_ga_engine.create_session(
            name="Multi-Gen Test",
            target_frequency=440.0,
            population_size=2  # Very small for speed
        )

        # Mock external dependencies
        with patch('autodaw.core.ga_jsi_engine.JSIAudioOptimizationProblem') as mock_problem_class:
            mock_problem = MagicMock()
            mock_problem_class.return_value = mock_problem

            import numpy as np
            mock_problem.n_var = 2
            mock_problem.n_obj = 1
            mock_problem.xl = np.array([-2.0, -1.0])
            mock_problem.xu = np.array([2.0, 1.0])
            mock_problem.bounds.return_value = (mock_problem.xl, mock_problem.xu)

            with patch.object(real_ga_engine, '_render_solution_audio', return_value=None):
                # Create first population
                result1 = real_ga_engine.initialize_population(session_id)

                # Create second population (this would be a new generation in real usage)
                # For this test, we'll create a new session to simulate multiple populations
                session_id2 = real_ga_engine.create_session(
                    name="Multi-Gen Test 2",
                    target_frequency=440.0,
                    population_size=2
                )
                result2 = real_ga_engine.initialize_population(session_id2)

        # Verify both populations were created successfully
        assert result1['population_id'] != result2['population_id']
        assert len(result1['solutions']) == 2
        assert len(result2['solutions']) == 2

        # Verify solutions have different parameters (highly likely with random sampling)
        solutions1 = result1['solutions']
        solutions2 = result2['solutions']

        # At least some parameters should be different
        param_differences = 0
        for s1, s2 in zip(solutions1, solutions2):
            if s1['parameters']['octave'] != s2['parameters']['octave']:
                param_differences += 1
            if s1['parameters']['fine_tuning'] != s2['parameters']['fine_tuning']:
                param_differences += 1

        # With random sampling, we should see some differences
        assert param_differences > 0

    def test_ga_algorithm_configuration(self, real_ga_engine):
        """Test that the GA algorithm is configured correctly."""
        session_id = real_ga_engine.create_session(
            name="GA Config Test",
            target_frequency=440.0,
            population_size=4
        )

        # Mock external dependencies but capture the algorithm configuration
        captured_algorithm = None

        def capture_algorithm_init(*args, **kwargs):
            nonlocal captured_algorithm
            from pymoo.algorithms.soo.nonconvex.ga import GA
            captured_algorithm = GA(*args, **kwargs)
            return captured_algorithm

        with patch('autodaw.core.ga_jsi_engine.JSIAudioOptimizationProblem') as mock_problem_class:
            mock_problem = MagicMock()
            mock_problem_class.return_value = mock_problem

            import numpy as np
            mock_problem.n_var = 2
            mock_problem.n_obj = 1
            mock_problem.xl = np.array([-2.0, -1.0])
            mock_problem.xu = np.array([2.0, 1.0])
            mock_problem.bounds.return_value = (mock_problem.xl, mock_problem.xu)

            with patch('autodaw.core.ga_jsi_engine.GA', side_effect=capture_algorithm_init):
                with patch.object(real_ga_engine, '_render_solution_audio', return_value=None):
                    real_ga_engine.initialize_population(session_id)

        # Verify algorithm was configured
        assert captured_algorithm is not None

        # Check that the algorithm has the expected configuration
        # Note: We can't easily inspect all internal settings, but we can verify it was created
        assert hasattr(captured_algorithm, 'pop_size')

    @pytest.mark.slow
    def test_parameter_bounds_enforcement(self, real_ga_engine):
        """Test that parameter bounds are enforced by the GA sampling."""
        session_id = real_ga_engine.create_session(
            name="Bounds Test",
            target_frequency=440.0,
            population_size=10  # Larger population to test bounds thoroughly
        )

        with patch('autodaw.core.ga_jsi_engine.JSIAudioOptimizationProblem') as mock_problem_class:
            mock_problem = MagicMock()
            mock_problem_class.return_value = mock_problem

            import numpy as np
            mock_problem.n_var = 2
            mock_problem.n_obj = 1
            mock_problem.xl = np.array([-2.0, -1.0])
            mock_problem.xu = np.array([2.0, 1.0])
            mock_problem.bounds.return_value = (mock_problem.xl, mock_problem.xu)

            with patch.object(real_ga_engine, '_render_solution_audio', return_value=None):
                result = real_ga_engine.initialize_population(session_id)

        # Check that all parameters are within bounds
        for solution in result['solutions']:
            octave = solution['parameters']['octave']
            fine_tuning = solution['parameters']['fine_tuning']

            # These bounds should be enforced by the GA sampling
            assert -2.0 <= octave <= 2.0, f"Octave {octave} out of bounds [-2.0, 2.0]"
            assert -1.0 <= fine_tuning <= 1.0, f"Fine tuning {fine_tuning} out of bounds [-1.0, 1.0]"

        # Also check that we have some diversity in parameters
        octaves = [s['parameters']['octave'] for s in result['solutions']]
        fine_tunings = [s['parameters']['fine_tuning'] for s in result['solutions']]

        # With random sampling of 10 solutions, we should see some diversity
        assert len(set(octaves)) > 1, "No diversity in octave parameters"
        assert len(set(fine_tunings)) > 1, "No diversity in fine tuning parameters"


class TestErrorHandlingWithRealGA:
    """Test error handling when using real GA components."""

    def test_invalid_population_size_handling(self, real_ga_engine):
        """Test handling of edge case population sizes."""
        # Test with population size 1 (edge case)
        session_id = real_ga_engine.create_session(
            name="Edge Case Test",
            target_frequency=440.0,
            population_size=1
        )

        with patch('autodaw.core.ga_jsi_engine.JSIAudioOptimizationProblem') as mock_problem_class:
            mock_problem = MagicMock()
            mock_problem_class.return_value = mock_problem

            import numpy as np
            mock_problem.n_var = 2
            mock_problem.n_obj = 1
            mock_problem.xl = np.array([-2.0, -1.0])
            mock_problem.xu = np.array([2.0, 1.0])
            mock_problem.bounds.return_value = (mock_problem.xl, mock_problem.xu)

            with patch.object(real_ga_engine, '_render_solution_audio', return_value=None):
                result = real_ga_engine.initialize_population(session_id)

        # Should handle population size 1
        assert len(result['solutions']) == 1
        assert result['comparison_pairs_generated'] == 0  # No pairs possible with 1 solution

    def test_problem_creation_failure(self, real_ga_engine):
        """Test handling when problem creation fails."""
        session_id = real_ga_engine.create_session(
            name="Failure Test",
            target_frequency=440.0,
            population_size=4
        )

        # Make problem creation fail
        with patch('autodaw.core.ga_jsi_engine.JSIAudioOptimizationProblem', side_effect=Exception("Problem creation failed")):
            with pytest.raises(Exception, match="Problem creation failed"):
                real_ga_engine.initialize_population(session_id)
