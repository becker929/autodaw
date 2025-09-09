"""Tests for src/ranking/comparison_oracle.py module."""

import pytest
import numpy as np
from unittest.mock import Mock, patch
from io import StringIO

from serum_evolver.src.ranking.comparison_oracle import ComparisonOracle


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
