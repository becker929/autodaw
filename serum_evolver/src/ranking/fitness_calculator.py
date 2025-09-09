"""Fitness calculation utilities for ranking results."""

import numpy as np
from typing import List, Dict, Any


class FitnessCalculator:
    """Calculates fitness values from ranking results."""

    @staticmethod
    def ranking_to_fitness(
        ranked_solution_ids: List[str],
        normalization: str = "exponential"
    ) -> List[float]:
        """Convert ranking to fitness values.

        Args:
            ranked_solution_ids: List of solution IDs in ranked order (best first)
            normalization: Method for normalization ("exponential", "linear", "inverse")

        Returns:
            List of fitness values corresponding to the ranking
        """
        if not ranked_solution_ids:
            return []

        n_solutions = len(ranked_solution_ids)

        if normalization == "exponential":
            return FitnessCalculator._exponential_fitness(n_solutions)
        elif normalization == "linear":
            return FitnessCalculator._linear_fitness(n_solutions)
        elif normalization == "inverse":
            return FitnessCalculator._inverse_fitness(n_solutions)
        else:
            raise ValueError(f"Unknown normalization method: {normalization}")

    @staticmethod
    def _exponential_fitness(n_solutions: int) -> List[float]:
        """Exponential decay fitness (higher rank = exponentially lower fitness)."""
        fitness_values = []
        for rank in range(n_solutions):
            fitness = np.exp(-rank * 0.5)  # Higher rank gets lower fitness
            fitness_values.append(fitness)
        return fitness_values

    @staticmethod
    def _linear_fitness(n_solutions: int) -> List[float]:
        """Linear fitness assignment."""
        fitness_values = []
        for rank in range(n_solutions):
            fitness = 1.0 - (rank / max(n_solutions - 1, 1))
            fitness_values.append(max(fitness, 0.01))  # Minimum fitness
        return fitness_values

    @staticmethod
    def _inverse_fitness(n_solutions: int) -> List[float]:
        """Inverse rank fitness."""
        fitness_values = []
        for rank in range(n_solutions):
            fitness = 1.0 / (rank + 1)
            fitness_values.append(fitness)
        return fitness_values

    @staticmethod
    def add_penalty_fitness(
        existing_fitness: List[float],
        n_penalty_solutions: int,
        penalty_value: float = 0.01
    ) -> List[float]:
        """Add penalty fitness values for invalid solutions.

        Args:
            existing_fitness: Existing fitness values for valid solutions
            n_penalty_solutions: Number of solutions to add penalty for
            penalty_value: Fitness value for penalized solutions

        Returns:
            Extended fitness list with penalty values
        """
        penalty_fitness = [penalty_value] * n_penalty_solutions
        return existing_fitness + penalty_fitness


class RankingInfoBuilder:
    """Builds ranking information dictionaries."""

    @staticmethod
    def build_ranking_info(
        tracker,
        comparison_count: int,
        valid_solutions_count: int,
        total_solutions_count: int,
        use_bt_ranking: bool = True
    ) -> Dict[str, Any]:
        """Build comprehensive ranking information.

        Args:
            tracker: Ranking tracker with comparison data
            comparison_count: Total number of comparisons made
            valid_solutions_count: Number of solutions with valid audio
            total_solutions_count: Total number of solutions
            use_bt_ranking: Whether to use Bradley-Terry ranking

        Returns:
            Dictionary with ranking information
        """
        if use_bt_ranking and valid_solutions_count >= 3:
            bt_ranking, confidence, strengths = tracker.get_bt_ranking_with_confidence()
        else:
            bt_ranking = tracker.get_simple_ranking()
            confidence = 0.0
            strengths = {}

        return {
            'bt_ranking': bt_ranking,
            'confidence': confidence,
            'strengths': strengths,
            'comparisons_made': comparison_count,
            'valid_solutions': valid_solutions_count,
            'total_solutions': total_solutions_count
        }
