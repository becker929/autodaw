"""Unit tests for refactored population ranker components."""

import pytest
import numpy as np
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from serum_evolver.src.ranking.population_ranker import (
    GAPopulationRanker, JSIFitnessEvaluator, create_standard_population_ranker
)
from serum_evolver.src.ranking.audio_path_matcher import AudioPathMatcher
from serum_evolver.src.ranking.ranking_display import SilentRankingDisplayer
from serum_evolver.src.ranking.jsi_sorter import JSIAdaptiveQuicksort
from serum_evolver.src.ranking.fitness_calculator import FitnessCalculator


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
    """Test cases for refactored GAPopulationRanker."""

    def test_initialization(self):
        """Test ranker initialization with dependency injection."""
        mock_oracle = Mock()
        path_matcher = AudioPathMatcher()
        displayer = SilentRankingDisplayer()
        sorter = JSIAdaptiveQuicksort(mock_oracle, displayer)
        fitness_calc = FitnessCalculator()

        ranker = GAPopulationRanker(
            oracle=mock_oracle,
            path_matcher=path_matcher,
            displayer=displayer,
            sorter=sorter,
            fitness_calculator=fitness_calc
        )

        assert ranker.oracle is mock_oracle
        assert ranker.path_matcher is path_matcher
        assert ranker.displayer is displayer
        assert ranker.sorter is sorter
        assert ranker.fitness_calculator is fitness_calc

    def test_find_matching_audio_path_direct_match(self):
        """Test finding matching audio path with direct match."""
        audio_paths = {
            'sol_001': Path('/audio/sol_001.wav'),
            'sol_002': Path('/audio/sol_002.wav')
        }

        result = AudioPathMatcher.find_matching_audio_path('sol_001', audio_paths)
        assert result == Path('/audio/sol_001.wav')

    def test_find_matching_audio_path_fuzzy_match(self):
        """Test finding matching audio path with fuzzy matching."""
        audio_paths = {
            'individual_001': Path('/audio/individual_001.wav'),
            'individual_002': Path('/audio/individual_002.wav')
        }

        result = AudioPathMatcher.find_matching_audio_path('sol_001', audio_paths)
        assert result == Path('/audio/individual_001.wav')

    def test_find_matching_audio_path_no_match(self):
        """Test finding matching audio path with no match."""
        audio_paths = {
            'completely_different': Path('/audio/completely_different.wav'),
            'also_different': Path('/audio/also_different.wav')
        }

        result = AudioPathMatcher.find_matching_audio_path('sol_999', audio_paths)
        assert result is None

    def test_fallback_ranking(self):
        """Test fallback ranking when insufficient solutions."""
        mock_oracle = Mock()
        ranker = create_standard_population_ranker(mock_oracle, show_live_ranking=False)

        solutions = [MockSolution(0.0, 0.0), MockSolution(0.5, 0.5)]
        audio_paths = {}  # No audio paths

        ranked_solutions, fitness_values, ranking_info = ranker.rank_population_with_audio(
            solutions, audio_paths
        )

        assert len(ranked_solutions) == 2
        assert len(fitness_values) == 2
        assert ranking_info.get('fallback_used') is True

    def test_rank_population_insufficient_solutions(self):
        """Test ranking with insufficient solutions for JSI."""
        mock_oracle = Mock()
        ranker = create_standard_population_ranker(mock_oracle, show_live_ranking=False)

        solutions = [MockSolution(0.0, 0.0)]  # Only one solution
        audio_paths = {'sol_000': Path('/audio/sol_000.wav')}

        ranked_solutions, fitness_values, ranking_info = ranker.rank_population_with_audio(
            solutions, audio_paths
        )

        assert len(ranked_solutions) == 1
        assert len(fitness_values) == 1
        assert ranking_info.get('fallback_used') is True

    def test_adaptive_quicksort_single_item(self):
        """Test JSI sorting with single item."""
        mock_oracle = Mock()
        displayer = SilentRankingDisplayer()
        sorter = JSIAdaptiveQuicksort(mock_oracle, displayer)

        solution_ids = ['sol_001']
        audio_paths = {'sol_001': Path('/audio/sol_001.wav')}
        tracker = Mock()

        result = sorter.sort_with_audio(solution_ids, audio_paths, tracker)
        assert result == ['sol_001']

    def test_adaptive_quicksort_multiple_items(self):
        """Test JSI sorting with multiple items."""
        mock_oracle = Mock()
        mock_oracle.compare.return_value = True  # First item always wins

        displayer = SilentRankingDisplayer()
        sorter = JSIAdaptiveQuicksort(mock_oracle, displayer)

        solution_ids = ['sol_001', 'sol_002', 'sol_003']
        audio_paths = {
            'sol_001': Path('/audio/sol_001.wav'),
            'sol_002': Path('/audio/sol_002.wav'),
            'sol_003': Path('/audio/sol_003.wav')
        }
        tracker = Mock()

        result = sorter.sort_with_audio(solution_ids, audio_paths, tracker)

        # Should return all items in some order
        assert len(result) == 3
        assert set(result) == set(solution_ids)


