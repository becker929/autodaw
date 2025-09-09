"""Tests for src/ranking/fitness_normalizer.py module."""

import pytest
import numpy as np
from unittest.mock import patch

from serum_evolver.src.ranking.fitness_normalizer import FitnessNormalizer


class TestFitnessNormalizer:
    """Test cases for FitnessNormalizer class."""

    def test_initialization_default(self):
        """Test default initialization."""
        normalizer = FitnessNormalizer()
        assert normalizer.temperature == 1.0

    def test_initialization_custom_temperature(self):
        """Test initialization with custom temperature."""
        normalizer = FitnessNormalizer(temperature=2.5)
        assert normalizer.temperature == 2.5

    def test_softmax_normalize_empty(self):
        """Test softmax normalization with empty input."""
        normalizer = FitnessNormalizer()
        result = normalizer.softmax_normalize({})
        assert result == {}

    def test_softmax_normalize_single_item(self):
        """Test softmax normalization with single item."""
        normalizer = FitnessNormalizer()
        strengths = {'item1': 2.0}
        result = normalizer.softmax_normalize(strengths)
        assert list(result.keys()) == ['item1']
        assert abs(result['item1'] - 1.0) < 1e-10

    def test_softmax_normalize_multiple_items(self):
        """Test softmax normalization with multiple items."""
        normalizer = FitnessNormalizer()
        strengths = {'item1': 1.0, 'item2': 2.0, 'item3': 0.0}
        result = normalizer.softmax_normalize(strengths)

        # Check that all items are present
        assert set(result.keys()) == set(strengths.keys())

        # Check that values sum to 1.0
        assert abs(sum(result.values()) - 1.0) < 1e-10

        # Check that higher strength gets higher fitness
        assert result['item2'] > result['item1'] > result['item3']

        # All values should be positive
        for value in result.values():
            assert value > 0

    def test_softmax_normalize_with_temperature(self):
        """Test softmax normalization with different temperature values."""
        strengths = {'item1': 1.0, 'item2': 2.0}

        # High temperature should make distribution more uniform
        high_temp_normalizer = FitnessNormalizer(temperature=10.0)
        high_temp_result = high_temp_normalizer.softmax_normalize(strengths)

        # Low temperature should make distribution more peaked
        low_temp_normalizer = FitnessNormalizer(temperature=0.1)
        low_temp_result = low_temp_normalizer.softmax_normalize(strengths)

        # High temperature should have smaller difference between values
        high_temp_diff = high_temp_result['item2'] - high_temp_result['item1']
        low_temp_diff = low_temp_result['item2'] - low_temp_result['item1']

        assert high_temp_diff < low_temp_diff

    def test_softmax_normalize_numerical_stability(self):
        """Test softmax normalization with large values for numerical stability."""
        normalizer = FitnessNormalizer()
        # Large values that could cause overflow without proper scaling
        strengths = {'item1': 1000.0, 'item2': 1001.0, 'item3': 999.0}
        result = normalizer.softmax_normalize(strengths)

        # Should not have any NaN or inf values
        for value in result.values():
            assert not np.isnan(value)
            assert not np.isinf(value)
            assert value > 0

        # Should still sum to 1.0
        assert abs(sum(result.values()) - 1.0) < 1e-10

    def test_exponential_normalize_empty(self):
        """Test exponential normalization with empty input."""
        normalizer = FitnessNormalizer()
        result = normalizer.exponential_normalize({})
        assert result == {}

    def test_exponential_normalize_basic(self):
        """Test exponential normalization with basic input."""
        normalizer = FitnessNormalizer()
        strengths = {'item1': 0.0, 'item2': 1.0, 'item3': -1.0}
        result = normalizer.exponential_normalize(strengths)

        # Check expected exponential values
        expected = {
            'item1': np.exp(0.0),  # 1.0
            'item2': np.exp(1.0),  # ~2.718
            'item3': np.exp(-1.0)  # ~0.368
        }

        for item in strengths:
            assert abs(result[item] - expected[item]) < 1e-10

    def test_exponential_normalize_large_values(self):
        """Test exponential normalization with large values."""
        normalizer = FitnessNormalizer()
        strengths = {'item1': 10.0, 'item2': -10.0}
        result = normalizer.exponential_normalize(strengths)

        # Should handle large positive and negative values
        assert result['item1'] > 1000  # exp(10) is large
        assert result['item2'] < 0.001  # exp(-10) is small
        assert not np.isnan(result['item1'])
        assert not np.isnan(result['item2'])

    def test_min_max_normalize_empty(self):
        """Test min-max normalization with empty input."""
        normalizer = FitnessNormalizer()
        result = normalizer.min_max_normalize({})
        assert result == {}

    def test_min_max_normalize_single_item(self):
        """Test min-max normalization with single item."""
        normalizer = FitnessNormalizer()
        strengths = {'item1': 5.0}
        result = normalizer.min_max_normalize(strengths)
        assert result == {'item1': 0.5}

    def test_min_max_normalize_equal_values(self):
        """Test min-max normalization when all values are equal."""
        normalizer = FitnessNormalizer()
        strengths = {'item1': 3.0, 'item2': 3.0, 'item3': 3.0}
        result = normalizer.min_max_normalize(strengths)

        for value in result.values():
            assert value == 0.5

    def test_min_max_normalize_basic(self):
        """Test min-max normalization with basic input."""
        normalizer = FitnessNormalizer()
        strengths = {'item1': 0.0, 'item2': 10.0, 'item3': 5.0}
        result = normalizer.min_max_normalize(strengths)

        # Check expected normalized values
        assert result['item1'] == 0.0  # min value -> 0
        assert result['item2'] == 1.0  # max value -> 1
        assert result['item3'] == 0.5  # middle value -> 0.5

    def test_min_max_normalize_negative_values(self):
        """Test min-max normalization with negative values."""
        normalizer = FitnessNormalizer()
        strengths = {'item1': -10.0, 'item2': 0.0, 'item3': -5.0}
        result = normalizer.min_max_normalize(strengths)

        # Range is 10 (from -10 to 0)
        assert result['item1'] == 0.0  # min value
        assert result['item2'] == 1.0  # max value
        assert result['item3'] == 0.5  # middle value

    def test_get_fitness_summary(self):
        """Test fitness summary generation."""
        normalizer = FitnessNormalizer()
        strengths = {'item1': 1.0, 'item2': 2.0}
        result = normalizer.get_fitness_summary(strengths)

        # Check that all expected methods are included
        expected_keys = ['raw_strengths', 'softmax', 'exponential', 'min_max']
        assert set(result.keys()) == set(expected_keys)

        # Check that raw strengths are preserved
        assert result['raw_strengths'] == strengths

        # Check that each method produces results
        for method in ['softmax', 'exponential', 'min_max']:
            assert len(result[method]) == len(strengths)
            for item in strengths:
                assert item in result[method]

    def test_get_fitness_summary_empty(self):
        """Test fitness summary with empty input."""
        normalizer = FitnessNormalizer()
        result = normalizer.get_fitness_summary({})

        for method in ['raw_strengths', 'softmax', 'exponential', 'min_max']:
            assert result[method] == {}

    def test_rank_by_fitness_basic(self):
        """Test ranking by fitness values."""
        normalizer = FitnessNormalizer()
        fitness_values = {'item1': 0.3, 'item2': 0.7, 'item3': 0.1}
        result = normalizer.rank_by_fitness(fitness_values)

        # Should be sorted by fitness (highest first)
        assert result == [('item2', 0.7), ('item1', 0.3), ('item3', 0.1)]

    def test_rank_by_fitness_equal_values(self):
        """Test ranking with equal fitness values."""
        normalizer = FitnessNormalizer()
        fitness_values = {'item1': 0.5, 'item2': 0.5}
        result = normalizer.rank_by_fitness(fitness_values)

        # Should have both items, order may vary but values should be correct
        assert len(result) == 2
        assert all(value == 0.5 for _, value in result)
        assert set(item for item, _ in result) == {'item1', 'item2'}

    def test_rank_by_fitness_empty(self):
        """Test ranking with empty input."""
        normalizer = FitnessNormalizer()
        result = normalizer.rank_by_fitness({})
        assert result == []

    def test_rank_by_fitness_single_item(self):
        """Test ranking with single item."""
        normalizer = FitnessNormalizer()
        fitness_values = {'item1': 0.8}
        result = normalizer.rank_by_fitness(fitness_values)
        assert result == [('item1', 0.8)]

    def test_integration_workflow(self):
        """Test a complete workflow integrating multiple methods."""
        normalizer = FitnessNormalizer(temperature=0.5)

        # Start with Bradley-Terry strengths
        strengths = {
            'solution_a': 1.5,
            'solution_b': -0.5,
            'solution_c': 0.0,
            'solution_d': 2.0
        }

        # Get all normalization results
        summary = normalizer.get_fitness_summary(strengths)

        # Test softmax ranking
        softmax_ranking = normalizer.rank_by_fitness(summary['softmax'])
        assert softmax_ranking[0][0] == 'solution_d'  # Highest strength
        assert softmax_ranking[-1][0] == 'solution_b'  # Lowest strength

        # Test exponential ranking
        exp_ranking = normalizer.rank_by_fitness(summary['exponential'])
        assert exp_ranking[0][0] == 'solution_d'  # Should match softmax order

        # Test min-max ranking
        minmax_ranking = normalizer.rank_by_fitness(summary['min_max'])
        assert minmax_ranking[0][0] == 'solution_d'  # Should match others
