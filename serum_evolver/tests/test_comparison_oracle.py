"""Tests for src/ranking/comparison_oracle.py module."""

import pytest
import numpy as np
from unittest.mock import Mock, patch
from io import StringIO

from serum_evolver.src.ranking.comparison_oracle import (
    ComparisonOracle, SimulatedOracle, HumanOracle
)


class TestComparisonOracle:
    """Test cases for abstract ComparisonOracle base class."""

    def test_abstract_base_class(self):
        """Test that ComparisonOracle is abstract and cannot be instantiated."""
        with pytest.raises(TypeError):
            ComparisonOracle()

    def test_compare_method_is_abstract(self):
        """Test that compare method is abstract."""
        # Create a concrete subclass without implementing compare
        class IncompleteOracle(ComparisonOracle):
            pass

        # Should not be able to instantiate
        with pytest.raises(TypeError):
            IncompleteOracle()

    def test_concrete_implementation_works(self):
        """Test that concrete implementation can be created."""
        class ConcreteOracle(ComparisonOracle):
            def compare(self, item_a, item_b):
                return True

        oracle = ConcreteOracle()
        assert oracle.compare('a', 'b') is True


class TestSimulatedOracle:
    """Test cases for SimulatedOracle class."""

    def test_initialization_basic(self):
        """Test basic initialization."""
        strengths = {'item1': 2.0, 'item2': 1.0}
        oracle = SimulatedOracle(strengths)

        assert oracle.item_strengths == strengths
        assert oracle.noise_level == 0.1  # default
        assert oracle.rng is not None

    def test_initialization_with_custom_params(self):
        """Test initialization with custom parameters."""
        strengths = {'a': 5.0, 'b': 3.0}
        oracle = SimulatedOracle(strengths, noise_level=0.2, random_seed=123)

        assert oracle.item_strengths == strengths
        assert oracle.noise_level == 0.2
        assert oracle.rng.get_state()[1][0] == 123  # Check seed was set

    def test_compare_with_zero_noise(self):
        """Test comparison with zero noise (mostly deterministic)."""
        strengths = {'strong': 10.0, 'weak': 1.0}
        oracle = SimulatedOracle(strengths, noise_level=0.0, random_seed=42)

        # Strong should beat weak most of the time with zero noise
        # P(strong wins) = 10/(10+1) ≈ 0.91, so expect ~91% win rate
        results = [oracle.compare('strong', 'weak') for _ in range(100)]
        win_rate = sum(results) / len(results)
        assert win_rate > 0.85, f"Strong item should win >85% with zero noise, got {win_rate}"

        # Weak should rarely beat strong
        results = [oracle.compare('weak', 'strong') for _ in range(100)]
        win_rate = sum(results) / len(results)
        assert win_rate < 0.15, f"Weak item should win <15% with zero noise, got {win_rate}"

    def test_compare_with_maximum_noise(self):
        """Test comparison with maximum noise (random)."""
        strengths = {'strong': 10.0, 'weak': 1.0}
        oracle = SimulatedOracle(strengths, noise_level=1.0, random_seed=42)

        # With maximum noise, results should be approximately 50/50
        results = [oracle.compare('strong', 'weak') for _ in range(100)]
        win_rate = sum(results) / len(results)

        # Should be around 0.5 (allowing some variance)
        assert 0.3 < win_rate < 0.7, f"Win rate {win_rate} should be around 0.5 with max noise"

    def test_compare_with_moderate_noise(self):
        """Test comparison with moderate noise."""
        strengths = {'strong': 4.0, 'weak': 1.0}
        oracle = SimulatedOracle(strengths, noise_level=0.3, random_seed=42)

        # With moderate noise, strong should still win more often
        results = [oracle.compare('strong', 'weak') for _ in range(100)]
        win_rate = sum(results) / len(results)

        # Should be better than 50% but not perfect
        assert 0.6 < win_rate < 0.9, f"Win rate {win_rate} should be between 0.6 and 0.9"

    def test_compare_equal_strength_items(self):
        """Test comparison of items with equal strength."""
        strengths = {'item1': 2.0, 'item2': 2.0}
        oracle = SimulatedOracle(strengths, noise_level=0.1, random_seed=42)

        # With equal strengths, should be approximately 50/50
        results = [oracle.compare('item1', 'item2') for _ in range(100)]
        win_rate = sum(results) / len(results)

        # Should be around 0.5
        assert 0.3 < win_rate < 0.7, f"Win rate {win_rate} should be around 0.5 for equal items"

    def test_compare_unknown_items(self):
        """Test comparison of items not in strengths dictionary."""
        strengths = {'known': 3.0}
        oracle = SimulatedOracle(strengths, noise_level=0.0, random_seed=42)

        # Unknown items should get default strength of 1.0
        # So known (3.0) should beat unknown (1.0)
        # P(known wins) = 3/(3+1) = 0.75, so expect ~75% win rate
        results = [oracle.compare('known', 'unknown') for _ in range(100)]
        win_rate = sum(results) / len(results)
        assert win_rate > 0.65, f"Known item should win >65% with zero noise, got {win_rate}"

        # Two unknown items should be equal (both 1.0)
        results = [oracle.compare('unknown1', 'unknown2') for _ in range(100)]
        win_rate = sum(results) / len(results)
        assert 0.3 < win_rate < 0.7, "Unknown items should have equal probability"

    def test_bradley_terry_probability_calculation(self):
        """Test that Bradley-Terry probability is calculated correctly."""
        strengths = {'a': 4.0, 'b': 1.0}
        oracle = SimulatedOracle(strengths, noise_level=0.0, random_seed=42)

        # P(A beats B) = strength_A / (strength_A + strength_B) = 4/(4+1) = 0.8
        # With zero noise, expect ~80% win rate
        results = [oracle.compare('a', 'b') for _ in range(100)]
        win_rate = sum(results) / len(results)
        assert win_rate > 0.7, f"Item 'a' should win >70% with these strengths and zero noise, got {win_rate}"

    def test_reproducibility_with_same_seed(self):
        """Test that results are reproducible with same seed."""
        strengths = {'x': 2.0, 'y': 1.0}

        oracle1 = SimulatedOracle(strengths, noise_level=0.5, random_seed=123)
        oracle2 = SimulatedOracle(strengths, noise_level=0.5, random_seed=123)

        results1 = [oracle1.compare('x', 'y') for _ in range(20)]
        results2 = [oracle2.compare('x', 'y') for _ in range(20)]

        assert results1 == results2, "Results should be identical with same seed"

    def test_different_results_with_different_seeds(self):
        """Test that results differ with different seeds."""
        strengths = {'x': 2.0, 'y': 1.0}

        oracle1 = SimulatedOracle(strengths, noise_level=0.5, random_seed=123)
        oracle2 = SimulatedOracle(strengths, noise_level=0.5, random_seed=456)

        results1 = [oracle1.compare('x', 'y') for _ in range(50)]
        results2 = [oracle2.compare('x', 'y') for _ in range(50)]

        # Should be different (very unlikely to be identical by chance)
        assert results1 != results2, "Results should differ with different seeds"


