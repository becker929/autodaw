"""Tests for JSI integration with GA populations."""

import pytest
import numpy as np
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from ga_jsi_audio_oracle.jsi_ga_integration import GAPopulationRanker, JSIFitnessEvaluator
from ga_jsi_audio_oracle.audio_oracle import AudioComparisonOracle


class MockSolution:
    """Mock solution for testing."""

    def __init__(self, octave, fine):
        self.octave = octave
        self.fine = fine

    def __str__(self):
        return f"Solution(octave={self.octave}, fine={self.fine})"


class TestGAPopulationRanker:
    """Test suite for GAPopulationRanker."""

    def test_initialization(self):
        """Test ranker initialization."""
        oracle = Mock()
        ranker = GAPopulationRanker(oracle, show_live_ranking=False)

        assert ranker.oracle == oracle
        assert ranker.comparison_count == 0
        assert ranker.generation_count == 0
        assert not ranker.show_live_ranking

    def test_find_matching_audio_path_direct_match(self):
        """Test finding audio path with direct match."""
        oracle = Mock()
        ranker = GAPopulationRanker(oracle)

        audio_paths = {
            'sol_001': Path('audio1.wav'),
            'sol_002': Path('audio2.wav')
        }

        result = ranker._find_matching_audio_path('sol_001', audio_paths)
        assert result == Path('audio1.wav')

    def test_find_matching_audio_path_fuzzy_match(self):
        """Test finding audio path with fuzzy matching."""
        oracle = Mock()
        ranker = GAPopulationRanker(oracle)

        audio_paths = {
            'individual_001_gen_1': Path('audio1.wav'),
            'individual_002_gen_1': Path('audio2.wav')
        }

        result = ranker._find_matching_audio_path('sol_001', audio_paths)
        assert result == Path('audio1.wav')

    def test_find_matching_audio_path_no_match(self):
        """Test finding audio path with no match."""
        oracle = Mock()
        ranker = GAPopulationRanker(oracle)

        audio_paths = {
            'other_001': Path('audio1.wav'),
            'different_002': Path('audio2.wav')
        }

        result = ranker._find_matching_audio_path('sol_999', audio_paths)
        assert result is None

    def test_fallback_ranking(self):
        """Test fallback ranking when insufficient solutions."""
        oracle = Mock()
        ranker = GAPopulationRanker(oracle)

        solutions = [
            MockSolution(0.5, 0.2),
            MockSolution(-0.3, 0.8)
        ]

        ranked_solutions, fitness_values, ranking_info = ranker._fallback_ranking(solutions)

        assert len(ranked_solutions) == 2
        assert len(fitness_values) == 2
        assert fitness_values[0] > fitness_values[1]  # Decreasing fitness
        assert ranking_info['comparisons_made'] == 0
        assert ranking_info['confidence'] == 0.0

    def test_rank_population_insufficient_solutions(self):
        """Test ranking with insufficient valid solutions."""
        oracle = Mock()
        ranker = GAPopulationRanker(oracle)

        solutions = [MockSolution(0.5, 0.2)]
        audio_paths = {}  # No valid audio paths

        ranked_solutions, fitness_values, ranking_info = ranker.rank_population_with_audio(
            solutions, audio_paths, generation=1
        )

        assert len(ranked_solutions) == 1
        assert len(fitness_values) == 1
        assert ranking_info['valid_solutions'] == 0
        assert ranking_info['total_solutions'] == 1

    @patch('ga_jsi_audio_oracle.jsi_ga_integration.SimpleRankingTracker')
    def test_rank_population_with_valid_solutions(self, mock_tracker_class):
        """Test ranking with valid solutions and audio paths."""
        # Mock oracle to always prefer first item
        oracle = Mock()
        oracle.compare.return_value = True

        # Mock tracker
        mock_tracker = Mock()
        mock_tracker.get_bt_ranking_with_confidence.return_value = (
            ['sol_000', 'sol_001'], 0.8, {'sol_000': 1.5, 'sol_001': 0.5}
        )
        mock_tracker_class.return_value = mock_tracker

        ranker = GAPopulationRanker(oracle, show_live_ranking=False)

        solutions = [
            MockSolution(0.5, 0.2),
            MockSolution(-0.3, 0.8)
        ]

        audio_paths = {
            'sol_000': Path('audio1.wav'),
            'sol_001': Path('audio2.wav')
        }

        # Mock path existence
        with patch.object(Path, 'exists', return_value=True):
            ranked_solutions, fitness_values, ranking_info = ranker.rank_population_with_audio(
                solutions, audio_paths, generation=1
            )

        assert len(ranked_solutions) == 2
        assert len(fitness_values) == 2
        assert ranking_info['valid_solutions'] == 2
        assert ranking_info['confidence'] == 0.8
        assert ranker.comparison_count > 0

    @patch('ga_jsi_audio_oracle.jsi_ga_integration.SimpleRankingTracker')
    def test_adaptive_quicksort_audio(self, mock_tracker_class):
        """Test adaptive quicksort with audio comparisons."""
        # Mock oracle behavior
        oracle = Mock()
        oracle.compare.side_effect = [False, True]  # First comparison: pivot wins, second: item wins

        mock_tracker = Mock()
        mock_tracker_class.return_value = mock_tracker

        ranker = GAPopulationRanker(oracle, show_live_ranking=False)

        solution_ids = ['sol_000', 'sol_001', 'sol_002']
        audio_paths = {
            'sol_000': Path('audio0.wav'),
            'sol_001': Path('audio1.wav'),
            'sol_002': Path('audio2.wav')
        }

        result = ranker._adaptive_quicksort_audio(solution_ids, audio_paths, mock_tracker)

        assert len(result) == 3
        assert all(sol_id in result for sol_id in solution_ids)
        assert ranker.comparison_count == 2  # Two comparisons made


