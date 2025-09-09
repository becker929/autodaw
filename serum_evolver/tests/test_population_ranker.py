"""Unit tests for population ranker components."""

import pytest
import numpy as np
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from serum_evolver.src.ranking.population_ranker import GAPopulationRanker, JSIFitnessEvaluator


class MockSolution:
    """Mock solution for testing."""
    def __init__(self, octave=0.0, fine=0.0):
        self.octave = octave
        self.fine = fine

    def __str__(self):
        return f"Solution(octave={self.octave}, fine={self.fine})"

    def calculate_frequency_ratio(self):
        return 1.0 + self.octave + self.fine


class TestGAPopulationRanker:
    """Test cases for GAPopulationRanker."""

    def test_initialization(self):
        """Test ranker initialization."""
        mock_oracle = Mock()
        ranker = GAPopulationRanker(oracle=mock_oracle, show_live_ranking=False)

        assert ranker.oracle == mock_oracle
        assert ranker.show_live_ranking == False
        assert ranker.comparison_count == 0
        assert ranker.generation_count == 0

    def test_find_matching_audio_path_direct_match(self):
        """Test finding audio path with direct match."""
        mock_oracle = Mock()
        ranker = GAPopulationRanker(oracle=mock_oracle)

        audio_paths = {
            "sol_001": Path("audio1.wav"),
            "sol_002": Path("audio2.wav")
        }

        result = ranker._find_matching_audio_path("sol_001", audio_paths)
        assert result == Path("audio1.wav")

    def test_find_matching_audio_path_fuzzy_match(self):
        """Test finding audio path with fuzzy matching."""
        mock_oracle = Mock()
        ranker = GAPopulationRanker(oracle=mock_oracle)

        audio_paths = {
            "individual_001": Path("audio1.wav"),
            "individual_002": Path("audio2.wav")
        }

        result = ranker._find_matching_audio_path("sol_001", audio_paths)
        assert result == Path("audio1.wav")

    def test_find_matching_audio_path_no_match(self):
        """Test finding audio path with no match."""
        mock_oracle = Mock()
        ranker = GAPopulationRanker(oracle=mock_oracle)

        audio_paths = {
            "other_001": Path("audio1.wav"),
            "other_002": Path("audio2.wav")
        }

        result = ranker._find_matching_audio_path("sol_999", audio_paths)
        assert result is None

    def test_fallback_ranking(self):
        """Test fallback ranking when insufficient valid solutions."""
        mock_oracle = Mock()
        ranker = GAPopulationRanker(oracle=mock_oracle)

        solutions = [MockSolution(0.1, 0.2), MockSolution(0.3, 0.4)]

        ranked_solutions, fitness_values, ranking_info = ranker._fallback_ranking(solutions)

        assert len(ranked_solutions) == 2
        assert len(fitness_values) == 2
        assert fitness_values[0] > fitness_values[1]  # Decreasing fitness
        assert ranking_info['confidence'] == 0.0
        assert ranking_info['valid_solutions'] == 0

    @patch('serum_evolver.src.ranking.population_ranker.SimpleRankingTracker')
    def test_rank_population_insufficient_solutions(self, mock_tracker_class):
        """Test ranking with insufficient valid solutions."""
        mock_oracle = Mock()
        ranker = GAPopulationRanker(oracle=mock_oracle)

        solutions = [MockSolution()]
        audio_paths = {}  # No valid audio paths

        result = ranker.rank_population_with_audio(solutions, audio_paths, generation=1)

        ranked_solutions, fitness_values, ranking_info = result
        assert len(ranked_solutions) == 1
        assert ranking_info['valid_solutions'] == 0

    @patch('serum_evolver.src.ranking.population_ranker.SimpleRankingTracker')
    def test_adaptive_quicksort_single_item(self, mock_tracker_class):
        """Test quicksort with single item."""
        mock_oracle = Mock()
        mock_tracker = Mock()
        ranker = GAPopulationRanker(oracle=mock_oracle)

        solution_ids = ["sol_001"]
        audio_paths = {"sol_001": Path("audio1.wav")}

        result = ranker._adaptive_quicksort_audio(solution_ids, audio_paths, mock_tracker)

        assert result == ["sol_001"]
        assert ranker.comparison_count == 0  # No comparisons needed

    @patch('serum_evolver.src.ranking.population_ranker.SimpleRankingTracker')
    def test_adaptive_quicksort_multiple_items(self, mock_tracker_class):
        """Test quicksort with multiple items."""
        mock_oracle = Mock()
        mock_oracle.compare.side_effect = [True, False]  # First comparison: item1 > pivot, second: pivot > item2
        mock_tracker = Mock()
        ranker = GAPopulationRanker(oracle=mock_oracle, show_live_ranking=False)

        solution_ids = ["sol_001", "sol_002", "sol_003"]
        audio_paths = {
            "sol_001": Path("audio1.wav"),
            "sol_002": Path("audio2.wav"),
            "sol_003": Path("audio3.wav")
        }

        result = ranker._adaptive_quicksort_audio(solution_ids, audio_paths, mock_tracker)

        assert len(result) == 3
        assert ranker.comparison_count == 2
        mock_tracker.add_comparison.assert_called()


