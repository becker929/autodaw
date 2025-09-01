"""Just Sort It (JSI) adaptive quicksort engine."""

import time
from typing import List, Any, Optional
from rich.console import Console
from .comparison_oracle import ComparisonOracle
from .ranking_tracker import SimpleRankingTracker


class JSIAdaptiveQuicksort:
    """Pure JSI adaptive quicksort implementation."""

    def __init__(self, oracle: ComparisonOracle, ranking_tracker: SimpleRankingTracker):
        """Initialize JSI engine.

        Args:
            oracle: Comparison oracle for making pairwise comparisons
            ranking_tracker: Tracker for maintaining Bradley-Terry model
        """
        self.oracle = oracle
        self.tracker = ranking_tracker
        self.comparison_count = 0

    def adaptive_quicksort(self, items: List[Any], console: Optional[Console] = None) -> List[Any]:
        """JSI adaptive quicksort with live ranking display.

        Args:
            items: List of items to sort
            console: Optional Rich console for live display

        Returns:
            Sorted list of items
        """
        if len(items) <= 1:
            return items.copy()

        # Choose pivot (first item)
        pivot = items[0]
        rest = items[1:]

        # Partition around pivot with live display
        less = []
        greater = []

        for item in rest:
            # Make comparison
            if self.oracle.compare(item, pivot):
                # item > pivot
                greater.append(item)
                winner = item
            else:
                # pivot >= item
                less.append(item)
                winner = pivot

            # Record comparison
            self.tracker.add_comparison(item, pivot, winner)
            self.comparison_count += 1

            # Show simple ranking after each comparison (no BT model yet)
            if console:
                from .display_utils import create_ranking_table
                current_ranking = self.tracker.get_simple_ranking()
                table = create_ranking_table(
                    current_ranking,
                    title=f"Live Ranking (after {self.comparison_count} comparisons)"
                )
                console.clear()
                console.print(table)

        # Recursively sort partitions
        sorted_less = self.adaptive_quicksort(less, console)
        sorted_greater = self.adaptive_quicksort(greater, console)

        return sorted_less + [pivot] + sorted_greater