class TestJSIFitnessEvaluator:
    """Test suite for JSIFitnessEvaluator."""

    def test_initialization(self):
        """Test evaluator initialization."""
        oracle = Mock()
        evaluator = JSIFitnessEvaluator(oracle, fitness_normalization="exponential")

        assert evaluator.fitness_normalization == "exponential"
        assert evaluator.ranker.oracle == oracle

    @patch('ga_jsi_audio_oracle.jsi_ga_integration.GAPopulationRanker')
    def test_evaluate_population_fitness_exponential(self, mock_ranker_class):
        """Test population fitness evaluation with exponential normalization."""
        oracle = Mock()

        # Mock ranker
        mock_ranker = Mock()
        mock_ranker.rank_population_with_audio.return_value = (
            [MockSolution(0.5, 0.2), MockSolution(-0.3, 0.8)],
            [1.0, 0.6],  # Pre-computed exponential fitness
            {'comparisons_made': 5}
        )
        mock_ranker_class.return_value = mock_ranker

        evaluator = JSIFitnessEvaluator(oracle, fitness_normalization="exponential")
        evaluator.ranker = mock_ranker

        solutions = [MockSolution(0.5, 0.2), MockSolution(-0.3, 0.8)]
        audio_paths = {'sol_000': Path('audio1.wav'), 'sol_001': Path('audio2.wav')}

        fitness_values = evaluator.evaluate_population_fitness(solutions, audio_paths, generation=1)

        assert len(fitness_values) == 2
        assert fitness_values == [1.0, 0.6]  # Should use pre-computed values

    @patch('ga_jsi_audio_oracle.jsi_ga_integration.GAPopulationRanker')
    def test_evaluate_population_fitness_linear(self, mock_ranker_class):
        """Test population fitness evaluation with linear normalization."""
        oracle = Mock()

        # Mock ranker
        mock_ranker = Mock()
        mock_ranker.rank_population_with_audio.return_value = (
            [MockSolution(0.5, 0.2), MockSolution(-0.3, 0.8)],
            [1.0, 0.6],  # Original fitness (will be overwritten)
            {'comparisons_made': 5}
        )
        mock_ranker_class.return_value = mock_ranker

        evaluator = JSIFitnessEvaluator(oracle, fitness_normalization="linear")
        evaluator.ranker = mock_ranker

        solutions = [MockSolution(0.5, 0.2), MockSolution(-0.3, 0.8)]
        audio_paths = {'sol_000': Path('audio1.wav'), 'sol_001': Path('audio2.wav')}

        fitness_values = evaluator.evaluate_population_fitness(solutions, audio_paths, generation=1)

        assert len(fitness_values) == 2
        assert fitness_values[0] == 1.0  # First rank gets max fitness
        assert fitness_values[1] == 0.1  # Second rank gets min fitness

    @patch('ga_jsi_audio_oracle.jsi_ga_integration.GAPopulationRanker')
    def test_evaluate_population_fitness_inverse(self, mock_ranker_class):
        """Test population fitness evaluation with inverse normalization."""
        oracle = Mock()

        # Mock ranker
        mock_ranker = Mock()
        mock_ranker.rank_population_with_audio.return_value = (
            [MockSolution(0.5, 0.2), MockSolution(-0.3, 0.8), MockSolution(0.1, -0.5)],
            [1.0, 0.6, 0.3],  # Original fitness (will be overwritten)
            {'comparisons_made': 8}
        )
        mock_ranker_class.return_value = mock_ranker

        evaluator = JSIFitnessEvaluator(oracle, fitness_normalization="inverse")
        evaluator.ranker = mock_ranker

        solutions = [MockSolution(0.5, 0.2), MockSolution(-0.3, 0.8), MockSolution(0.1, -0.5)]
        audio_paths = {
            'sol_000': Path('audio1.wav'),
            'sol_001': Path('audio2.wav'),
            'sol_002': Path('audio3.wav')
        }

        fitness_values = evaluator.evaluate_population_fitness(solutions, audio_paths, generation=1)

        assert len(fitness_values) == 3
        assert fitness_values[0] == 1.0  # 1/(0+1)
        assert fitness_values[1] == 0.5  # 1/(1+1)
        assert fitness_values[2] == 1.0/3  # 1/(2+1)

    def test_get_ranking_info(self):
        """Test getting ranking information."""
        oracle = Mock()
        evaluator = JSIFitnessEvaluator(oracle)

        # Set some values on the ranker
        evaluator.ranker.comparison_count = 15
        evaluator.ranker.generation_count = 3

        info = evaluator.get_ranking_info()

        assert info['comparison_count'] == 15
        assert info['generation_count'] == 3
