"""Integration of JSI adaptive quicksort with genetic algorithm populations."""

import time
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import numpy as np
from rich.console import Console

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent / "choix_active_online"))
sys.path.append(str(Path(__file__).parent.parent.parent / "pymoo_ga_freq_reaper"))

from choix_active_online_demo.comparison_oracle import ComparisonOracle
from choix_active_online_demo.ranking_tracker import SimpleRankingTracker
from choix_active_online_demo.display_utils import create_ranking_table
from ga_frequency_demo.genetics import Solution


class GAPopulationRanker:
    """JSI-based ranking system for GA populations using audio comparisons."""

    def __init__(
        self,
        oracle: ComparisonOracle,
        console: Optional[Console] = None,
        show_live_ranking: bool = True
    ):
        """Initialize GA population ranker.

        Args:
            oracle: Comparison oracle for pairwise comparisons
            console: Optional Rich console for live display (not stored to avoid serialization issues)
            show_live_ranking: Whether to show live ranking updates
        """
        self.oracle = oracle
        self.show_live_ranking = show_live_ranking
        self.comparison_count = 0
        self.generation_count = 0
        # Don't store console to avoid serialization issues with pymoo

    def rank_population_with_audio(
        self,
        solutions: List[Solution],
        audio_paths: Dict[str, Path],
        generation: int = None
    ) -> Tuple[List[Solution], List[float], Dict[str, Any]]:
        """Rank GA population using JSI with audio-based comparisons.

        Args:
            solutions: List of GA solutions to rank
            audio_paths: Dictionary mapping solution IDs to rendered audio paths
            generation: Optional generation number for tracking

        Returns:
            Tuple of (ranked_solutions, fitness_values, ranking_info)
        """
        if generation is not None:
            self.generation_count = generation

        # Create solution IDs for tracking
        solution_ids = [f"sol_{i:03d}" for i in range(len(solutions))]

        # Initialize ranking tracker
        tracker = SimpleRankingTracker(solution_ids)

        # Filter solutions that have corresponding audio files
        valid_solutions = []
        valid_ids = []
        valid_paths = {}

        for i, (solution, sol_id) in enumerate(zip(solutions, solution_ids)):
            # Look for matching audio path
            matching_path = self._find_matching_audio_path(sol_id, audio_paths)
            if matching_path and matching_path.exists():
                valid_solutions.append(solution)
                valid_ids.append(sol_id)
                valid_paths[sol_id] = matching_path

        if len(valid_solutions) < 2:
            # Not enough valid solutions for ranking
            return self._fallback_ranking(solutions)

        print(f"\n=== JSI Ranking Generation {self.generation_count} ===")
        print(f"Valid solutions with audio: {len(valid_solutions)}/{len(solutions)}")

        # Perform adaptive quicksort with audio comparisons
        ranked_ids = self._adaptive_quicksort_audio(
            valid_ids,
            valid_paths,
            tracker
        )

        # Convert back to solutions and calculate fitness
        ranked_solutions = []
        fitness_values = []

        for rank, sol_id in enumerate(ranked_ids):
            # Find corresponding solution
            idx = valid_ids.index(sol_id)
            solution = valid_solutions[idx]

            # Convert rank to fitness (lower rank = better fitness)
            # Use exponential decay to create meaningful fitness differences
            fitness = np.exp(-rank * 0.5)  # Higher rank gets lower fitness

            ranked_solutions.append(solution)
            fitness_values.append(fitness)

        # Add back invalid solutions with penalty fitness
        penalty_fitness = 0.01  # Very low fitness for missing audio
        for i, solution in enumerate(solutions):
            sol_id = solution_ids[i]
            if sol_id not in valid_ids:
                ranked_solutions.append(solution)
                fitness_values.append(penalty_fitness)

        # Get final ranking information
        if len(valid_solutions) >= 3:
            bt_ranking, confidence, strengths = tracker.get_bt_ranking_with_confidence()
        else:
            bt_ranking = tracker.get_simple_ranking()
            confidence = 0.0
            strengths = {}

        ranking_info = {
            'bt_ranking': bt_ranking,
            'confidence': confidence,
            'strengths': strengths,
            'comparisons_made': self.comparison_count,
            'valid_solutions': len(valid_solutions),
            'total_solutions': len(solutions)
        }

        print(f"Ranking complete: {self.comparison_count} comparisons, confidence: {confidence:.3f}")

        return ranked_solutions, fitness_values, ranking_info

    def _adaptive_quicksort_audio(
        self,
        solution_ids: List[str],
        audio_paths: Dict[str, Path],
        tracker: SimpleRankingTracker
    ) -> List[str]:
        """Perform adaptive quicksort using audio-based comparisons.

        Args:
            solution_ids: List of solution IDs to sort
            audio_paths: Dictionary mapping IDs to audio file paths
            tracker: Ranking tracker for Bradley-Terry model

        Returns:
            List of solution IDs in ranked order (best to worst)
        """
        if len(solution_ids) <= 1:
            return solution_ids.copy()

        # Choose pivot (first item)
        pivot = solution_ids[0]
        rest = solution_ids[1:]

        # Partition around pivot
        better = []  # Items better than pivot
        worse = []   # Items worse than pivot

        for sol_id in rest:
            # Make audio comparison
            pivot_path = audio_paths[pivot]
            item_path = audio_paths[sol_id]

            # oracle.compare returns True if first item is better
            if self.oracle.compare(item_path, pivot_path):
                # sol_id is better than pivot
                better.append(sol_id)
                winner = sol_id
            else:
                # pivot is better than or equal to sol_id
                worse.append(sol_id)
                winner = pivot

            # Record comparison for Bradley-Terry model
            tracker.add_comparison(sol_id, pivot, winner)
            self.comparison_count += 1

            # Show live ranking if enabled
            if self.show_live_ranking and self.comparison_count % 5 == 0:
                self._show_live_ranking(tracker)

        # Recursively sort partitions
        sorted_better = self._adaptive_quicksort_audio(better, audio_paths, tracker)
        sorted_worse = self._adaptive_quicksort_audio(worse, audio_paths, tracker)

        # Return in order: better items, pivot, worse items
        return sorted_better + [pivot] + sorted_worse

    def _find_matching_audio_path(
        self,
        solution_id: str,
        audio_paths: Dict[str, Path]
    ) -> Optional[Path]:
        """Find audio path matching the solution ID.

        Args:
            solution_id: ID of the solution
            audio_paths: Dictionary of available audio paths

        Returns:
            Matching Path or None if not found
        """
        # Direct match
        if solution_id in audio_paths:
            return audio_paths[solution_id]

        # Fuzzy match - look for solution ID in path keys
        for path_key, path in audio_paths.items():
            if solution_id in path_key or path_key in solution_id:
                return path

        # Try extracting individual number from solution_id
        try:
            sol_num = solution_id.split('_')[-1]  # Get number part
            for path_key, path in audio_paths.items():
                if sol_num in path_key:
                    return path
        except (IndexError, ValueError):
            pass

        return None

    def _show_live_ranking(self, tracker: SimpleRankingTracker) -> None:
        """Display live ranking updates.

        Args:
            tracker: Current ranking tracker
        """
        if not self.show_live_ranking:
            return

        # Create console locally to avoid serialization issues
        from rich.console import Console
        console = Console()

        current_ranking = tracker.get_simple_ranking()
        table = create_ranking_table(
            current_ranking,
            title=f"Live JSI Ranking (Gen {self.generation_count}, {self.comparison_count} comparisons)"
        )

        console.clear()
        console.print(table)
        time.sleep(0.1)  # Brief pause for visibility

    def _fallback_ranking(
        self,
        solutions: List[Solution]
    ) -> Tuple[List[Solution], List[float], Dict[str, Any]]:
        """Fallback ranking when insufficient valid solutions.

        Args:
            solutions: Original solutions list

        Returns:
            Tuple with original order and uniform fitness
        """
        print("Warning: Insufficient valid audio files for JSI ranking, using fallback")

        # Assign uniform fitness with slight variation
        fitness_values = [1.0 - i * 0.01 for i in range(len(solutions))]

        ranking_info = {
            'bt_ranking': [f"sol_{i:03d}" for i in range(len(solutions))],
            'confidence': 0.0,
            'strengths': {},
            'comparisons_made': 0,
            'valid_solutions': 0,
            'total_solutions': len(solutions)
        }

        return solutions, fitness_values, ranking_info


