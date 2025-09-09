"""Fitness normalization utilities for converting Bradley-Terry strengths to GA fitness values."""

import numpy as np
from typing import Dict, List, Tuple, Optional


class FitnessNormalizer:
    """Converts Bradley-Terry strength parameters to normalized fitness values for genetic algorithms."""

    def __init__(self, temperature: float = 1.0):
        """Initialize fitness normalizer.

        Args:
            temperature: Temperature parameter for softmax (higher = more uniform, lower = more peaked)
        """
        self.temperature = temperature

    def softmax_normalize(self, strengths: Dict[str, float]) -> Dict[str, float]:
        """Convert Bradley-Terry strengths to softmax-normalized fitness values.

        Args:
            strengths: Dictionary mapping items to their Bradley-Terry strength values

        Returns:
            Dictionary mapping items to normalized fitness values (sum to 1.0)
        """
        if not strengths:
            return {}

        items = list(strengths.keys())
        strength_values = np.array([strengths[item] for item in items])

        # Apply temperature scaling
        scaled_strengths = strength_values / self.temperature

        # Compute softmax
        exp_strengths = np.exp(scaled_strengths - np.max(scaled_strengths))  # Numerical stability
        softmax_values = exp_strengths / np.sum(exp_strengths)

        return dict(zip(items, softmax_values))

    def exponential_normalize(self, strengths: Dict[str, float]) -> Dict[str, float]:
        """Convert Bradley-Terry strengths to exponential fitness values.

        This preserves the Bradley-Terry interpretation where exp(strength_i) represents
        the relative "skill" or "quality" of item i.

        Args:
            strengths: Dictionary mapping items to their Bradley-Terry strength values

        Returns:
            Dictionary mapping items to exponential fitness values
        """
        if not strengths:
            return {}

        return {item: np.exp(strength) for item, strength in strengths.items()}

    def min_max_normalize(self, strengths: Dict[str, float]) -> Dict[str, float]:
        """Convert Bradley-Terry strengths to min-max normalized fitness values.

        Args:
            strengths: Dictionary mapping items to their Bradley-Terry strength values

        Returns:
            Dictionary mapping items to fitness values in [0, 1] range
        """
        if not strengths:
            return {}

        strength_values = list(strengths.values())
        min_strength = min(strength_values)
        max_strength = max(strength_values)

        if min_strength == max_strength:
            # All strengths are equal
            return {item: 0.5 for item in strengths.keys()}

        range_strength = max_strength - min_strength
        return {
            item: (strength - min_strength) / range_strength
            for item, strength in strengths.items()
        }

    def get_fitness_summary(self, strengths: Dict[str, float]) -> Dict[str, Dict[str, float]]:
        """Get a summary of all normalization methods for comparison.

        Args:
            strengths: Dictionary mapping items to their Bradley-Terry strength values

        Returns:
            Dictionary with all normalization methods and their results
        """
        return {
            'raw_strengths': strengths.copy(),
            'softmax': self.softmax_normalize(strengths),
            'exponential': self.exponential_normalize(strengths),
            'min_max': self.min_max_normalize(strengths)
        }

    def rank_by_fitness(self, fitness_values: Dict[str, float]) -> List[Tuple[str, float]]:
        """Rank items by their fitness values in descending order.

        Args:
            fitness_values: Dictionary mapping items to fitness values

        Returns:
            List of (item, fitness) tuples sorted by fitness (highest first)
        """
        return sorted(fitness_values.items(), key=lambda x: x[1], reverse=True)
