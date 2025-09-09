"""Refactored population ranking with dependency injection and composition."""

from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

from .comparison_oracle import ComparisonOracle
from .ranking_tracker import SimpleRankingTracker
from .audio_path_matcher import AudioPathMatcher
from .ranking_display import RankingDisplayer, LiveRankingDisplayer
from .jsi_sorter import JSIAdaptiveQuicksort, FallbackSorter
from .fitness_calculator import FitnessCalculator, RankingInfoBuilder
from ..genetics.genetics import Solution


class GAPopulationRanker:
    """JSI-based ranking system for GA populations using composition and dependency injection."""

    def __init__(
        self,
        oracle: ComparisonOracle,
        path_matcher: AudioPathMatcher = None,
        displayer: RankingDisplayer = None,
        sorter: JSIAdaptiveQuicksort = None,
        fitness_calculator: FitnessCalculator = None
    ):
        """Initialize GA population ranker with injected dependencies.

        Args:
            oracle: Comparison oracle for pairwise comparisons
            path_matcher: Component for matching solution IDs to audio paths
            displayer: Component for displaying live ranking updates
            sorter: JSI sorter for ranking solutions
            fitness_calculator: Component for calculating fitness from rankings
        """
        self.oracle = oracle
        self.path_matcher = path_matcher or AudioPathMatcher()
        self.displayer = displayer or LiveRankingDisplayer()
        self.sorter = sorter or JSIAdaptiveQuicksort(oracle, self.displayer)
        self.fitness_calculator = fitness_calculator or FitnessCalculator()
        self.fallback_sorter = FallbackSorter()

        self.comparison_count = 0
        self.generation_count = 0

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

        # Filter valid solutions using path matcher
        valid_paths = self.path_matcher.filter_valid_solutions(solution_ids, audio_paths)

        if len(valid_paths) < 2:
            # Not enough valid solutions for JSI ranking
            return self._fallback_ranking(solutions)

        # Print progress information
        print(f"\n=== JSI Ranking Generation {self.generation_count} ===")
        print(f"Valid solutions with audio: {len(valid_paths)}/{len(solutions)}")

        # Perform JSI sorting
        valid_ids = list(valid_paths.keys())
        ranked_ids = self.sorter.sort_with_audio(valid_ids, valid_paths, tracker, self.generation_count)

        # Update comparison count from sorter
        self.comparison_count = self.sorter.comparison_count

        # Convert ranking to solutions and fitness
        ranked_solutions, fitness_values = self._build_results(
            solutions, solution_ids, ranked_ids, valid_ids
        )

        # Build ranking information
        ranking_info = RankingInfoBuilder.build_ranking_info(
            tracker, self.comparison_count, len(valid_ids), len(solutions)
        )

        print(f"Ranking complete: {self.comparison_count} comparisons, confidence: {ranking_info.get('confidence', 0):.3f}")

        return ranked_solutions, fitness_values, ranking_info

    def _build_results(
        self,
        solutions: List[Solution],
        solution_ids: List[str],
        ranked_ids: List[str],
        valid_ids: List[str]
    ) -> Tuple[List[Solution], List[float]]:
        """Build final results from ranking."""
        # Convert ranked IDs back to solutions
        ranked_solutions = []

        # Add ranked valid solutions
        for sol_id in ranked_ids:
            idx = solution_ids.index(sol_id)
            ranked_solutions.append(solutions[idx])

        # Calculate fitness for ranked solutions
        fitness_values = self.fitness_calculator.ranking_to_fitness(ranked_ids)

        # Add invalid solutions with penalty fitness
        penalty_count = 0
        for i, solution in enumerate(solutions):
            sol_id = solution_ids[i]
            if sol_id not in valid_ids:
                ranked_solutions.append(solution)
                penalty_count += 1

        # Add penalty fitness values
        if penalty_count > 0:
            fitness_values = self.fitness_calculator.add_penalty_fitness(
                fitness_values, penalty_count
            )

        return ranked_solutions, fitness_values

    def _fallback_ranking(
        self,
        solutions: List[Solution]
    ) -> Tuple[List[Solution], List[float], Dict[str, Any]]:
        """Fallback ranking when JSI is not applicable."""
        print("Not enough valid audio files for JSI ranking. Using fallback method.")

        # Sort by parameter distance
        ranked_solutions = self.fallback_sorter.sort_by_parameter_distance(solutions)
        fitness_values = self.fallback_sorter.create_fallback_fitness(solutions)

        ranking_info = {
            'bt_ranking': [],
            'confidence': 0.0,
            'strengths': {},
            'comparisons_made': 0,
            'valid_solutions': 0,
            'total_solutions': len(solutions),
            'fallback_used': True
        }

        return ranked_solutions, fitness_values, ranking_info


class JSIFitnessEvaluator:
    """Fitness evaluator that uses JSI ranking with dependency injection."""

    def __init__(
        self,
        ranker: GAPopulationRanker,
        fitness_normalization: str = "exponential"
    ):
        """Initialize JSI fitness evaluator.

        Args:
            ranker: Pre-configured GA population ranker
            fitness_normalization: Method for converting ranks to fitness
        """
        self.ranker = ranker
        self.fitness_normalization = fitness_normalization

    def evaluate_population_fitness(
        self,
        solutions: List[Solution],
        audio_paths: Dict[str, Path]
    ) -> List[float]:
        """Evaluate population fitness using JSI ranking.

        Args:
            solutions: List of solutions to evaluate
            audio_paths: Dictionary mapping solution IDs to audio paths

        Returns:
            List of fitness values for each solution
        """
        _, fitness_values, _ = self.ranker.rank_population_with_audio(
            solutions, audio_paths
        )
        return fitness_values

    def get_ranking_info(self) -> Dict[str, Any]:
        """Get information about the ranking process."""
        return {
            'comparison_count': self.ranker.comparison_count,
            'generation_count': self.ranker.generation_count,
            'fitness_normalization': self.fitness_normalization
        }


# Factory functions for easy creation with standard dependencies
def create_standard_population_ranker(
    oracle: ComparisonOracle,
    show_live_ranking: bool = True
) -> GAPopulationRanker:
    """Create a population ranker with standard dependencies."""
    displayer = LiveRankingDisplayer(enabled=show_live_ranking)
    sorter = JSIAdaptiveQuicksort(oracle, displayer)

    return GAPopulationRanker(
        oracle=oracle,
        displayer=displayer,
        sorter=sorter
    )


def create_standard_fitness_evaluator(
    oracle: ComparisonOracle,
    fitness_normalization: str = "exponential",
    show_live_ranking: bool = True
) -> JSIFitnessEvaluator:
    """Create a fitness evaluator with standard dependencies."""
    ranker = create_standard_population_ranker(oracle, show_live_ranking)
    return JSIFitnessEvaluator(ranker, fitness_normalization)