class JSIFitnessEvaluator:
    """Fitness evaluator that uses JSI ranking instead of direct distance calculation."""

    def __init__(
        self,
        oracle: ComparisonOracle,
        console: Optional[Console] = None,
        fitness_normalization: str = "exponential"
    ):
        """Initialize JSI fitness evaluator.

        Args:
            oracle: Comparison oracle for audio comparisons
            console: Optional console for display
            fitness_normalization: Method for converting ranks to fitness ("exponential", "linear", "inverse")
        """
        self.ranker = GAPopulationRanker(oracle, console)
        self.fitness_normalization = fitness_normalization

    def evaluate_population_fitness(
        self,
        solutions: List[Solution],
        audio_paths: Dict[str, Path],
        generation: int = None
    ) -> List[float]:
        """Evaluate population fitness using JSI ranking.

        Args:
            solutions: List of solutions to evaluate
            audio_paths: Dictionary mapping solution IDs to audio paths
            generation: Current generation number

        Returns:
            List of fitness values (higher is better for maximization)
        """
        _, fitness_values, ranking_info = self.ranker.rank_population_with_audio(
            solutions, audio_paths, generation
        )

        # Normalize fitness values based on selected method
        if self.fitness_normalization == "exponential":
            # Already done in ranker
            pass
        elif self.fitness_normalization == "linear":
            # Linear decrease from 1.0 to 0.1
            n = len(fitness_values)
            fitness_values = [1.0 - 0.9 * i / max(1, n - 1) for i in range(n)]
        elif self.fitness_normalization == "inverse":
            # Inverse of rank + 1
            fitness_values = [1.0 / (i + 1) for i in range(len(fitness_values))]

        return fitness_values

    def get_ranking_info(self) -> Dict[str, Any]:
        """Get information about the last ranking operation.

        Returns:
            Dictionary with ranking statistics
        """
        return {
            'comparison_count': self.ranker.comparison_count,
            'generation_count': self.ranker.generation_count
        }