class TestJSIFitnessEvaluator:
    """Test cases for JSIFitnessEvaluator."""

    def test_initialization(self):
        """Test evaluator initialization."""
        mock_oracle = Mock()
        evaluator = JSIFitnessEvaluator(oracle=mock_oracle)

        assert evaluator.ranker.oracle == mock_oracle
        assert evaluator.fitness_normalization == "exponential"

    def test_initialization_with_custom_normalization(self):
        """Test evaluator initialization with custom normalization."""
        mock_oracle = Mock()
        evaluator = JSIFitnessEvaluator(
            oracle=mock_oracle,
            fitness_normalization="linear"
        )

        assert evaluator.fitness_normalization == "linear"

    @patch.object(GAPopulationRanker, 'rank_population_with_audio')
    def test_evaluate_population_fitness_exponential(self, mock_rank):
        """Test population fitness evaluation with exponential normalization."""
        mock_oracle = Mock()
        evaluator = JSIFitnessEvaluator(oracle=mock_oracle, fitness_normalization="exponential")

        # Mock the ranking result
        solutions = [MockSolution(), MockSolution()]
        mock_rank.return_value = (solutions, [0.8, 0.4], {})

        audio_paths = {"sol_001": Path("audio1.wav"), "sol_002": Path("audio2.wav")}

        result = evaluator.evaluate_population_fitness(solutions, audio_paths, generation=1)

        assert len(result) == 2
        assert result[0] == 0.8  # Should use the values from ranker directly
        assert result[1] == 0.4

    @patch.object(GAPopulationRanker, 'rank_population_with_audio')
    def test_evaluate_population_fitness_linear(self, mock_rank):
        """Test population fitness evaluation with linear normalization."""
        mock_oracle = Mock()
        evaluator = JSIFitnessEvaluator(oracle=mock_oracle, fitness_normalization="linear")

        solutions = [MockSolution(), MockSolution(), MockSolution()]
        mock_rank.return_value = (solutions, [0.9, 0.6, 0.3], {})

        audio_paths = {}

        result = evaluator.evaluate_population_fitness(solutions, audio_paths)

        assert len(result) == 3
        assert result[0] == 1.0  # First item gets highest fitness
        assert result[1] == 0.55  # Middle item
        assert abs(result[2] - 0.1) < 0.001   # Last item gets lowest fitness (allow for floating point precision)

    @patch.object(GAPopulationRanker, 'rank_population_with_audio')
    def test_evaluate_population_fitness_inverse(self, mock_rank):
        """Test population fitness evaluation with inverse normalization."""
        mock_oracle = Mock()
        evaluator = JSIFitnessEvaluator(oracle=mock_oracle, fitness_normalization="inverse")

        solutions = [MockSolution(), MockSolution()]
        mock_rank.return_value = (solutions, [0.9, 0.3], {})

        audio_paths = {}

        result = evaluator.evaluate_population_fitness(solutions, audio_paths)

        assert len(result) == 2
        assert result[0] == 1.0    # 1/(0+1)
        assert result[1] == 0.5    # 1/(1+1)

    def test_get_ranking_info(self):
        """Test ranking info retrieval."""
        mock_oracle = Mock()
        evaluator = JSIFitnessEvaluator(oracle=mock_oracle)
        evaluator.ranker.comparison_count = 10
        evaluator.ranker.generation_count = 3

        info = evaluator.get_ranking_info()

        assert info['comparison_count'] == 10
        assert info['generation_count'] == 3


if __name__ == "__main__":
    pytest.main([__file__])
