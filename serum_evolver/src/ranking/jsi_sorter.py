"""JSI adaptive quicksort implementation."""

from typing import List, Dict, Any
from pathlib import Path

from .comparison_oracle import ComparisonOracle
from .ranking_tracker import SimpleRankingTracker
from .ranking_display import RankingDisplayer, SilentRankingDisplayer


class JSIAdaptiveQuicksort:
    """Pure JSI adaptive quicksort implementation with dependency injection."""

    def __init__(
        self,
        oracle: ComparisonOracle,
        displayer: RankingDisplayer = None
    ):
        self.oracle = oracle
        self.displayer = displayer or SilentRankingDisplayer()
        self.comparison_count = 0

    def sort_with_audio(
        self,
        solution_ids: List[str],
        audio_paths: Dict[str, Path],
        tracker: SimpleRankingTracker,
        generation: int = 0
    ) -> List[str]:
        """Sort solution IDs using JSI with audio comparisons.

        Args:
            solution_ids: List of solution IDs to sort
            audio_paths: Mapping of solution IDs to audio file paths
            tracker: Ranking tracker for maintaining comparisons
            generation: Generation number for display

        Returns:
            List of solution IDs in sorted order
        """
        if len(solution_ids) <= 1:
            return solution_ids.copy()

        # Choose pivot (first item)
        pivot = solution_ids[0]
        rest = solution_ids[1:]

        # Partition around pivot
        less = []
        greater = []

        for item in rest:
            # Get audio paths for comparison
            item_path = audio_paths.get(item)
            pivot_path = audio_paths.get(pivot)

            if not item_path or not pivot_path:
                # If we can't compare, put in less partition
                less.append(item)
                continue

            # Make comparison using oracle
            if self.oracle.compare(item_path, pivot_path):
                # item > pivot
                greater.append(item)
                winner = item
            else:
                # pivot >= item
                less.append(item)
                winner = pivot

            # Record comparison
            tracker.add_comparison(item, pivot, winner)
            self.comparison_count += 1

            # Show live ranking if enabled
            if self.comparison_count % 5 == 0:
                self.displayer.show_ranking(tracker, generation, self.comparison_count)

        # Recursively sort partitions
        sorted_less = self.sort_with_audio(less, audio_paths, tracker, generation)
        sorted_greater = self.sort_with_audio(greater, audio_paths, tracker, generation)

        return sorted_less + [pivot] + sorted_greater


class FallbackSorter:
    """Fallback sorting when JSI is not applicable."""

    @staticmethod
    def sort_by_parameter_distance(solutions: List[Any]) -> List[Any]:
        """Sort solutions by their parameter distance from origin.

        This is a fallback when audio-based comparison is not possible.
        """
        def distance_from_origin(solution):
            if hasattr(solution, 'octave') and hasattr(solution, 'fine'):
                return abs(solution.octave) + abs(solution.fine)
            return 0

        return sorted(solutions, key=distance_from_origin)

    @staticmethod
    def create_fallback_fitness(solutions: List[Any]) -> List[float]:
        """Create fallback fitness values based on parameter distance."""
        distances = []
        for solution in solutions:
            if hasattr(solution, 'octave') and hasattr(solution, 'fine'):
                distance = abs(solution.octave) + abs(solution.fine)
            else:
                distance = 1.0
            distances.append(distance)

        # Convert distances to fitness (lower distance = higher fitness)
        max_distance = max(distances) if distances else 1.0
        fitness_values = []

        for distance in distances:
            if max_distance > 0:
                fitness = 1.0 - (distance / max_distance)
            else:
                fitness = 1.0
            fitness_values.append(max(fitness, 0.01))  # Minimum fitness

        return fitness_values