class TestHumanOracle:
    """Test cases for HumanOracle class."""

    def test_initialization_with_callback(self):
        """Test initialization with custom callback."""
        callback = Mock(return_value=True)
        oracle = HumanOracle(callback)

        assert oracle.comparison_callback is callback
        assert oracle.comparison_count == 0

    def test_initialization_without_callback(self):
        """Test initialization without callback."""
        oracle = HumanOracle()

        assert oracle.comparison_callback is None
        assert oracle.comparison_count == 0

    def test_compare_with_callback(self):
        """Test comparison using callback."""
        callback = Mock(return_value=True)
        oracle = HumanOracle(callback)

        result = oracle.compare('item1', 'item2')

        assert result is True
        assert oracle.comparison_count == 1
        callback.assert_called_once_with('item1', 'item2')

    def test_compare_callback_return_false(self):
        """Test comparison with callback returning False."""
        callback = Mock(return_value=False)
        oracle = HumanOracle(callback)

        result = oracle.compare('a', 'b')

        assert result is False
        assert oracle.comparison_count == 1
        callback.assert_called_once_with('a', 'b')

    def test_comparison_count_increments(self):
        """Test that comparison count increments correctly."""
        callback = Mock(return_value=True)
        oracle = HumanOracle(callback)

        oracle.compare('a', 'b')
        assert oracle.comparison_count == 1

        oracle.compare('c', 'd')
        assert oracle.comparison_count == 2

        oracle.compare('e', 'f')
        assert oracle.comparison_count == 3

    def test_reset_count(self):
        """Test resetting comparison count."""
        callback = Mock(return_value=True)
        oracle = HumanOracle(callback)

        oracle.compare('a', 'b')
        oracle.compare('c', 'd')
        assert oracle.comparison_count == 2

        oracle.reset_count()
        assert oracle.comparison_count == 0

    def test_comparison_count_property(self):
        """Test comparison_count property access."""
        callback = Mock(return_value=True)
        oracle = HumanOracle(callback)

        # Should be readable
        count = oracle.comparison_count
        assert count == 0

        # Should increment after comparison
        oracle.compare('x', 'y')
        assert oracle.comparison_count == 1

    @patch('builtins.input', side_effect=['1'])
    def test_compare_without_callback_choice_1(self, mock_input):
        """Test comparison without callback, choosing option 1."""
        oracle = HumanOracle()

        result = oracle.compare('item1', 'item2')

        assert result is True
        assert oracle.comparison_count == 1
        mock_input.assert_called_once_with("Which is better? (1) item1 or (2) item2? [1/2]: ")

    @patch('builtins.input', side_effect=['2'])
    def test_compare_without_callback_choice_2(self, mock_input):
        """Test comparison without callback, choosing option 2."""
        oracle = HumanOracle()

        result = oracle.compare('item1', 'item2')

        assert result is False
        assert oracle.comparison_count == 1
        mock_input.assert_called_once_with("Which is better? (1) item1 or (2) item2? [1/2]: ")

    @patch('builtins.input', side_effect=['invalid', '3', '1'])
    @patch('builtins.print')
    def test_compare_without_callback_invalid_input(self, mock_print, mock_input):
        """Test comparison without callback with invalid inputs."""
        oracle = HumanOracle()

        result = oracle.compare('item1', 'item2')

        assert result is True
        assert oracle.comparison_count == 1

        # Should have prompted 3 times
        assert mock_input.call_count == 3

        # Should have printed error messages
        assert mock_print.call_count == 2
        mock_print.assert_called_with("Please enter 1 or 2")

    def test_callback_with_different_return_types(self):
        """Test callback with different return types."""
        # Test with various truthy/falsy values
        test_cases = [
            (True, True),
            (False, False),
            (1, True),
            (0, False),
            ('yes', True),
            ('', False),
            ([1], True),
            ([], False),
        ]

        for callback_return, expected_result in test_cases:
            callback = Mock(return_value=callback_return)
            oracle = HumanOracle(callback)

            result = oracle.compare('a', 'b')
            assert bool(result) == expected_result

    def test_multiple_oracles_independent_counts(self):
        """Test that multiple oracle instances have independent counts."""
        callback1 = Mock(return_value=True)
        callback2 = Mock(return_value=False)

        oracle1 = HumanOracle(callback1)
        oracle2 = HumanOracle(callback2)

        oracle1.compare('a', 'b')
        oracle1.compare('c', 'd')

        oracle2.compare('x', 'y')

        assert oracle1.comparison_count == 2
        assert oracle2.comparison_count == 1

        oracle1.reset_count()
        assert oracle1.comparison_count == 0
        assert oracle2.comparison_count == 1  # Should be unchanged
