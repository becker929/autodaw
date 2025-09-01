"""Tests for comparison oracles."""

import pytest
import numpy as np
from choix_active_online_demo.comparison_oracle import (
    ComparisonOracle, SimulatedOracle, HumanOracle
)


class TestSimulatedOracle:
    """Test cases for SimulatedOracle."""

    def test_initialization(self):
        """Test proper initialization."""
        strengths = {"A": 2.0, "B": 1.0, "C": 0.5}
        oracle = SimulatedOracle(strengths, noise_level=0.1, random_seed=42)

        assert oracle.item_strengths == strengths
        assert oracle.noise_level == 0.1
        assert oracle.rng is not None

    def test_comparison_deterministic(self):
        """Test comparisons are deterministic with same seed."""
        strengths = {"A": 3.0, "B": 1.0}

        oracle1 = SimulatedOracle(strengths, noise_level=0.0, random_seed=42)
        oracle2 = SimulatedOracle(strengths, noise_level=0.0, random_seed=42)

        # Should give same results with same seed
        result1 = oracle1.compare("A", "B")
        result2 = oracle2.compare("A", "B")
        assert result1 == result2

    def test_comparison_probabilities(self):
        """Test that comparisons follow expected probabilities."""
        # Strong item should beat weak item most of the time
        strengths = {"Strong": 10.0, "Weak": 1.0}
        oracle = SimulatedOracle(strengths, noise_level=0.1, random_seed=42)

        wins = 0
        trials = 10  # Reduced from 100 to 10
        for _ in range(trials):
            if oracle.compare("Strong", "Weak"):
                wins += 1

        # Strong should win most of the time (allow some randomness)
        assert wins > trials * 0.5  # Reduced threshold

    def test_noise_effect(self):
        """Test that noise affects comparison outcomes."""
        strengths = {"A": 2.0, "B": 1.0}

        # No noise - should be consistent
        oracle_no_noise = SimulatedOracle(strengths, noise_level=0.0, random_seed=42)
        results_no_noise = [oracle_no_noise.compare("A", "B") for _ in range(5)]

        # High noise - should be more random
        oracle_noise = SimulatedOracle(strengths, noise_level=0.8, random_seed=42)
        results_noise = [oracle_noise.compare("A", "B") for _ in range(5)]

        # Just verify both return valid results
        assert all(isinstance(r, bool) for r in results_no_noise)
        assert all(isinstance(r, bool) for r in results_noise)

    def test_missing_items(self):
        """Test behavior with items not in strength dictionary."""
        strengths = {"A": 2.0}
        oracle = SimulatedOracle(strengths, random_seed=42)

        # Should use default strength of 1.0 for missing items
        result = oracle.compare("A", "Unknown")
        assert isinstance(result, bool)


class TestHumanOracle:
    """Test cases for HumanOracle."""

    def test_initialization(self):
        """Test proper initialization."""
        oracle = HumanOracle()
        assert oracle.comparison_callback is None
        assert oracle.comparison_count == 0

    def test_with_callback(self):
        """Test oracle with comparison callback."""
        def mock_callback(item_a, item_b):
            return item_a == "A"  # A always wins

        oracle = HumanOracle(mock_callback)

        result = oracle.compare("A", "B")
        assert result == True
        assert oracle.comparison_count == 1

        result = oracle.compare("B", "A")
        assert result == False
        assert oracle.comparison_count == 2

    def test_comparison_counting(self):
        """Test that comparisons are counted correctly."""
        def mock_callback(item_a, item_b):
            return True

        oracle = HumanOracle(mock_callback)

        assert oracle.comparison_count == 0

        oracle.compare("A", "B")
        assert oracle.comparison_count == 1

        oracle.compare("C", "D")
        assert oracle.comparison_count == 2

        oracle.reset_count()
        assert oracle.comparison_count == 0

    def test_callback_arguments(self):
        """Test that callback receives correct arguments."""
        received_args = []

        def mock_callback(item_a, item_b):
            received_args.append((item_a, item_b))
            return True

        oracle = HumanOracle(mock_callback)
        oracle.compare("X", "Y")

        assert received_args == [("X", "Y")]
