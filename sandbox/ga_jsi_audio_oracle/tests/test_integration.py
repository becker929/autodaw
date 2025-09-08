"""Integration tests for the complete GA + JSI + Audio Oracle system."""

import pytest
import numpy as np
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from ga_jsi_audio_oracle.ga_problem import JSIAudioOptimizationProblem
from ga_jsi_audio_oracle.main import demo_jsi_audio_optimization


class TestJSIAudioOptimizationProblem:
    """Test suite for JSIAudioOptimizationProblem."""

    @patch('ga_jsi_audio_oracle.ga_problem.ReaperExecutor')
    @patch('ga_jsi_audio_oracle.ga_problem.AudioComparisonOracle')
    @patch('ga_jsi_audio_oracle.ga_problem.JSIFitnessEvaluator')
    def test_initialization(self, mock_evaluator, mock_oracle, mock_executor):
        """Test problem initialization."""
        reaper_path = Path('/fake/reaper/path')

        problem = JSIAudioOptimizationProblem(
            reaper_project_path=reaper_path,
            target_frequency=440.0,
            session_name_prefix="test_session"
        )

        assert problem.reaper_project_path == reaper_path
        assert problem.session_name_prefix == "test_session"
        assert problem.generation_counter == 0
        assert problem.evaluation_count == 0

        # Check pymoo problem setup
        assert problem.n_var == 2
        assert problem.n_obj == 1
        assert np.array_equal(problem.xl, np.array([-2.0, -1.0]))
        assert np.array_equal(problem.xu, np.array([2.0, 1.0]))

    @patch('ga_jsi_audio_oracle.ga_problem.FrequencyTargetOracle')
    @patch('ga_jsi_audio_oracle.ga_problem.ReaperExecutor')
    @patch('ga_jsi_audio_oracle.ga_problem.JSIFitnessEvaluator')
    def test_initialization_with_target_audio(self, mock_evaluator, mock_executor, mock_target_oracle):
        """Test initialization with target audio file."""
        reaper_path = Path('/fake/reaper/path')
        target_audio = Path('/fake/target.wav')

        with patch.object(target_audio, 'exists', return_value=True):
            problem = JSIAudioOptimizationProblem(
                reaper_project_path=reaper_path,
                target_audio_path=target_audio
            )

        # Should use FrequencyTargetOracle instead of AudioComparisonOracle
        mock_target_oracle.assert_called_once()

    @patch('ga_jsi_audio_oracle.ga_problem.ReaperExecutor')
    @patch('ga_jsi_audio_oracle.ga_problem.AudioComparisonOracle')
    @patch('ga_jsi_audio_oracle.ga_problem.JSIFitnessEvaluator')
    @patch('ga_jsi_audio_oracle.ga_problem.GenomeToPhenotypeMapper')
    def test_render_population_audio(self, mock_mapper_class, mock_evaluator, mock_oracle, mock_executor_class):
        """Test audio rendering for population."""
        reaper_path = Path('/fake/reaper/path')
        problem = JSIAudioOptimizationProblem(reaper_project_path=reaper_path)

        # Mock the executor
        mock_executor = Mock()
        mock_executor.execute_session.return_value = {
            'individual_000_render': Path('audio0.wav'),
            'individual_001_render': Path('audio1.wav')
        }
        problem.reaper_executor = mock_executor

        # Mock the mapper
        mock_mapper = Mock()
        mock_mapper.population_to_render_configs.return_value = ['config1', 'config2']
        problem.genome_mapper = mock_mapper

        # Create mock solutions
        from unittest.mock import Mock as MockSolution
        solutions = [MockSolution(), MockSolution()]

        result = problem._render_population_audio(solutions, "test_session")

        assert len(result) == 2
        assert 'sol_000' in result
        assert 'sol_001' in result
        mock_executor.execute_session.assert_called_once()

    @patch('ga_jsi_audio_oracle.ga_problem.ReaperExecutor')
    @patch('ga_jsi_audio_oracle.ga_problem.AudioComparisonOracle')
    @patch('ga_jsi_audio_oracle.ga_problem.JSIFitnessEvaluator')
    def test_evaluate_population_success(self, mock_evaluator_class, mock_oracle, mock_executor):
        """Test successful population evaluation."""
        reaper_path = Path('/fake/reaper/path')
        problem = JSIAudioOptimizationProblem(reaper_project_path=reaper_path)

        # Mock the JSI evaluator
        mock_evaluator = Mock()
        mock_evaluator.evaluate_population_fitness.return_value = [0.8, 0.6]
        mock_evaluator.get_ranking_info.return_value = {'comparison_count': 5}
        problem.jsi_evaluator = mock_evaluator

        # Mock render population
        problem._render_population_audio = Mock(return_value={
            'sol_000': Path('audio0.wav'),
            'sol_001': Path('audio1.wav')
        })

        # Mock cleanup
        problem._cleanup_old_renders = Mock()

        # Test population
        x = np.array([[0.5, 0.2], [-0.3, 0.8]])
        out = {}

        problem._evaluate(x, out)

        assert 'F' in out
        assert out['F'].shape == (2, 1)
        # Fitness should be negated for minimization
        assert np.allclose(out['F'], np.array([[-0.8], [-0.6]]))
        assert problem.generation_counter == 1
        assert problem.evaluation_count == 2

    @patch('ga_jsi_audio_oracle.ga_problem.ReaperExecutor')
    @patch('ga_jsi_audio_oracle.ga_problem.AudioComparisonOracle')
    @patch('ga_jsi_audio_oracle.ga_problem.JSIFitnessEvaluator')
    def test_evaluate_population_exception(self, mock_evaluator_class, mock_oracle, mock_executor):
        """Test population evaluation with exception."""
        reaper_path = Path('/fake/reaper/path')
        problem = JSIAudioOptimizationProblem(reaper_project_path=reaper_path)

        # Mock render to raise exception
        problem._render_population_audio = Mock(side_effect=Exception("Render failed"))

        x = np.array([[0.5, 0.2], [-0.3, 0.8]])
        out = {}

        problem._evaluate(x, out)

        assert 'F' in out
        assert out['F'].shape == (2, 1)
        # Should return penalty values
        assert np.allclose(out['F'], np.array([[-1000.0], [-1000.0]]))

    def test_get_best_solution_info(self):
        """Test extracting best solution information."""
        reaper_path = Path('/fake/reaper/path')

        with patch('ga_jsi_audio_oracle.ga_problem.ReaperExecutor'), \
             patch('ga_jsi_audio_oracle.ga_problem.AudioComparisonOracle'), \
             patch('ga_jsi_audio_oracle.ga_problem.JSIFitnessEvaluator'):

            problem = JSIAudioOptimizationProblem(reaper_project_path=reaper_path)
            problem.evaluation_count = 50
            problem.generation_counter = 5

            # Mock JSI evaluator
            problem.jsi_evaluator = Mock()
            problem.jsi_evaluator.get_ranking_info.return_value = {'comparison_count': 25}

            # Mock result object
            mock_result = Mock()
            mock_result.X = np.array([0.5, 0.2])
            mock_result.F = np.array([-0.8])  # Negated fitness

            info = problem.get_best_solution_info(mock_result)

            assert 'solution' in info
            assert 'fitness' in info
            assert info['fitness'] == 0.8  # Should be converted back from negated
            assert info['evaluations'] == 50
            assert info['generations'] == 5
            assert info['jsi_comparisons'] == 25


