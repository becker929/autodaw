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


class SimulatedOracle(ComparisonOracle):
    """Simulated oracle using ground truth with noise for demonstrations."""

    def __init__(self, item_strengths: dict, noise_level: float = 0.1, random_seed: int = 42):
        """Initialize simulated oracle.

        Args:
            item_strengths: Dictionary mapping items to their true strength values
            noise_level: Amount of noise to add (0.0 = perfect, 1.0 = random)
            random_seed: Random seed for reproducibility
        """
        self.item_strengths = item_strengths
        self.noise_level = noise_level
        self.rng = np.random.RandomState(random_seed)

    def compare(self, item_a: Any, item_b: Any) -> bool:
        """Compare items using Bradley-Terry model with noise.

        Args:
            item_a: First item to compare
            item_b: Second item to compare

        Returns:
            True if item_a is better than item_b, False otherwise
        """
        # Get true strengths
        strength_a = self.item_strengths.get(item_a, 1.0)
        strength_b = self.item_strengths.get(item_b, 1.0)

        # Bradley-Terry probability that A beats B
        prob_a_wins = strength_a / (strength_a + strength_b)

        # Add noise by interpolating with random decision
        noisy_prob = (1 - self.noise_level) * prob_a_wins + self.noise_level * 0.5

        # Make stochastic decision
        return self.rng.random() < noisy_prob


class HumanOracle(ComparisonOracle):
    """Human oracle that prompts user via callback for comparisons."""

    def __init__(self, comparison_callback: Optional[callable] = None):
        """Initialize human oracle.

        Args:
            comparison_callback: Function to call for comparisons.
                                Should take (item_a, item_b) and return bool.
                                If None, will use simple input prompt.
        """
        self.comparison_callback = comparison_callback
        self._comparison_count = 0

    def compare(self, item_a: Any, item_b: Any) -> bool:
        """Compare items by asking human user.

        Args:
            item_a: First item to compare
            item_b: Second item to compare

        Returns:
            True if item_a is better than item_b, False otherwise
        """
        self._comparison_count += 1

        if self.comparison_callback:
            return self.comparison_callback(item_a, item_b)
        else:
            # Fallback to simple console prompt
            while True:
                response = input(f"Which is better? (1) {item_a} or (2) {item_b}? [1/2]: ").strip()
                if response == "1":
                    return True
                elif response == "2":
                    return False
                else:
                    print("Please enter 1 or 2")

    @property
    def comparison_count(self) -> int:
        """Get number of comparisons made."""
        return self._comparison_count

    def reset_count(self) -> None:
        """Reset comparison counter."""
        self._comparison_count = 0
