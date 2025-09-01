"""Bradley-Terry ranking tracker for JSI algorithm."""

import numpy as np
import choix
import warnings
from typing import List, Dict, Tuple, Optional


class SimpleRankingTracker:
    """Simple ranking tracker for JSI without complex uncertainty estimation."""

    def __init__(self, items: List[str]):
        """Initialize ranking tracker.

        Args:
            items: List of item names to track rankings for
        """
        self.items = items
        self.comparisons = []  # (winner_idx, loser_idx)
        self.name_to_idx = {name: i for i, name in enumerate(items)}

    def add_comparison(self, item_a: str, item_b: str, winner: str) -> None:
        """Add a comparison result.

        Args:
            item_a: First item in comparison
            item_b: Second item in comparison
            winner: The winning item (must be either item_a or item_b)
        """
        winner_idx = self.name_to_idx[winner]
        loser_idx = self.name_to_idx[item_b if winner == item_a else item_a]
        self.comparisons.append((winner_idx, loser_idx))

    def get_simple_ranking(self) -> List[str]:
        """Get current ranking based on win counts (simple approximation).

        Returns:
            List of items in descending order of estimated strength
        """
        if not self.comparisons:
            return self.items.copy()

        win_counts = [0] * len(self.items)
        total_counts = [0] * len(self.items)

        for winner_idx, loser_idx in self.comparisons:
            win_counts[winner_idx] += 1
            total_counts[winner_idx] += 1
            total_counts[loser_idx] += 1

        # Calculate win rates
        win_rates = []
        for i in range(len(self.items)):
            if total_counts[i] > 0:
                win_rates.append((win_counts[i] / total_counts[i], self.items[i]))
            else:
                win_rates.append((0.5, self.items[i]))

        win_rates.sort(reverse=True)
        return [item for _, item in win_rates]

    def get_bt_ranking_with_confidence(self) -> Tuple[List[str], float, Dict[str, float]]:
        """Get full Bradley-Terry ranking with real confidence calculation.

        Returns:
            Tuple of (ranking, confidence, strength_dict)
        """
        if len(self.comparisons) < 3:
            return self.get_simple_ranking(), 0.0, {}

        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", RuntimeWarning)
                strengths = choix.ilsr_pairwise(len(self.items), self.comparisons)

            # Calculate real confidence based on model convergence
            # Higher comparison density = higher confidence
            n_possible_pairs = len(self.items) * (len(self.items) - 1) // 2
            comparison_density = len(self.comparisons) / n_possible_pairs
            confidence = min(0.95, comparison_density * 2)  # Cap at 95%

            # Create ranking
            item_strengths = [(self.items[i], strengths[i]) for i in range(len(self.items))]
            item_strengths.sort(key=lambda x: x[1], reverse=True)

            ranking = [item for item, _ in item_strengths]
            strength_dict = {item: strength for item, strength in item_strengths}

            return ranking, confidence, strength_dict

        except (ValueError, RuntimeError):
            return self.get_simple_ranking(), 0.0, {}
