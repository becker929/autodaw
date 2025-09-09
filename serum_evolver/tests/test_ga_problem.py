"""Unit tests for GA problem classes."""

import pytest
import numpy as np
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from serum_evolver.src.genetics.jsi_problems import JSIAudioOptimizationProblem, MultiTargetJSIOptimizationProblem
from serum_evolver.src.genetics.genetics import Solution


class TestJSIAudioOptimizationProblem:
    """Test cases for JSIAudioOptimizationProblem."""

    @patch('serum_evolver.src.genetics.jsi_problems.ReaperExecutor')
    @patch('serum_evolver.src.genetics.jsi_problems.AudioComparisonOracle')
    @patch('serum_evolver.src.genetics.jsi_problems.JSIFitnessEvaluator')
    @patch('serum_evolver.src.genetics.jsi_problems.GenomeToPhenotypeMapper')
    def test_initialization_with_target_frequency(self, mock_mapper, mock_evaluator, mock_oracle, mock_reaper):
        """Test initialization with target frequency."""
        reaper_path = Path("/test/reaper")
        target_freq = 440.0

        problem = JSIAudioOptimizationProblem(
            reaper_project_path=reaper_path,
            target_frequency=target_freq
        )

        assert problem.reaper_project_path == reaper_path
        assert problem.session_name_prefix == "jsi_audio_ga"
        assert problem.generation_counter == 0
        assert problem.evaluation_count == 0

        # Check problem dimensions
        assert problem.n_var == 2
        assert problem.n_obj == 1
        np.testing.assert_array_equal(problem.xl, np.array([-2.0, -1.0]))
        np.testing.assert_array_equal(problem.xu, np.array([2.0, 1.0]))

    @patch('serum_evolver.src.genetics.jsi_problems.ReaperExecutor')
    @patch('serum_evolver.src.genetics.jsi_problems.FrequencyTargetOracle')
    @patch('serum_evolver.src.genetics.jsi_problems.JSIFitnessEvaluator')
    @patch('serum_evolver.src.genetics.jsi_problems.GenomeToPhenotypeMapper')
    def test_initialization_with_target_audio(self, mock_mapper, mock_evaluator, mock_oracle, mock_reaper):
        """Test initialization with target audio file."""
        reaper_path = Path("/test/reaper")
        target_audio = Mock()
        target_audio.exists.return_value = True

        problem = JSIAudioOptimizationProblem(
            reaper_project_path=reaper_path,
            target_audio_path=target_audio
        )

        mock_oracle.assert_called_once()
        assert problem.reaper_project_path == reaper_path

    @patch('serum_evolver.src.genetics.jsi_problems.ReaperExecutor')
    @patch('serum_evolver.src.genetics.jsi_problems.AudioComparisonOracle')
    @patch('serum_evolver.src.genetics.jsi_problems.JSIFitnessEvaluator')
    @patch('serum_evolver.src.genetics.jsi_problems.GenomeToPhenotypeMapper')
    def test_evaluate_population_success(self, mock_mapper, mock_evaluator, mock_oracle, mock_reaper):
        """Test successful population evaluation."""
        problem = JSIAudioOptimizationProblem(Path("/test/reaper"))

        # Mock the render method
        mock_audio_paths = {"sol_000": Path("audio1.wav"), "sol_001": Path("audio2.wav")}
        problem._render_population_audio = Mock(return_value=mock_audio_paths)

        # Mock JSI evaluator
        mock_evaluator_instance = Mock()
        mock_evaluator_instance.evaluate_population_fitness.return_value = [0.8, 0.6]
        problem.jsi_evaluator = mock_evaluator_instance

        # Test population
        x = np.array([[0.5, 0.2], [1.0, -0.3]])
        out = {}

        problem._evaluate(x, out)

        # Check that fitness values were computed and negated for minimization
        assert "F" in out
        assert len(out["F"]) == 2
        np.testing.assert_array_equal(out["F"], np.array([[-0.8], [-0.6]]))

        # Check counters updated
        assert problem.generation_counter == 1
        assert problem.evaluation_count == 2

    @patch('serum_evolver.src.genetics.jsi_problems.ReaperExecutor')
    @patch('serum_evolver.src.genetics.jsi_problems.AudioComparisonOracle')
    @patch('serum_evolver.src.genetics.jsi_problems.JSIFitnessEvaluator')
    @patch('serum_evolver.src.genetics.jsi_problems.GenomeToPhenotypeMapper')
    def test_evaluate_population_failure(self, mock_mapper, mock_evaluator, mock_oracle, mock_reaper):
        """Test population evaluation with exception."""
        problem = JSIAudioOptimizationProblem(Path("/test/reaper"))

        # Mock render method to raise exception
        problem._render_population_audio = Mock(side_effect=Exception("Render failed"))

        x = np.array([[0.5, 0.2], [1.0, -0.3]])
        out = {}

        problem._evaluate(x, out)

        # Should return penalty values
        assert "F" in out
        np.testing.assert_array_equal(out["F"], np.array([[-1000.0], [-1000.0]]))

    @patch('serum_evolver.src.genetics.jsi_problems.ReaperExecutor')
    @patch('serum_evolver.src.genetics.jsi_problems.AudioComparisonOracle')
    @patch('serum_evolver.src.genetics.jsi_problems.JSIFitnessEvaluator')
    @patch('serum_evolver.src.genetics.jsi_problems.GenomeToPhenotypeMapper')
    def test_render_population_audio(self, mock_mapper, mock_evaluator, mock_oracle, mock_reaper):
        """Test rendering population audio."""
        problem = JSIAudioOptimizationProblem(Path("/test/reaper"))

        # Mock genome mapper
        mock_mapper_instance = Mock()
        mock_configs = [Mock(), Mock()]
        mock_mapper_instance.population_to_render_configs.return_value = mock_configs
        problem.genome_mapper = mock_mapper_instance

        # Mock REAPER executor
        mock_reaper_instance = Mock()
        mock_render_paths = {
            "session_individual_000": Path("render1.wav"),
            "session_individual_001": Path("render2.wav")
        }
        mock_reaper_instance.execute_session.return_value = mock_render_paths
        problem.reaper_executor = mock_reaper_instance

        solutions = [Solution(0.5, 0.2), Solution(1.0, -0.3)]
        session_name = "test_session"

        result = problem._render_population_audio(solutions, session_name)

        assert len(result) == 2
        assert "sol_000" in result
        assert "sol_001" in result

    @patch('serum_evolver.src.genetics.jsi_problems.ReaperExecutor')
    @patch('serum_evolver.src.genetics.jsi_problems.AudioComparisonOracle')
    @patch('serum_evolver.src.genetics.jsi_problems.JSIFitnessEvaluator')
    @patch('serum_evolver.src.genetics.jsi_problems.GenomeToPhenotypeMapper')
    def test_log_generation_stats(self, mock_mapper, mock_evaluator, mock_oracle, mock_reaper):
        """Test logging generation statistics."""
        problem = JSIAudioOptimizationProblem(Path("/test/reaper"))

        # Mock JSI evaluator
        mock_evaluator_instance = Mock()
        mock_evaluator_instance.get_ranking_info.return_value = {"comparison_count": 10}
        problem.jsi_evaluator = mock_evaluator_instance

        solutions = [Solution(0.5, 0.2), Solution(1.0, -0.3)]
        fitness_values = [0.8, 0.6]

        # Should not raise exception
        problem._log_generation_stats(solutions, fitness_values)

    @patch('serum_evolver.src.genetics.jsi_problems.ReaperExecutor')
    @patch('serum_evolver.src.genetics.jsi_problems.AudioComparisonOracle')
    @patch('serum_evolver.src.genetics.jsi_problems.JSIFitnessEvaluator')
    @patch('serum_evolver.src.genetics.jsi_problems.GenomeToPhenotypeMapper')
    def test_cleanup_old_renders(self, mock_mapper, mock_evaluator, mock_oracle, mock_reaper):
        """Test cleanup of old render directories."""
        problem = JSIAudioOptimizationProblem(Path("/test/reaper"))
        problem.generation_counter = 5

        # Mock REAPER executor renders directory
        mock_renders_dir = Mock()
        mock_old_dir = Mock()
        mock_old_dir.is_dir.return_value = True
        mock_old_dir.name = "jsi_audio_ga_gen_003"
        mock_renders_dir.iterdir.return_value = [mock_old_dir]

        mock_reaper_instance = Mock()
        mock_reaper_instance.renders_dir = mock_renders_dir
        problem.reaper_executor = mock_reaper_instance

        with patch('shutil.rmtree') as mock_rmtree:
            problem._cleanup_old_renders(keep_generations=2)
            mock_rmtree.assert_called_once_with(mock_old_dir)

    @patch('serum_evolver.src.genetics.jsi_problems.ReaperExecutor')
    @patch('serum_evolver.src.genetics.jsi_problems.AudioComparisonOracle')
    @patch('serum_evolver.src.genetics.jsi_problems.JSIFitnessEvaluator')
    @patch('serum_evolver.src.genetics.jsi_problems.GenomeToPhenotypeMapper')
    def test_get_best_solution_info(self, mock_mapper, mock_evaluator, mock_oracle, mock_reaper):
        """Test extracting best solution information."""
        problem = JSIAudioOptimizationProblem(Path("/test/reaper"))
        problem.evaluation_count = 100
        problem.generation_counter = 5

        # Mock JSI evaluator
        mock_evaluator_instance = Mock()
        mock_evaluator_instance.get_ranking_info.return_value = {"comparison_count": 50}
        problem.jsi_evaluator = mock_evaluator_instance

        # Mock optimization result
        mock_result = Mock()
        mock_result.X = np.array([0.5, 0.2])
        mock_result.F = np.array([-0.8])  # Negated fitness

        result = problem.get_best_solution_info(mock_result)

        assert result["fitness"] == 0.8  # Should be un-negated
        assert result["evaluations"] == 100
        assert result["generations"] == 5
        assert result["jsi_comparisons"] == 50

    @patch('serum_evolver.src.genetics.jsi_problems.ReaperExecutor')
    @patch('serum_evolver.src.genetics.jsi_problems.AudioComparisonOracle')
    @patch('serum_evolver.src.genetics.jsi_problems.JSIFitnessEvaluator')
    @patch('serum_evolver.src.genetics.jsi_problems.GenomeToPhenotypeMapper')
    def test_set_target_frequency(self, mock_mapper, mock_evaluator, mock_oracle, mock_reaper):
        """Test updating target frequency."""
        problem = JSIAudioOptimizationProblem(Path("/test/reaper"))

        mock_oracle_instance = Mock()
        mock_oracle_instance.set_target_frequency = Mock()
        problem.oracle = mock_oracle_instance

        problem.set_target_frequency(880.0)

        mock_oracle_instance.set_target_frequency.assert_called_once_with(880.0)

    @patch('serum_evolver.src.genetics.jsi_problems.ReaperExecutor')
    @patch('serum_evolver.src.genetics.jsi_problems.AudioComparisonOracle')
    @patch('serum_evolver.src.genetics.jsi_problems.JSIFitnessEvaluator')
    @patch('serum_evolver.src.genetics.jsi_problems.GenomeToPhenotypeMapper')
    def test_clear_oracle_cache(self, mock_mapper, mock_evaluator, mock_oracle, mock_reaper):
        """Test clearing oracle cache."""
        problem = JSIAudioOptimizationProblem(Path("/test/reaper"))

        mock_oracle_instance = Mock()
        mock_oracle_instance.clear_cache = Mock()
        problem.oracle = mock_oracle_instance

        problem.clear_oracle_cache()

        mock_oracle_instance.clear_cache.assert_called_once()


