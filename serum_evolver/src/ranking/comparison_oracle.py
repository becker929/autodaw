"""Comparison oracles for active learning."""

from abc import ABC, abstractmethod
import numpy as np
from typing import Any, Optional


class ComparisonOracle(ABC):
    """Abstract base class for comparison oracles."""

    @abstractmethod
    def compare(self, item_a: Any, item_b: Any) -> bool:
        """Compare two items.

        Args:
            item_a: First item to compare
            item_b: Second item to compare

        Returns:
            True if item_a is better than item_b, False otherwise
        """
        pass


