"""Display functionality for live ranking updates."""

import time
from typing import Protocol, List, Tuple
from rich.console import Console

from .display_utils import create_ranking_table
from .ranking_tracker import SimpleRankingTracker


class RankingDisplayer(Protocol):
    """Protocol for displaying ranking updates."""

    def show_ranking(
        self,
        tracker: SimpleRankingTracker,
        generation: int,
        comparison_count: int
    ) -> None:
        """Show current ranking."""
        ...


class LiveRankingDisplayer:
    """Displays live ranking updates using Rich console."""

    def __init__(self, enabled: bool = True):
        self.enabled = enabled

    def show_ranking(
        self,
        tracker: SimpleRankingTracker,
        generation: int,
        comparison_count: int
    ) -> None:
        """Show current ranking with Rich console."""
        if not self.enabled:
            return

        # Create console locally to avoid serialization issues
        console = Console()

        current_ranking = tracker.get_simple_ranking()
        table = create_ranking_table(
            current_ranking,
            title=f"Live JSI Ranking (Gen {generation}, {comparison_count} comparisons)"
        )

        console.clear()
        console.print(table)
        time.sleep(0.1)  # Brief pause for visibility


class SilentRankingDisplayer:
    """Silent displayer that does nothing - useful for testing."""

    def show_ranking(
        self,
        tracker: SimpleRankingTracker,
        generation: int,
        comparison_count: int
    ) -> None:
        """Do nothing."""
        pass


class LoggingRankingDisplayer:
    """Displayer that logs ranking to console without Rich formatting."""

    def show_ranking(
        self,
        tracker: SimpleRankingTracker,
        generation: int,
        comparison_count: int
    ) -> None:
        """Log current ranking to console."""
        current_ranking = tracker.get_simple_ranking()
        print(f"\n=== JSI Ranking Generation {generation} ===")
        print(f"Comparisons: {comparison_count}")

        for i, (item, rank) in enumerate(current_ranking, 1):
            print(f"{i}. {item} (rank: {rank})")
        print()
