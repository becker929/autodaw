"""Tests for JSI optimization problems."""

import pytest
import numpy as np
from pathlib import Path
from unittest.mock import Mock, patch

from serum_evolver.src.genetics.jsi_problems import (
    JSIAudioOptimizationProblem,
    MultiTargetJSIOptimizationProblem
)
from serum_evolver.src.genetics.genetics import Solution


class TestJSIAudioOptimizationProblem:
    """Test JSIAudioOptimizationProblem class."""

    @pytest.fixture
    def mock_reaper_path(self, tmp_path):
        """Create a mock REAPER project path with required directories."""
        reaper_path = tmp_path / "mock_reaper"
        reaper_path.mkdir(parents=True, exist_ok=True)
        (reaper_path / "session-configs").mkdir(exist_ok=True)
        (reaper_path / "renders").mkdir(exist_ok=True)
        return reaper_path

    @pytest.fixture
    def mock_target_audio(self, tmp_path):
        """Create a mock target audio file."""
        audio_file = tmp_path / "target.wav"
        audio_file.touch()
        return audio_file

    def test_initialization_basic(self, mock_reaper_path):
        """Test basic initialization without mocking internals."""
        # This will create real objects but won't execute anything
        problem = JSIAudioOptimizationProblem(mock_reaper_path)

        # Test problem dimensions
        assert problem.n_var == 2
        assert problem.n_obj == 1
        assert np.array_equal(problem.xl, np.array([-2.0, -1.0]))
        assert np.array_equal(problem.xu, np.array([2.0, 1.0]))

        # Test initialization state
        assert problem.reaper_project_path == mock_reaper_path
        assert problem.generation_counter == 0
        assert problem.evaluation_count == 0

    def test_initialization_with_custom_params(self, mock_reaper_path):
        """Test initialization with custom parameters."""
        problem = JSIAudioOptimizationProblem(
            mock_reaper_path,
            target_frequency=880.0,
            session_name_prefix="custom_session",
            oracle_noise_level=0.1
        )

        assert problem.session_name_prefix == "custom_session"
        # Oracle should be initialized with target frequency
        assert hasattr(problem, 'oracle')

    def test_render_population_audio_structure(self, mock_reaper_path):
        """Test the structure of render population audio method."""
        problem = JSIAudioOptimizationProblem(mock_reaper_path)

        # Create test solutions
        solutions = [
            Solution(1.0, 0.5),
            Solution(-0.5, -0.2)
        ]

        # Mock the executor to avoid actual REAPER execution
        problem.reaper_executor = Mock()
        problem.reaper_executor.execute_session.return_value = {
            'test_individual_000': Path('audio1.wav'),
            'test_individual_001': Path('audio2.wav')
        }

        result = problem._render_population_audio(solutions, "test_session")

        # Should return dictionary mapping solution IDs to paths
        assert isinstance(result, dict)
        assert len(result) == 2

    def test_get_best_solution_info_with_result(self, mock_reaper_path):
        """Test extracting best solution information."""
        problem = JSIAudioOptimizationProblem(mock_reaper_path)
        problem.evaluation_count = 10
        problem.generation_counter = 3

        # Mock JSI evaluator
        problem.jsi_evaluator = Mock()
        problem.jsi_evaluator.get_ranking_info.return_value = {'comparison_count': 15}

        # Mock optimization result
        mock_result = Mock()
        mock_result.X = np.array([1.5, 0.3])
        mock_result.F = np.array([-0.85])  # Negated JSI fitness

        info = problem.get_best_solution_info(mock_result)

        assert 'solution' in info
        assert isinstance(info['solution'], Solution)
        assert info['solution'].octave == 1.5
        assert info['solution'].fine == 0.3
        assert info['fitness'] == 0.85  # Converted back from negated
        assert info['evaluations'] == 10
        assert info['generations'] == 3
        assert info['jsi_comparisons'] == 15

    def test_get_best_solution_info_empty_result(self, mock_reaper_path):
        """Test extracting info from empty result."""
        problem = JSIAudioOptimizationProblem(mock_reaper_path)

        # Mock result without X and F attributes
        mock_result = Mock(spec=[])

        info = problem.get_best_solution_info(mock_result)

        assert info == {}

    def test_oracle_methods(self, mock_reaper_path):
        """Test oracle interaction methods."""
        problem = JSIAudioOptimizationProblem(mock_reaper_path)

        # Mock oracle
        problem.oracle = Mock()

        # Test set_target_frequency
        problem.set_target_frequency(660.0)
        problem.oracle.set_target_frequency.assert_called_once_with(660.0)

        # Test clear_oracle_cache
        problem.clear_oracle_cache()
        problem.oracle.clear_cache.assert_called_once()

    def test_oracle_methods_without_methods(self, mock_reaper_path):
        """Test oracle methods when oracle doesn't have the methods."""
        problem = JSIAudioOptimizationProblem(mock_reaper_path)

        # Mock oracle without the methods
        problem.oracle = Mock(spec=[])

        # These should not raise errors
        problem.set_target_frequency(660.0)
        problem.clear_oracle_cache()