class TestMainDemo:
    """Test suite for main demo functions."""

    @patch('ga_jsi_audio_oracle.main.JSIAudioOptimizationProblem')
    @patch('ga_jsi_audio_oracle.main.minimize')
    def test_demo_jsi_audio_optimization_success(self, mock_minimize, mock_problem_class):
        """Test successful demo execution."""
        reaper_path = Path('/fake/reaper/path')

        # Mock problem
        mock_problem = Mock()
        mock_problem.generation_counter = 5
        mock_problem.evaluation_count = 40
        mock_problem.get_best_solution_info.return_value = {
            'solution': 'MockSolution(octave=0.5, fine=0.2)',
            'fitness': 0.85,
            'frequency_ratio': 1.2,
            'evaluations': 40,
            'jsi_comparisons': 20
        }
        mock_problem.clear_oracle_cache = Mock()
        mock_problem_class.return_value = mock_problem

        # Mock optimization result
        mock_result = Mock()
        mock_minimize.return_value = mock_result

        with patch.object(reaper_path, 'exists', return_value=True):
            result = demo_jsi_audio_optimization(
                reaper_project_path=reaper_path,
                target_frequency=440.0,
                n_generations=5,
                population_size=4
            )

        assert result['success'] is True
        assert 'best_info' in result
        assert result['target_frequency'] == 440.0
        assert result['generations_completed'] == 5
        assert result['total_evaluations'] == 40
        mock_problem.clear_oracle_cache.assert_called_once()

    @patch('ga_jsi_audio_oracle.main.JSIAudioOptimizationProblem')
    def test_demo_jsi_audio_optimization_missing_reaper(self, mock_problem_class):
        """Test demo with missing REAPER project."""
        reaper_path = Path('/nonexistent/reaper/path')

        with patch.object(reaper_path, 'exists', return_value=False):
            with pytest.raises(FileNotFoundError):
                demo_jsi_audio_optimization(
                    reaper_project_path=reaper_path,
                    target_frequency=440.0
                )

    @patch('ga_jsi_audio_oracle.main.JSIAudioOptimizationProblem')
    @patch('ga_jsi_audio_oracle.main.minimize')
    def test_demo_jsi_audio_optimization_exception(self, mock_minimize, mock_problem_class):
        """Test demo with optimization exception."""
        reaper_path = Path('/fake/reaper/path')

        # Mock problem
        mock_problem = Mock()
        mock_problem.generation_counter = 2
        mock_problem.evaluation_count = 8
        mock_problem_class.return_value = mock_problem

        # Mock minimize to raise exception
        mock_minimize.side_effect = Exception("Optimization failed")

        with patch.object(reaper_path, 'exists', return_value=True):
            result = demo_jsi_audio_optimization(
                reaper_project_path=reaper_path,
                target_frequency=440.0
            )

        assert result['success'] is False
        assert 'error' in result
        assert result['generations_completed'] == 2
        assert result['total_evaluations'] == 8