class TestJSIFitnessEvaluator:
    """Test cases for refactored JSIFitnessEvaluator."""

    def test_initialization(self):
        """Test fitness evaluator initialization."""
        mock_oracle = Mock()
        ranker = create_standard_population_ranker(mock_oracle)
        evaluator = JSIFitnessEvaluator(ranker, "exponential")

        assert evaluator.ranker is ranker
        assert evaluator.fitness_normalization == "exponential"

    def test_initialization_with_custom_normalization(self):
        """Test fitness evaluator with custom normalization."""
        mock_oracle = Mock()
        ranker = create_standard_population_ranker(mock_oracle)
        evaluator = JSIFitnessEvaluator(ranker, "linear")

        assert evaluator.fitness_normalization == "linear"

    def test_evaluate_population_fitness_exponential(self):
        """Test population fitness evaluation with exponential normalization."""
        mock_oracle = Mock()
        ranker = create_standard_population_ranker(mock_oracle, show_live_ranking=False)
        evaluator = JSIFitnessEvaluator(ranker, "exponential")

        solutions = [MockSolution(), MockSolution()]
        audio_paths = {}  # Will trigger fallback

        fitness_values = evaluator.evaluate_population_fitness(solutions, audio_paths)

        assert len(fitness_values) == 2
        assert all(isinstance(f, float) for f in fitness_values)

    def test_evaluate_population_fitness_linear(self):
        """Test population fitness evaluation with linear normalization."""
        mock_oracle = Mock()
        ranker = create_standard_population_ranker(mock_oracle, show_live_ranking=False)
        evaluator = JSIFitnessEvaluator(ranker, "linear")

        solutions = [MockSolution(), MockSolution()]
        audio_paths = {}  # Will trigger fallback

        fitness_values = evaluator.evaluate_population_fitness(solutions, audio_paths)

        assert len(fitness_values) == 2
        assert all(isinstance(f, float) for f in fitness_values)

    def test_evaluate_population_fitness_inverse(self):
        """Test population fitness evaluation with inverse normalization."""
        mock_oracle = Mock()
        ranker = create_standard_population_ranker(mock_oracle, show_live_ranking=False)
        evaluator = JSIFitnessEvaluator(ranker, "inverse")

        solutions = [MockSolution(), MockSolution()]
        audio_paths = {}  # Will trigger fallback

        fitness_values = evaluator.evaluate_population_fitness(solutions, audio_paths)

        assert len(fitness_values) == 2
        assert all(isinstance(f, float) for f in fitness_values)

    def test_get_ranking_info(self):
        """Test getting ranking information."""
        mock_oracle = Mock()
        ranker = create_standard_population_ranker(mock_oracle)
        ranker.comparison_count = 10
        ranker.generation_count = 3

        evaluator = JSIFitnessEvaluator(ranker, "exponential")

        info = evaluator.get_ranking_info()

        assert info['comparison_count'] == 10
        assert info['generation_count'] == 3
        assert info['fitness_normalization'] == "exponential"


# Additional tests for the new components
class TestFitnessCalculator:
    """Test cases for FitnessCalculator."""

    def test_ranking_to_fitness_exponential(self):
        """Test exponential fitness calculation."""
        ranked_ids = ['sol_001', 'sol_002', 'sol_003']
        fitness_values = FitnessCalculator.ranking_to_fitness(ranked_ids, "exponential")

        assert len(fitness_values) == 3
        assert fitness_values[0] > fitness_values[1] > fitness_values[2]  # Decreasing

    def test_ranking_to_fitness_linear(self):
        """Test linear fitness calculation."""
        ranked_ids = ['sol_001', 'sol_002', 'sol_003']
        fitness_values = FitnessCalculator.ranking_to_fitness(ranked_ids, "linear")

        assert len(fitness_values) == 3
        assert fitness_values[0] > fitness_values[1] > fitness_values[2]  # Decreasing

    def test_ranking_to_fitness_inverse(self):
        """Test inverse fitness calculation."""
        ranked_ids = ['sol_001', 'sol_002', 'sol_003']
        fitness_values = FitnessCalculator.ranking_to_fitness(ranked_ids, "inverse")

        assert len(fitness_values) == 3
        assert fitness_values[0] > fitness_values[1] > fitness_values[2]  # Decreasing

    def test_add_penalty_fitness(self):
        """Test adding penalty fitness values."""
        existing_fitness = [1.0, 0.8, 0.6]
        extended_fitness = FitnessCalculator.add_penalty_fitness(existing_fitness, 2, 0.01)

        assert len(extended_fitness) == 5
        assert extended_fitness[-2:] == [0.01, 0.01]  # Penalty values