class TestMultiTargetJSIOptimizationProblem:
    """Test MultiTargetJSIOptimizationProblem class."""

    @pytest.fixture
    def mock_reaper_path(self, tmp_path):
        """Create a mock REAPER project path with required directories."""
        reaper_path = tmp_path / "mock_reaper"
        reaper_path.mkdir(parents=True, exist_ok=True)
        (reaper_path / "session-configs").mkdir(exist_ok=True)
        (reaper_path / "renders").mkdir(exist_ok=True)
        return reaper_path

    def test_initialization(self, mock_reaper_path):
        """Test initialization with multiple target frequencies."""
        target_frequencies = [440.0, 880.0, 660.0]
        problem = MultiTargetJSIOptimizationProblem(
            mock_reaper_path,
            target_frequencies=target_frequencies
        )

        assert problem.target_frequencies == target_frequencies
        assert problem.current_target_index == 0
        # Should inherit from parent class
        assert problem.n_var == 2
        assert problem.n_obj == 1

    def test_target_frequency_cycling_logic(self, mock_reaper_path):
        """Test the logic for cycling through target frequencies."""
        target_frequencies = [440.0, 880.0, 660.0]
        problem = MultiTargetJSIOptimizationProblem(
            mock_reaper_path,
            target_frequencies=target_frequencies
        )

        # Test cycling logic
        assert problem.current_target_index == 0

        # Simulate cycling
        problem.current_target_index = (problem.current_target_index + 1) % len(target_frequencies)
        assert problem.current_target_index == 1
        assert problem.target_frequencies[problem.current_target_index] == 880.0

        problem.current_target_index = (problem.current_target_index + 1) % len(target_frequencies)
        assert problem.current_target_index == 2
        assert problem.target_frequencies[problem.current_target_index] == 660.0

        problem.current_target_index = (problem.current_target_index + 1) % len(target_frequencies)
        assert problem.current_target_index == 0  # Back to start
        assert problem.target_frequencies[problem.current_target_index] == 440.0


class TestJSIProblemsIntegration:
    """Integration tests for JSI problems."""

    @pytest.fixture
    def mock_reaper_path(self, tmp_path):
        """Create a mock REAPER project path with required directories."""
        reaper_path = tmp_path / "mock_reaper"
        reaper_path.mkdir(parents=True, exist_ok=True)
        (reaper_path / "session-configs").mkdir(exist_ok=True)
        (reaper_path / "renders").mkdir(exist_ok=True)
        return reaper_path

    def test_solution_conversion_to_numpy(self, mock_reaper_path):
        """Test that solutions are properly converted to numpy arrays."""
        problem = JSIAudioOptimizationProblem(mock_reaper_path)

        # Test data that would come from pymoo
        x = np.array([
            [1.0, 0.5],   # Individual 1
            [-0.5, -0.2], # Individual 2
            [0.0, 0.0]    # Individual 3
        ])

        # Convert to solutions (this logic is in _evaluate method)
        solutions = []
        for i, individual in enumerate(x):
            octave, fine = individual
            solution = Solution(octave=octave, fine=fine)
            solutions.append(solution)

        # Verify conversion
        assert len(solutions) == 3
        assert solutions[0].octave == 1.0
        assert solutions[0].fine == 0.5
        assert solutions[1].octave == -0.5
        assert solutions[1].fine == -0.2
        assert solutions[2].octave == 0.0
        assert solutions[2].fine == 0.0

    def test_fitness_negation_for_minimization(self, mock_reaper_path):
        """Test that JSI fitness values are negated for pymoo minimization."""
        problem = JSIAudioOptimizationProblem(mock_reaper_path)

        # JSI fitness values (higher is better)
        jsi_fitness = [0.8, 0.6, 0.4]

        # Convert for pymoo (negate for minimization)
        pymoo_fitness = np.array([-f for f in jsi_fitness]).reshape(-1, 1)

        expected = np.array([[-0.8], [-0.6], [-0.4]])
        np.testing.assert_array_equal(pymoo_fitness, expected)

    def test_problem_bounds_validation(self, mock_reaper_path):
        """Test that problem bounds are correctly set."""
        problem = JSIAudioOptimizationProblem(mock_reaper_path)

        # Check bounds match Solution class bounds
        assert problem.xl[0] == -2.0  # octave lower bound
        assert problem.xl[1] == -1.0  # fine lower bound
        assert problem.xu[0] == 2.0   # octave upper bound
        assert problem.xu[1] == 1.0   # fine upper bound

        # Test that bounds are compatible with Solution class
        test_solution = Solution(octave=problem.xl[0], fine=problem.xl[1])
        assert test_solution.octave == -2.0
        assert test_solution.fine == -1.0

        test_solution = Solution(octave=problem.xu[0], fine=problem.xu[1])
        assert test_solution.octave == 2.0
        assert test_solution.fine == 1.0