class TestMultiTargetJSIOptimizationProblem:
    """Test cases for MultiTargetJSIOptimizationProblem."""

    @patch('serum_evolver.src.genetics.jsi_problems.ReaperExecutor')
    @patch('serum_evolver.src.genetics.jsi_problems.AudioComparisonOracle')
    @patch('serum_evolver.src.genetics.jsi_problems.JSIFitnessEvaluator')
    @patch('serum_evolver.src.genetics.jsi_problems.GenomeToPhenotypeMapper')
    def test_initialization(self, mock_mapper, mock_evaluator, mock_oracle, mock_reaper):
        """Test multi-target problem initialization."""
        reaper_path = Path("/test/reaper")
        target_frequencies = [440.0, 880.0, 1320.0]

        problem = MultiTargetJSIOptimizationProblem(
            reaper_project_path=reaper_path,
            target_frequencies=target_frequencies
        )

        assert problem.target_frequencies == target_frequencies
        assert problem.current_target_index == 0

    @patch('serum_evolver.src.genetics.jsi_problems.ReaperExecutor')
    @patch('serum_evolver.src.genetics.jsi_problems.AudioComparisonOracle')
    @patch('serum_evolver.src.genetics.jsi_problems.JSIFitnessEvaluator')
    @patch('serum_evolver.src.genetics.jsi_problems.GenomeToPhenotypeMapper')
    def test_target_frequency_rotation(self, mock_mapper, mock_evaluator, mock_oracle, mock_reaper):
        """Test rotation of target frequencies."""
        reaper_path = Path("/test/reaper")
        target_frequencies = [440.0, 880.0, 1320.0]

        problem = MultiTargetJSIOptimizationProblem(
            reaper_project_path=reaper_path,
            target_frequencies=target_frequencies
        )

        # Mock parent evaluate method
        problem.set_target_frequency = Mock()

        # Mock the render method to avoid actual evaluation
        problem._render_population_audio = Mock(return_value={})
        mock_evaluator_instance = Mock()
        mock_evaluator_instance.evaluate_population_fitness.return_value = []
        problem.jsi_evaluator = mock_evaluator_instance

        # Set generation counter to trigger frequency rotation
        # Rotation happens when generation_counter > 0 and generation_counter % 5 == 0
        problem.generation_counter = 5  # This will trigger rotation

        x = np.array([[0.5, 0.2]])
        out = {}

        problem._evaluate(x, out)

        # Should have rotated to next target frequency
        problem.set_target_frequency.assert_called_once_with(880.0)
        assert problem.current_target_index == 1


if __name__ == "__main__":
    pytest.main([__file__])
